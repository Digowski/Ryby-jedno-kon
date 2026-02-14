# calibration.py - v4.9 (obsługa wielu kont)

import pyautogui
import json
import time
import os
import win32api
import numpy as np
from pathlib import Path
from PIL import ImageGrab
import cv2

# Kody klawiszy
VK_SPACE = 0x20
VK_ESCAPE = 0x1B


class FishingCalibration:
    """Kalibracja główna - 5 kroków"""
    
    def __init__(self):
        self.positions = {}
        self.current_step = 0
        self.output_file = 'calibration.json'  # Można zmienić dla konta 2
        self.gui_callback = None
        
        self.steps = [
            {'id': 'fishing_window_top_left', 'desc': 'LEWY GÓRNY róg okna łowienia'},
            {'id': 'fishing_window_bottom_right', 'desc': 'PRAWY DOLNY róg okna łowienia'},
            {'id': 'bait_f1', 'desc': 'ŚRODEK pola F1 (robak)'},
            {'id': 'bait_f4', 'desc': 'ŚRODEK pola F4 (robak)'},
            {'id': 'armor_slot', 'desc': 'ŚRODEK ZBROI (ESC=pomiń)'},
        ]
    
    def _update_gui(self, message):
        if self.gui_callback:
            self.gui_callback(message)
        print(message)
    
    def _show_step(self):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self._update_gui(f"🔧 [{self.current_step + 1}/5] {step['desc']} → SPACJA")
    
    def start(self):
        self.current_step = 0
        self._show_step()
        
        prev_space = False
        prev_esc = False
        
        while self.current_step < len(self.steps):
            try:
                space_now = (win32api.GetAsyncKeyState(VK_SPACE) & 0x8000) != 0
                esc_now = (win32api.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0
                
                if space_now and not prev_space:
                    x, y = pyautogui.position()
                    step = self.steps[self.current_step]
                    step_id = step['id']
                    
                    print(f"[Calibration] SPACJA @ ({x}, {y}) - {step_id}")
                    
                    if step_id == 'fishing_window_top_left':
                        self.positions['fishing_window_left'] = x
                        self.positions['fishing_window_top'] = y
                    elif step_id == 'fishing_window_bottom_right':
                        self.positions['fishing_window_right'] = x
                        self.positions['fishing_window_bottom'] = y
                    elif step_id == 'bait_f1':
                        self.positions['bait_f1_x'] = x
                        self.positions['bait_f1_y'] = y
                    elif step_id == 'bait_f4':
                        self.positions['bait_f4_x'] = x
                        self.positions['bait_f4_y'] = y
                    elif step_id == 'armor_slot':
                        self.positions['armor_slot_x'] = x
                        self.positions['armor_slot_y'] = y
                        self.positions['armor_enabled'] = True
                    
                    self.current_step += 1
                    time.sleep(0.3)
                    self._show_step()
                
                if esc_now and not prev_esc:
                    if self.current_step < len(self.steps):
                        step = self.steps[self.current_step]
                        if step['id'] == 'armor_slot':
                            print("[Calibration] ESC - pomijam zbroję")
                            self.positions['armor_slot_x'] = 0
                            self.positions['armor_slot_y'] = 0
                            self.positions['armor_enabled'] = False
                            self.current_step += 1
                            time.sleep(0.3)
                            self._show_step()
                        else:
                            self._update_gui("❌ Anulowano")
                            return False
                
                prev_space = space_now
                prev_esc = esc_now
                
                time.sleep(0.03)
                
            except Exception as e:
                print(f"[Calibration] Błąd: {e}")
                time.sleep(0.1)
        
        self._calculate_center()
        self._calculate_f2_f3()
        self._save_calibration()
        self._update_gui("✅ Kalibracja zakończona!")
        return True
    
    def _calculate_center(self):
        left = self.positions.get('fishing_window_left', 0)
        top = self.positions.get('fishing_window_top', 0)
        right = self.positions.get('fishing_window_right', 0)
        bottom = self.positions.get('fishing_window_bottom', 0)
        
        self.positions['circle_center_x'] = (left + right) // 2
        self.positions['circle_center_y'] = (top + bottom) // 2
        self.positions['circle_radius'] = 152
    
    def _calculate_f2_f3(self):
        f1_x = self.positions.get('bait_f1_x', 0)
        f1_y = self.positions.get('bait_f1_y', 0)
        f4_x = self.positions.get('bait_f4_x', 0)
        
        if f1_x == 0 or f4_x == 0:
            return
        
        dx = (f4_x - f1_x) / 3.0
        
        self.positions['bait_f2_x'] = int(f1_x + dx)
        self.positions['bait_f2_y'] = f1_y
        self.positions['bait_f3_x'] = int(f1_x + 2 * dx)
        self.positions['bait_f3_y'] = f1_y
    
    def _save_calibration(self):
        if 'active_bait_slot' not in self.positions:
            self.positions['active_bait_slot'] = 'f1'
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.positions, f, indent=4, ensure_ascii=False)
        print(f"[Calibration] Zapisano: {self.output_file}")


class EQCalibration:
    """Kalibracja ekwipunku - 4 kroki"""
    
    def __init__(self):
        self.positions = {}
        self.current_step = 0
        self.output_file = 'calibration_eq.json'  # Można zmienić dla konta 2
        self.gui_callback = None
        
        self.steps = [
            {'id': 'eq_top_left', 'desc': 'LEWY GÓRNY róg EQ'},
            {'id': 'eq_bottom_right', 'desc': 'PRAWY DOLNY róg EQ'},
            {'id': 'empty_field', 'desc': 'PUSTE POLE (do wyrzucania)'},
            {'id': 'tak_button', 'desc': 'Przycisk TAK'},
        ]
    
    def _update_gui(self, message):
        if self.gui_callback:
            self.gui_callback(message)
        print(message)
    
    def _show_step(self):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self._update_gui(f"📦 [{self.current_step + 1}/4] {step['desc']} → SPACJA")
    
    def start(self):
        if Path(self.output_file).exists():
            with open(self.output_file, 'r') as f:
                self.positions = json.load(f)
        
        self.current_step = 0
        self._show_step()
        
        prev_space = False
        prev_esc = False
        
        while self.current_step < len(self.steps):
            try:
                space_now = (win32api.GetAsyncKeyState(VK_SPACE) & 0x8000) != 0
                esc_now = (win32api.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0
                
                if space_now and not prev_space:
                    x, y = pyautogui.position()
                    step = self.steps[self.current_step]
                    step_id = step['id']
                    
                    print(f"[EQ] SPACJA @ ({x}, {y}) - {step_id}")
                    
                    if step_id == 'eq_top_left':
                        self.positions['eq_left'] = x
                        self.positions['eq_top'] = y
                    elif step_id == 'eq_bottom_right':
                        self.positions['eq_right'] = x
                        self.positions['eq_bottom'] = y
                    elif step_id == 'empty_field':
                        self.positions['empty_field_x'] = x
                        self.positions['empty_field_y'] = y
                    elif step_id == 'tak_button':
                        self.positions['tak_button_x'] = x
                        self.positions['tak_button_y'] = y
                    
                    self.current_step += 1
                    time.sleep(0.3)
                    self._show_step()
                
                if esc_now and not prev_esc:
                    self._update_gui("❌ Anulowano")
                    return False
                
                prev_space = space_now
                prev_esc = esc_now
                time.sleep(0.03)
                
            except Exception as e:
                print(f"[EQ] Błąd: {e}")
                time.sleep(0.1)
        
        self._save_calibration()
        self._update_gui("✅ Kalibracja EQ zakończona!")
        return True
    
    def _save_calibration(self):
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.positions, f, indent=4, ensure_ascii=False)
        print(f"[EQ] Zapisano: {self.output_file}")


class EmptyEQCalibration:
    """Zapis pustego EQ - 1 krok"""
    
    def __init__(self):
        self.gui_callback = None
        self.eq_file = 'calibration_eq.json'  # Można zmienić dla konta 2
        self.output_file = 'empty_eq.png'      # Można zmienić dla konta 2
    
    def _update_gui(self, message):
        if self.gui_callback:
            self.gui_callback(message)
        print(message)
    
    def start(self):
        if not os.path.exists(self.eq_file):
            self._update_gui("❌ Najpierw zrób KALIBRACJA EQ!")
            return False
        
        with open(self.eq_file, 'r') as f:
            eq_cal = json.load(f)
        
        left = eq_cal.get('eq_left', 0)
        top = eq_cal.get('eq_top', 0)
        right = eq_cal.get('eq_right', 0)
        bottom = eq_cal.get('eq_bottom', 0)
        
        if left == 0 or right == 0:
            self._update_gui("❌ Błędna kalibracja EQ!")
            return False
        
        self._update_gui("📸 OPRÓŻNIJ EQ (zostaw zbroję) → SPACJA")
        
        prev_space = False
        prev_esc = False
        
        while True:
            try:
                space_now = (win32api.GetAsyncKeyState(VK_SPACE) & 0x8000) != 0
                esc_now = (win32api.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0
                
                if space_now and not prev_space:
                    print("[EmptyEQ] Zapisuję screenshot...")
                    
                    bbox = (left, top, right, bottom)
                    screenshot = ImageGrab.grab(bbox)
                    img_array = np.array(screenshot)
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    
                    cv2.imwrite(self.output_file, img_bgr)
                    
                    self._update_gui(f"✅ Zapisano {self.output_file}!")
                    time.sleep(0.3)
                    return True
                
                if esc_now and not prev_esc:
                    self._update_gui("❌ Anulowano")
                    return False
                
                prev_space = space_now
                prev_esc = esc_now
                time.sleep(0.03)
                
            except Exception as e:
                print(f"[EmptyEQ] Błąd: {e}")
                time.sleep(0.1)


class GMCalibration:
    """Kalibracja GM - 3 kroki"""
    
    def __init__(self):
        self.positions = {}
        self.current_step = 0
        self.output_file = 'calibration_gm.json'  # Można zmienić dla konta 2
        self.gm_area_file = 'gm_clean_area.npy'   # Można zmienić dla konta 2
        self.gui_callback = None
        
        self.steps = [
            {'id': 'gm_top_left', 'desc': 'LEWY GÓRNY róg GM (ESC=pomiń)'},
            {'id': 'gm_bottom_right', 'desc': 'PRAWY DOLNY róg GM'},
            {'id': 'message_icon', 'desc': 'Ikona wiadomości (ESC=pomiń)'},
        ]
    
    def _update_gui(self, message):
        if self.gui_callback:
            self.gui_callback(message)
        print(message)
    
    def _show_step(self):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self._update_gui(f"⚠️ [{self.current_step + 1}/3] {step['desc']} → SPACJA")
    
    def start(self):
        if Path(self.output_file).exists():
            with open(self.output_file, 'r') as f:
                self.positions = json.load(f)
        
        self.current_step = 0
        self._show_step()
        
        prev_space = False
        prev_esc = False
        
        while self.current_step < len(self.steps):
            try:
                space_now = (win32api.GetAsyncKeyState(VK_SPACE) & 0x8000) != 0
                esc_now = (win32api.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0
                
                if space_now and not prev_space:
                    x, y = pyautogui.position()
                    step = self.steps[self.current_step]
                    step_id = step['id']
                    
                    print(f"[GM] SPACJA @ ({x}, {y}) - {step_id}")
                    
                    if step_id == 'gm_top_left':
                        self.positions['gm_area_left'] = x
                        self.positions['gm_area_top'] = y
                        self.positions['gm_enabled'] = True
                    elif step_id == 'gm_bottom_right':
                        self.positions['gm_area_right'] = x
                        self.positions['gm_area_bottom'] = y
                    elif step_id == 'message_icon':
                        self.positions['message_x'] = x
                        self.positions['message_y'] = y
                        self.positions['message_enabled'] = True
                    
                    self.current_step += 1
                    time.sleep(0.3)
                    self._show_step()
                
                if esc_now and not prev_esc:
                    step = self.steps[self.current_step]
                    
                    if step['id'] == 'gm_top_left':
                        print("[GM] ESC - pomijam GM")
                        self.positions['gm_enabled'] = False
                        self.current_step = 2
                        time.sleep(0.3)
                        self._show_step()
                    elif step['id'] == 'message_icon':
                        print("[GM] ESC - pomijam wiadomości")
                        self.positions['message_enabled'] = False
                        self.current_step = 3
                        time.sleep(0.3)
                    else:
                        self._update_gui("❌ Anulowano")
                        return False
                
                prev_space = space_now
                prev_esc = esc_now
                time.sleep(0.03)
                
            except Exception as e:
                print(f"[GM] Błąd: {e}")
                time.sleep(0.1)
        
        self._save_calibration()
        self._save_clean_gm_area()
        self._update_gui("✅ Kalibracja GM zakończona!")
        return True
    
    def _save_calibration(self):
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.positions, f, indent=4, ensure_ascii=False)
        print(f"[GM] Zapisano: {self.output_file}")
    
    def _save_clean_gm_area(self):
        if not self.positions.get('gm_enabled', False):
            return
        
        try:
            left = self.positions.get('gm_area_left', 0)
            top = self.positions.get('gm_area_top', 0)
            right = self.positions.get('gm_area_right', 0)
            bottom = self.positions.get('gm_area_bottom', 0)
            
            if left > 0 and right > 0:
                bbox = (left, top, right, bottom)
                clean = ImageGrab.grab(bbox)
                np.save(self.gm_area_file, np.array(clean))
                print(f"[GM] Zapisano: {self.gm_area_file}")
        except Exception as e:
            print(f"[GM] Błąd: {e}")