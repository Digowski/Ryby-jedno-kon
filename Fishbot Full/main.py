# main.py - GUI v5.0 (dwa konta, Arduino ready)

import customtkinter as ctk
import threading
import time
import json
import os
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def check_arduino_connected():
    """Sprawdź czy Arduino jest podłączone"""
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        arduino_ports = []
        for port in ports:
            # Arduino zazwyczaj ma "Arduino" lub "CH340" lub "USB Serial" w opisie
            desc = port.description.lower()
            if 'arduino' in desc or 'ch340' in desc or 'usb serial' in desc or 'leonardo' in desc:
                arduino_ports.append(port.device)
        return arduino_ports
    except:
        return []


class FishingBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("FishBot by Kamil")
        self.geometry("580x900")
        self.minsize(520, 700)
        self.resizable(True, True)
        
        self.bot = None
        self.bot2 = None  # Bot dla konta 2
        self.hotkey_running = True
        
        # Checkboxy
        self.multi_window_var = ctk.BooleanVar(value=False)
        self.trash_var = ctk.BooleanVar(value=False)
        self.kill_fish_var = ctk.BooleanVar(value=False)
        self.gm_detect_var = ctk.BooleanVar(value=False)
        self.arduino_mode_var = ctk.StringVar(value="system_mouse")
        
        # Suwaki
        self.fish_click_speed = ctk.DoubleVar(value=0.075)
        self.after_armor_delay = ctk.DoubleVar(value=0.10)
        self.window_timeout = ctk.DoubleVar(value=5.0)
        self.no_armor_wait = ctk.DoubleVar(value=4.0)
        
        # Arduino
        self.arduino_ports = check_arduino_connected()
        self.arduino_available = len(self.arduino_ports) > 0
        
        # Przyciski konta 2 (do włączania/wyłączania)
        self.account2_buttons = []
        
        self._build_gui()
        self._start_hotkey_listener()
        self._load_checkbox_states()
        self._update_account2_state()
    
    def _build_gui(self):
        # === GŁÓWNY KONTENER (scrollowalny) ===
        self.main_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === NAGŁÓWEK ===
        header = ctk.CTkLabel(self.main_frame, text="<.!.> Działa xD <.!.>", 
                               font=("Arial", 28, "bold"))
        header.pack(pady=(10, 15))
        
        # === KALIBRACJA - DWA KONTA ===
        cal_frame = ctk.CTkFrame(self.main_frame)
        cal_frame.pack(pady=10, padx=5, fill="x")
        
        ctk.CTkLabel(cal_frame, text="KALIBRACJA", 
                     font=("Arial", 26, "bold")).pack(pady=8)
        
        # Kontener na dwie kolumny
        columns_frame = ctk.CTkFrame(cal_frame, fg_color="transparent")
        columns_frame.pack(fill="x", padx=5, pady=5)
        
        # Konfiguracja siatki - dwie równe kolumny
        columns_frame.grid_columnconfigure(0, weight=1)
        columns_frame.grid_columnconfigure(1, weight=1)
        
        # === KOLUMNA 1 - KONTO 1 ===
        col1_frame = ctk.CTkFrame(columns_frame)
        col1_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(col1_frame, text="KONTO 1", 
                     font=("Arial", 16, "bold"), text_color="#3b82f6").pack(pady=8)
        
        self._create_cal_button(col1_frame, "GŁÓWNA", 
                                lambda: self._start_calibration(1), 
                                lambda: self._reset_calibration('main', 1),
                                "#2563eb", "#1d4ed8")
        
        self._create_cal_button(col1_frame, "EQ", 
                                lambda: self._start_calibration_eq(1), 
                                lambda: self._reset_calibration('eq', 1),
                                "#16a34a", "#15803d")
        
        self._create_cal_button(col1_frame, "PUSTE EQ", 
                                lambda: self._start_empty_eq(1), 
                                lambda: self._reset_calibration('empty_eq', 1),
                                "#7c3aed", "#6d28d9")
        
        self._create_cal_button(col1_frame, "GM", 
                                lambda: self._start_calibration_gm(1), 
                                lambda: self._reset_calibration('gm', 1),
                                "#ea580c", "#c2410c")
        
        ctk.CTkLabel(col1_frame, text="").pack(pady=3)
        
        # === KOLUMNA 2 - KONTO 2 ===
        col2_frame = ctk.CTkFrame(columns_frame)
        col2_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(col2_frame, text="KONTO 2", 
                     font=("Arial", 16, "bold"), text_color="#22c55e").pack(pady=8)
        
        btn1 = self._create_cal_button(col2_frame, "GŁÓWNA", 
                                       lambda: self._start_calibration(2), 
                                       lambda: self._reset_calibration('main', 2),
                                       "#2563eb", "#1d4ed8", return_buttons=True)
        
        btn2 = self._create_cal_button(col2_frame, "EQ", 
                                       lambda: self._start_calibration_eq(2), 
                                       lambda: self._reset_calibration('eq', 2),
                                       "#16a34a", "#15803d", return_buttons=True)
        
        btn3 = self._create_cal_button(col2_frame, "PUSTE EQ", 
                                       lambda: self._start_empty_eq(2), 
                                       lambda: self._reset_calibration('empty_eq', 2),
                                       "#7c3aed", "#6d28d9", return_buttons=True)
        
        btn4 = self._create_cal_button(col2_frame, "GM", 
                                       lambda: self._start_calibration_gm(2), 
                                       lambda: self._reset_calibration('gm', 2),
                                       "#ea580c", "#c2410c", return_buttons=True)
        
        # Zapisz przyciski konta 2
        self.account2_buttons = [btn1, btn2, btn3, btn4]
        self.account2_frame = col2_frame
        
        ctk.CTkLabel(col2_frame, text="").pack(pady=3)
        
        # === STATUS ===
        self.status_label = ctk.CTkLabel(self.main_frame, 
                                          text="Oczekiwanie na kalibrację...", 
                                          font=("Arial", 14, "bold"), 
                                          text_color="black",
                                          fg_color="#AAAAAA",
                                          corner_radius=8, 
                                          height=50)
        self.status_label.pack(pady=12, padx=10, fill="x")
        
        # === STEROWANIE ===
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.pack(pady=8, padx=10, fill="x")
        
        ctk.CTkLabel(control_frame, text="STEROWANIE", 
                     font=("Arial", 15, "bold")).pack(pady=8)
        ctk.CTkLabel(control_frame, 
                     text="HOME = Start / Wznów   |   END = Pauza   |   ESC = Stop",
                     font=("Arial", 16), text_color="lightgray").pack(pady=(0, 10))
        
        # === SUWAKI ===
        speed_frame = ctk.CTkFrame(self.main_frame)
        speed_frame.pack(pady=8, padx=10, fill="x")
        
        ctk.CTkLabel(speed_frame, text="PRĘDKOŚĆ", 
                     font=("Arial", 15, "bold")).pack(pady=8)
        
        self._create_slider(speed_frame, "Klikanie ryby:", 
                           self.fish_click_speed, 0.03, 0.6, "fish_click")
        
        self._create_slider(speed_frame, "Po zbroi:", 
                           self.after_armor_delay, 0.05, 0.3, "armor")
        
        self._create_slider(speed_frame, "Timeout okna:", 
                           self.window_timeout, 3.0, 15.0, "timeout")
        
        self._create_slider(speed_frame, "Bez zbroi:", 
                           self.no_armor_wait, 3.0, 10.0, "no_armor")
        
        ctk.CTkLabel(speed_frame, text="").pack(pady=3)
        
        # === OPCJE ===
        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(pady=8, padx=10, fill="x")
        
        ctk.CTkLabel(options_frame, text="OPCJE", 
                     font=("Arial", 15, "bold")).pack(pady=8)
        
        # Checkbox Multi-okno (WAŻNY!)
        self.multi_checkbox = ctk.CTkCheckBox(options_frame, 
                                               text="Włącz dwa konta",
                                               variable=self.multi_window_var,
                                               command=self._on_multi_window_change,
                                               font=("Arial", 16, "bold"))
        self.multi_checkbox.pack(pady=8, anchor="w", padx=25)
        
        # Radio: Sterowanie
        radio_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        radio_frame.pack(pady=8, fill="x")
        
        ctk.CTkLabel(radio_frame, text="Sterowanie:", 
                     font=("Arial", 12, "bold"), width=100).pack(side="left", padx=(25, 15))
        
        self.radio_mouse = ctk.CTkRadioButton(radio_frame, text="Myszka systemowa",
                                               variable=self.arduino_mode_var,
                                               value="system_mouse",
                                               font=("Arial", 14))
        self.radio_mouse.pack(side="left", padx=10)
        
        # Arduino - status
        arduino_text = "Arduino"
        if self.arduino_available:
            arduino_text = f"Arduino ({', '.join(self.arduino_ports)})"
            arduino_state = "normal"
        else:
            arduino_text = "Arduino (nie wykryte)"
            arduino_state = "disabled"
        
        self.radio_arduino = ctk.CTkRadioButton(radio_frame, text=arduino_text,
                                                 variable=self.arduino_mode_var,
                                                 value="arduino",
                                                 font=("Arial", 14),
                                                 state=arduino_state)
        self.radio_arduino.pack(side="left", padx=10)
        
        # Przycisk odśwież Arduino
        self.refresh_arduino_btn = ctk.CTkButton(radio_frame, text="🔄",
                                                  command=self._refresh_arduino,
                                                  width=35, height=28,
                                                  font=("Arial", 12))
        self.refresh_arduino_btn.pack(side="left", padx=5)
        
        # Pozostałe checkboxy
        self.trash_checkbox = ctk.CTkCheckBox(options_frame, 
                                               text="Wyrzucanie śmieci (co 10 ryb)",
                                               variable=self.trash_var,
                                               command=self._on_checkbox_change,
                                               font=("Arial", 16))
        self.trash_checkbox.pack(pady=5, anchor="w", padx=25)
        
        self.kill_fish_checkbox = ctk.CTkCheckBox(options_frame, 
                                                   text="Zabijanie ryb (co 10 ryb)",
                                                   variable=self.kill_fish_var,
                                                   command=self._on_checkbox_change,
                                                   font=("Arial", 16))
        self.kill_fish_checkbox.pack(pady=5, anchor="w", padx=25)
        
        self.gm_checkbox = ctk.CTkCheckBox(options_frame, 
                                            text="Wykrywanie GM",
                                            variable=self.gm_detect_var,
                                            command=self._on_checkbox_change,
                                            font=("Arial", 16))
        self.gm_checkbox.pack(pady=5, anchor="w", padx=25)
        
        ctk.CTkLabel(options_frame, text="").pack(pady=5)
        
        # === STOPKA ===
        footer = ctk.CTkLabel(self, text="Lepiej nie bedzie :)", 
                               font=("Arial", 16), text_color="gray50")
        footer.pack(side="bottom", pady=8)
    
    def _create_cal_button(self, parent, text, cmd_main, cmd_reset, color, hover, return_buttons=False):
        """Tworzy wiersz kalibracji - kompaktowy"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(pady=3, padx=8, fill="x")
        
        btn_main = ctk.CTkButton(row, text=text,
                                  command=cmd_main,
                                  height=36,
                                  fg_color=color, hover_color=hover,
                                  font=("Arial", 11, "bold"))
        btn_main.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_reset = ctk.CTkButton(row, text="🗑️",
                                   command=cmd_reset,
                                   width=40, height=36,
                                   fg_color="#dc2626", hover_color="#b91c1c",
                                   font=("Arial", 11))
        btn_reset.pack(side="right")
        
        if return_buttons:
            return (btn_main, btn_reset)
    
    def _create_slider(self, parent, label, variable, min_val, max_val, name):
        """Tworzy suwak"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=4, padx=20)
        
        ctk.CTkLabel(frame, text=label, font=("Arial", 12), 
                     width=140, anchor="w").pack(side="left")
        
        slider = ctk.CTkSlider(frame, from_=min_val, to=max_val, 
                                variable=variable,
                                command=lambda v: self._on_slider_change(name, v))
        slider.pack(side="left", fill="x", expand=True, padx=10)
        
        value_label = ctk.CTkLabel(frame, text=f"{variable.get():.3f}", 
                                    font=("Arial", 12, "bold"), width=60)
        value_label.pack(side="right")
        
        setattr(self, f"{name}_value_label", value_label)
    
    def _on_multi_window_change(self):
        """Włącz/wyłącz przyciski konta 2"""
        self._update_account2_state()
        self._save_checkbox_states()
    
    def _update_account2_state(self):
        """Aktualizuj stan przycisków konta 2"""
        enabled = self.multi_window_var.get()
        
        for btn_tuple in self.account2_buttons:
            if btn_tuple:
                btn_main, btn_reset = btn_tuple
                if enabled:
                    btn_main.configure(state="normal")
                    btn_reset.configure(state="normal")
                else:
                    btn_main.configure(state="disabled")
                    btn_reset.configure(state="disabled")
        
        # Zmień kolor ramki konta 2
        if hasattr(self, 'account2_frame'):
            if enabled:
                self.account2_frame.configure(fg_color=("#2b2b2b", "#2b2b2b"))
            else:
                self.account2_frame.configure(fg_color=("#1a1a1a", "#1a1a1a"))
    
    def _refresh_arduino(self):
        """Odśwież listę Arduino"""
        self.arduino_ports = check_arduino_connected()
        self.arduino_available = len(self.arduino_ports) > 0
        
        if self.arduino_available:
            arduino_text = f"Arduino ({', '.join(self.arduino_ports)})"
            self.radio_arduino.configure(text=arduino_text, state="normal")
            self._update_status(f"✅ Wykryto Arduino: {', '.join(self.arduino_ports)}", "green")
        else:
            self.radio_arduino.configure(text="Arduino (nie wykryte)", state="disabled")
            self.arduino_mode_var.set("system_mouse")
            self._update_status("⚠️ Arduino nie wykryte", "yellow")
    
    def _get_file_suffix(self, account):
        """Zwróć sufiks pliku dla konta ('' dla 1, '_2' dla 2)"""
        return "" if account == 1 else "_2"
    
    def _on_slider_change(self, name, value):
        label = getattr(self, f"{name}_value_label", None)
        if label:
            label.configure(text=f"{value:.3f}")
        
        if self.bot and self.bot.is_running:
            self.bot.update_settings(
                self.fish_click_speed.get(),
                self.after_armor_delay.get(),
                self.window_timeout.get(),
                self.no_armor_wait.get()
            )
    
    def _on_checkbox_change(self):
        self._save_checkbox_states()
        
        if self.bot and self.bot.is_running:
            self.bot.trash_enabled = self.trash_var.get()
            self.bot.kill_fish_enabled = self.kill_fish_var.get()
            self.bot.gm_detection = self.gm_detect_var.get()
    
    def _save_checkbox_states(self):
        states = {
            'trash_enabled': self.trash_var.get(),
            'kill_fish_enabled': self.kill_fish_var.get(),
            'gm_detection': self.gm_detect_var.get(),
            'multi_window': self.multi_window_var.get(),
            'arduino_mode': self.arduino_mode_var.get()
        }
        try:
            with open('gui_settings.json', 'w') as f:
                json.dump(states, f, indent=4)
        except:
            pass
    
    def _load_checkbox_states(self):
        try:
            if os.path.exists('gui_settings.json'):
                with open('gui_settings.json', 'r') as f:
                    states = json.load(f)
                self.trash_var.set(states.get('trash_enabled', False))
                self.kill_fish_var.set(states.get('kill_fish_enabled', False))
                self.gm_detect_var.set(states.get('gm_detection', False))
                self.multi_window_var.set(states.get('multi_window', False))
                
                # Arduino mode - tylko jeśli dostępne
                saved_mode = states.get('arduino_mode', 'system_mouse')
                if saved_mode == 'arduino' and not self.arduino_available:
                    self.arduino_mode_var.set('system_mouse')
                else:
                    self.arduino_mode_var.set(saved_mode)
        except:
            pass
    
    def _reset_calibration(self, cal_type, account=1):
        """Usuń pliki kalibracji dla danego konta"""
        suffix = self._get_file_suffix(account)
        
        try:
            if cal_type == 'main':
                fname = f'calibration{suffix}.json'
                if os.path.exists(fname):
                    os.remove(fname)
                self._update_status(f"🗑️ Konto {account}: Kalibracja główna zresetowana!", "yellow")
            elif cal_type == 'eq':
                fname = f'calibration_eq{suffix}.json'
                if os.path.exists(fname):
                    os.remove(fname)
                self._update_status(f"🗑️ Konto {account}: Kalibracja EQ zresetowana!", "yellow")
            elif cal_type == 'empty_eq':
                fname = f'empty_eq{suffix}.png'
                if os.path.exists(fname):
                    os.remove(fname)
                self._update_status(f"🗑️ Konto {account}: Puste EQ zresetowane!", "yellow")
            elif cal_type == 'gm':
                fname1 = f'calibration_gm{suffix}.json'
                fname2 = f'gm_clean_area{suffix}.npy'
                if os.path.exists(fname1):
                    os.remove(fname1)
                if os.path.exists(fname2):
                    os.remove(fname2)
                self._update_status(f"🗑️ Konto {account}: Kalibracja GM zresetowana!", "yellow")
        except Exception as e:
            self._update_status(f"❌ Błąd: {e}", "red")
    
    def _start_hotkey_listener(self):
        def hotkey_loop():
            import win32api
            
            VK_HOME = 0x24
            VK_END = 0x23
            VK_ESCAPE = 0x1B
            
            prev_home = False
            prev_end = False
            prev_esc = False
            
            while self.hotkey_running:
                try:
                    home = (win32api.GetAsyncKeyState(VK_HOME) & 0x8000) != 0
                    end = (win32api.GetAsyncKeyState(VK_END) & 0x8000) != 0
                    esc = (win32api.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0
                    
                    if home and not prev_home:
                        self.after(0, self._on_home)
                    if end and not prev_end:
                        self.after(0, self._on_end)
                    if esc and not prev_esc:
                        self.after(0, self._on_escape)
                    
                    prev_home = home
                    prev_end = end
                    prev_esc = esc
                    
                    time.sleep(0.03)
                except:
                    time.sleep(0.1)
        
        threading.Thread(target=hotkey_loop, daemon=True).start()
    
    def _on_home(self):
        print("[GUI] HOME pressed")
        
        # Sprawdź kalibrację konta 1
        if not os.path.exists('calibration.json'):
            self._update_status("❌ Konto 1: Najpierw KALIBRACJA GŁÓWNA!", "red")
            return
        
        if (self.trash_var.get() or self.kill_fish_var.get()):
            if not os.path.exists('calibration_eq.json'):
                self._update_status("❌ Konto 1: Najpierw KALIBRACJA EQ!", "red")
                return
            if not os.path.exists('empty_eq.png'):
                self._update_status("❌ Konto 1: Najpierw ZAPISZ PUSTE EQ!", "red")
                return
        
        # Sprawdź konto 2 jeśli włączone
        if self.multi_window_var.get():
            if not os.path.exists('calibration_2.json'):
                self._update_status("❌ Konto 2: Najpierw KALIBRACJA GŁÓWNA!", "red")
                return
            
            if (self.trash_var.get() or self.kill_fish_var.get()):
                if not os.path.exists('calibration_eq_2.json'):
                    self._update_status("❌ Konto 2: Najpierw KALIBRACJA EQ!", "red")
                    return
                if not os.path.exists('empty_eq_2.png'):
                    self._update_status("❌ Konto 2: Najpierw ZAPISZ PUSTE EQ!", "red")
                    return
        
        if not self.bot:
            self._start_bot()
        elif not self.bot.is_running:
            self.bot.start()
        elif self.bot.is_paused:
            self.bot.update_settings(
                self.fish_click_speed.get(),
                self.after_armor_delay.get(),
                self.window_timeout.get(),
                self.no_armor_wait.get(),
                trash_enabled=self.trash_var.get(),
                kill_fish_enabled=self.kill_fish_var.get()
            )
            self.bot.resume()
    
    def _on_end(self):
        print("[GUI] END pressed")
        if self.bot:
            self.bot.pause()
        if self.bot2:
            self.bot2.pause()
        self._update_status("⏸️ PAUZA (HOME=wznów)", "yellow")
    
    def _on_escape(self):
        print("[GUI] ESC pressed")
        if self.bot:
            self.bot.stop()
            self.bot = None
        if self.bot2:
            self.bot2.stop()
            self.bot2 = None
        self._update_status("⏹️ ZATRZYMANO", "gray")
    
    def _start_bot(self):
        from bot_logic import FishingBot
        
        try:
            # Konto 1
            with open('calibration.json', 'r') as f:
                cal = json.load(f)
            
            cal['fish_click_speed'] = self.fish_click_speed.get()
            cal['after_armor_delay'] = self.after_armor_delay.get()
            cal['window_timeout'] = self.window_timeout.get()
            cal['no_armor_wait'] = self.no_armor_wait.get()
            cal['trash_enabled'] = self.trash_var.get()
            cal['kill_fish_enabled'] = self.kill_fish_var.get()
            cal['gm_detection'] = self.gm_detect_var.get()
            cal['account'] = 1
            
            self.bot = FishingBot(cal, status_callback=self._bot_status_callback)
            self.bot.start()
            
            status_msg = "🎣 Konto 1 uruchomione!"
            
            # Konto 2 (jeśli włączone)
            if self.multi_window_var.get():
                with open('calibration_2.json', 'r') as f:
                    cal2 = json.load(f)
                
                cal2['fish_click_speed'] = self.fish_click_speed.get()
                cal2['after_armor_delay'] = self.after_armor_delay.get()
                cal2['window_timeout'] = self.window_timeout.get()
                cal2['no_armor_wait'] = self.no_armor_wait.get()
                cal2['trash_enabled'] = self.trash_var.get()
                cal2['kill_fish_enabled'] = self.kill_fish_var.get()
                cal2['gm_detection'] = self.gm_detect_var.get()
                cal2['account'] = 2
                
                self.bot2 = FishingBot(cal2, status_callback=self._bot_status_callback)
                self.bot2.start()
                
                status_msg = "🎣 Oba konta uruchomione!"
            
            self._update_status(status_msg, "green")
            
        except Exception as e:
            self._update_status(f"❌ Błąd: {e}", "red")
            import traceback
            traceback.print_exc()
    
    def _bot_status_callback(self, status, stats):
        self.after(0, lambda: self._update_from_bot(status, stats))
    
    def _update_from_bot(self, status, stats):
        if "Klik" in status:
            self._update_status(f"🎯 {status}", "green")
        elif "Pauza" in status:
            self._update_status(f"⏸️ {status}", "yellow")
        elif "Brak" in status or "GM" in status:
            self._update_status(f"❌ {status}", "red")
        elif "Czekam" in status or "Łowię" in status:
            self._update_status(f"🎣 {status}", "blue")
        elif "Czyszczenie" in status:
            self._update_status(f"📦 {status}", "yellow")
        else:
            self._update_status(f"📌 {status}", "gray")
    
    def _update_status(self, text, color="gray"):
        bg_colors = {
            "gray": "#AAAAAA",
            "green": "#90EE90",
            "yellow": "#FFD700",
            "red": "#FF6B6B",
            "blue": "#87CEEB"
        }
        self.status_label.configure(text=text, 
                                     fg_color=bg_colors.get(color, "#AAAAAA"), 
                                     text_color="black")
    
    def _start_calibration(self, account=1):
        suffix = self._get_file_suffix(account)
        self._update_status(f"🔧 Konto {account}: Rozpoczynam kalibrację...", "yellow")
        
        def run():
            from calibration import FishingCalibration
            cal = FishingCalibration()
            cal.output_file = f'calibration{suffix}.json'
            cal.gui_callback = lambda msg: self.after(0, lambda: self._update_status(f"Konto {account}: {msg}", "yellow"))
            success = cal.start()
            if success:
                self.after(0, lambda: self._update_status(f"✅ Konto {account}: Kalibracja OK!", "green"))
            else:
                self.after(0, lambda: self._update_status(f"❌ Konto {account}: Anulowano", "red"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def _start_calibration_eq(self, account=1):
        suffix = self._get_file_suffix(account)
        self._update_status(f"📦 Konto {account}: Rozpoczynam kalibrację EQ...", "yellow")
        
        def run():
            from calibration import EQCalibration
            cal = EQCalibration()
            cal.output_file = f'calibration_eq{suffix}.json'
            cal.gui_callback = lambda msg: self.after(0, lambda: self._update_status(f"Konto {account}: {msg}", "yellow"))
            success = cal.start()
            if success:
                self.after(0, lambda: self._update_status(f"✅ Konto {account}: Kalibracja EQ OK!", "green"))
            else:
                self.after(0, lambda: self._update_status(f"❌ Konto {account}: Anulowano", "red"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def _start_empty_eq(self, account=1):
        suffix = self._get_file_suffix(account)
        self._update_status(f"📸 Konto {account}: Przygotuj puste EQ...", "yellow")
        
        def run():
            from calibration import EmptyEQCalibration
            cal = EmptyEQCalibration()
            cal.eq_file = f'calibration_eq{suffix}.json'
            cal.output_file = f'empty_eq{suffix}.png'
            cal.gui_callback = lambda msg: self.after(0, lambda: self._update_status(f"Konto {account}: {msg}", "yellow"))
            success = cal.start()
            if success:
                self.after(0, lambda: self._update_status(f"✅ Konto {account}: Puste EQ zapisane!", "green"))
            else:
                self.after(0, lambda: self._update_status(f"❌ Konto {account}: Anulowano", "red"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def _start_calibration_gm(self, account=1):
        suffix = self._get_file_suffix(account)
        self._update_status(f"⚠️ Konto {account}: Rozpoczynam kalibrację GM...", "yellow")
        
        def run():
            from calibration import GMCalibration
            cal = GMCalibration()
            cal.output_file = f'calibration_gm{suffix}.json'
            cal.gm_area_file = f'gm_clean_area{suffix}.npy'
            cal.gui_callback = lambda msg: self.after(0, lambda: self._update_status(f"Konto {account}: {msg}", "yellow"))
            success = cal.start()
            if success:
                self.after(0, lambda: self._update_status(f"✅ Konto {account}: Kalibracja GM OK!", "green"))
            else:
                self.after(0, lambda: self._update_status(f"❌ Konto {account}: Anulowano", "red"))
        
        threading.Thread(target=run, daemon=True).start()
    
    def on_closing(self):
        self.hotkey_running = False
        self._save_checkbox_states()
        if self.bot:
            self.bot.stop()
        if self.bot2:
            self.bot2.stop()
        self.destroy()


if __name__ == "__main__":
    print("="*50)
    print("FISHING BOT v5.0")
    print("="*50)
    
    for folder in ['trash', 'fish_kill', 'fish_keep']:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"[INFO] Utworzono folder {folder}/")
    
    app = FishingBotGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()