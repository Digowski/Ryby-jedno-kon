# bot_logic.py - v4.4 (naprawione checkboxy + trash handler)

import time
import threading
import winsound
import random
import numpy as np
import os
import json
from enum import Enum
from PIL import ImageGrab
from detection import FishDetector
from mouse_control import MouseController
from config import DELAYS, FISHING_TIMEOUT, TRASH_CHECK_INTERVAL

class BotState(Enum):
    IDLE = "Bezczynny"
    SCANNING_SLOTS = "Szukam robaków"
    EQUIPPING_BAIT = "Zakładanie robaka"
    CASTING = "Zarzucanie wędki"
    WAITING_WINDOW = "Czekam na okno"
    FISHING = "Łowienie ryby"
    CLICKING_FISH = "Klikanie w rybę"
    SKIPPING_ANIMATION = "Pomijanie animacji"
    CLEANING_EQ = "Czyszczenie EQ"
    NO_BAIT = "Brak robaków!"
    PAUSED = "Pauza"
    STOPPED = "Zatrzymany"
    GM_DETECTED = "GM WYKRYTY!"

class FishingBot:
    def __init__(self, calibration_data, status_callback=None):
        self.cal = calibration_data
        self.detector = FishDetector(calibration_data)
        self.mouse = MouseController(calibration_data)
        self.status_callback = status_callback
        
        self.state = BotState.IDLE
        self.is_running = False
        self.is_paused = False
        
        # Ustawienia z kalibracji/GUI
        self.fish_click_delay = self.cal.get('fish_click_speed', 0.075)
        self.after_armor_delay = self.cal.get('after_armor_delay', 0.15)
        self.window_timeout = self.cal.get('window_timeout', 5.0)
        self.no_armor_wait = self.cal.get('no_armor_wait', 4.0)
        
        # Checkboxy z GUI
        self.trash_enabled = self.cal.get('trash_enabled', False)
        self.kill_fish_enabled = self.cal.get('kill_fish_enabled', False)
        self.gm_detection = self.cal.get('gm_detection', False)
        
        print(f"[Bot] Ustawienia:")
        print(f"[Bot]   trash_enabled = {self.trash_enabled}")
        print(f"[Bot]   kill_fish_enabled = {self.kill_fish_enabled}")
        print(f"[Bot]   gm_detection = {self.gm_detection}")
        
        # Wykrywanie GM
        self.gm_clean_area = None
        if self.gm_detection and os.path.exists('gm_clean_area.npy'):
            try:
                self.gm_clean_area = np.load('gm_clean_area.npy')
                print("[Bot] Wczytano gm_clean_area.npy")
            except Exception as e:
                print(f"[Bot] ⚠️ Błąd wczytywania GM: {e}")
        
        # Trash handler - inicjalizuj TYLKO jeśli włączone
        self.trash_handler = None
        if (self.trash_enabled or self.kill_fish_enabled):
            if os.path.exists('calibration_eq.json'):
                try:
                    with open('calibration_eq.json', 'r') as f:
                        eq_cal = json.load(f)
                    from trash_handler import TrashHandler
                    self.trash_handler = TrashHandler(eq_cal, self.mouse)
                    print("[Bot] ✓ TrashHandler zainicjalizowany")
                except Exception as e:
                    print(f"[Bot] ⚠️ Błąd TrashHandler: {e}")
            else:
                print("[Bot] ⚠️ Brak calibration_eq.json - wyrzucanie wyłączone!")
                self.trash_enabled = False
                self.kill_fish_enabled = False
        
        # Sloty
        self.all_slots = ['f1', 'f2', 'f3', 'f4']
        self.current_slot = None
        self.current_slot_index = 0
        self.saved_slot = None
        self.saved_slot_index = 0
        
        self.WINDOW_OPEN_TIMEOUT = self.window_timeout
        
        self.stats = {
            'fish_caught': 0,
            'fish_clicks': 0,
            'baits_used': 0,
            'trash_discarded': 0,
            'fish_killed': 0,
            'session_start': None
        }
        
        print(f"[Bot] v4.4 - naprawione checkboxy")
    
    def update_settings(self, fish_click, armor_delay, timeout, no_armor, 
                        trash_enabled=None, kill_fish_enabled=None):
        """Aktualizuj ustawienia (wywoływane przy HOME/wznowieniu)"""
        self.fish_click_delay = fish_click
        self.after_armor_delay = armor_delay
        self.window_timeout = timeout
        self.no_armor_wait = no_armor
        self.WINDOW_OPEN_TIMEOUT = timeout
        
        # Aktualizuj checkboxy jeśli podane
        if trash_enabled is not None:
            self.trash_enabled = trash_enabled
        if kill_fish_enabled is not None:
            self.kill_fish_enabled = kill_fish_enabled
        
        # Reinicjalizuj trash handler jeśli potrzebny
        if (self.trash_enabled or self.kill_fish_enabled) and self.trash_handler is None:
            if os.path.exists('calibration_eq.json'):
                try:
                    with open('calibration_eq.json', 'r') as f:
                        eq_cal = json.load(f)
                    from trash_handler import TrashHandler
                    self.trash_handler = TrashHandler(eq_cal, self.mouse)
                    print("[Bot] ✓ TrashHandler zainicjalizowany przy update")
                except Exception as e:
                    print(f"[Bot] ⚠️ Błąd: {e}")
        
        print(f"[Bot] Ustawienia zaktualizowane:")
        print(f"[Bot]   klik={fish_click:.3f}, armor={armor_delay:.2f}")
        print(f"[Bot]   timeout={timeout:.1f}, no_armor={no_armor:.1f}")
        print(f"[Bot]   trash={self.trash_enabled}, kill={self.kill_fish_enabled}")
    
    def _micro_delay(self, base_ms, variance_ms):
        delay = (base_ms + random.uniform(-variance_ms, variance_ms)) / 1000.0
        if delay > 0:
            time.sleep(delay)
    
    def _micro_jitter(self):
        return random.randint(-2, 2), random.randint(-2, 2)
    
    def play_alert(self, count=6):
        print(f"[Bot] 🔊 ALERT ({count}x)")
        for i in range(count):
            winsound.MessageBeep(winsound.MB_ICONHAND)
            time.sleep(0.25)
    
    def _check_gm_area(self):
        if not self.gm_detection or self.gm_clean_area is None:
            return False
        
        try:
            if not os.path.exists('calibration_gm.json'):
                return False
            
            with open('calibration_gm.json', 'r') as f:
                gm_cal = json.load(f)
            
            if not gm_cal.get('gm_enabled', False):
                return False
            
            left = gm_cal.get('gm_area_left', 0)
            top = gm_cal.get('gm_area_top', 0)
            right = gm_cal.get('gm_area_right', 0)
            bottom = gm_cal.get('gm_area_bottom', 0)
            
            if left == 0:
                return False
            
            current = ImageGrab.grab((left, top, right, bottom))
            current_array = np.array(current)
            
            if current_array.shape != self.gm_clean_area.shape:
                return False
            
            diff = np.abs(current_array.astype(int) - self.gm_clean_area.astype(int))
            diff_sum = np.sum(diff)
            
            if diff_sum > 50000:
                return True
            
            return False
        except:
            return False
    
    def _handle_gm_detected(self):
        self.is_running = False
        self.update_status(BotState.GM_DETECTED, "GM WYKRYTY!")
        
        self.play_alert(6)
        time.sleep(2.0)
        
        self.mouse.press_key('enter')
        time.sleep(0.1)
        
        for char in "halo co jest":
            self.mouse.press_key(char)
            time.sleep(0.05)
        
        time.sleep(0.1)
        self.mouse.press_key('enter')
    
    def update_status(self, state, message=""):
        self.state = state
        status_text = f"[{state.value}] {message}"
        print(status_text)
        if self.status_callback:
            self.status_callback(status_text, self.stats)
    
    def start(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.is_paused = False
        self.stats['session_start'] = time.time()
        
        # START = zawsze od F1
        self.current_slot = None
        self.current_slot_index = 0
        
        threading.Thread(target=self._main_loop, daemon=True).start()
        
        if self.gm_detection:
            threading.Thread(target=self._gm_monitor_loop, daemon=True).start()
        
        self.update_status(BotState.IDLE, "Bot uruchomiony")
    
    def pause(self):
        """PAUZA - zapamiętaj slot"""
        self.is_paused = True
        self.saved_slot = self.current_slot
        self.saved_slot_index = self.current_slot_index
        print(f"[Bot] Zapamiętano slot: {self.saved_slot} (index={self.saved_slot_index})")
        self.update_status(BotState.PAUSED, "Pauza")
    
    def resume(self):
        """WZNÓW - przywróć slot"""
        self.is_paused = False
        
        if self.saved_slot is not None and self.saved_slot_index < 4:
            self.current_slot = self.saved_slot
            self.current_slot_index = self.saved_slot_index
            print(f"[Bot] Przywrócono: {self.current_slot} (index={self.current_slot_index})")
            self.update_status(BotState.IDLE, f"Wznowiono ({self.current_slot.upper()})")
        else:
            print("[Bot] Reset do F1")
            self.current_slot = None
            self.current_slot_index = 0
            self.update_status(BotState.IDLE, "Wznowiono (od F1)")
    
    def stop(self):
        """STOP - resetuj wszystko"""
        self.is_running = False
        self.is_paused = False
        self.current_slot = None
        self.current_slot_index = 0
        self.saved_slot = None
        self.saved_slot_index = 0
        self.update_status(BotState.STOPPED, "Zatrzymany")
    
    def _gm_monitor_loop(self):
        while self.is_running:
            if not self.is_paused and self.gm_detection:
                if self._check_gm_area():
                    self._handle_gm_detected()
                    break
            time.sleep(1.5)
    
    def _is_fishing_window_open(self):
        try:
            img, _, _ = self.detector.capture_circle_area()
            import cv2
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            bright_lower = np.array([0, 0, 200])
            bright_upper = np.array([180, 255, 255])
            mask = cv2.inRange(hsv, bright_lower, bright_upper)
            bright_pixels = cv2.countNonZero(mask)
            
            return bright_pixels > 1000
        except:
            return False
    
    def _wait_for_window_open(self, timeout=None):
        if timeout is None:
            timeout = self.WINDOW_OPEN_TIMEOUT
        
        start = time.time()
        while time.time() - start < timeout:
            if self._is_fishing_window_open():
                return True
            if self.is_paused or not self.is_running:
                return False
            time.sleep(0.1)
        return False
    
    def _try_slot(self, slot):
        x = self.cal[f'bait_{slot}_x']
        y = self.cal[f'bait_{slot}_y']
        
        jx, jy = self._micro_jitter()
        self.mouse.right_click_at(x + jx, y + jy)
        self._micro_delay(50, 30)
        
        self.mouse.press_key('space')
        
        self.update_status(BotState.WAITING_WINDOW, f"({slot.upper()})...")
        
        if self._wait_for_window_open():
            self.stats['baits_used'] += 1
            return True
        return False
    
    def _scan_for_bait(self):
        if self.current_slot_index >= 4:
            print("[Bot] Index >= 4, resetuję do 0")
            self.current_slot_index = 0
        
        self.update_status(BotState.SCANNING_SLOTS, f"Od {self.all_slots[self.current_slot_index].upper()}...")
        
        while self.current_slot_index < 4:
            if self.is_paused or not self.is_running:
                return False
            
            slot = self.all_slots[self.current_slot_index]
            
            if self._try_slot(slot):
                self.current_slot = slot
                return True
            else:
                self.current_slot_index += 1
        
        return False
    
    def _process_trash_if_needed(self):
        """Wyrzuć śmieci i zabij ryby co TRASH_CHECK_INTERVAL złowionych ryb"""
        # Sprawdź czy jest włączone
        if not self.trash_enabled and not self.kill_fish_enabled:
            return
        
        if self.trash_handler is None:
            print("[Bot] ⚠️ TrashHandler nie zainicjalizowany!")
            return
        
        # Sprawdź czy czas na czyszczenie
        if self.stats['fish_caught'] > 0 and self.stats['fish_caught'] % TRASH_CHECK_INTERVAL == 0:
            self.update_status(BotState.CLEANING_EQ, "Czyszczenie EQ...")
            
            try:
                discarded, killed = self.trash_handler.process_trash_and_fish()
                
                self.stats['trash_discarded'] += discarded
                self.stats['fish_killed'] += killed
                
                print(f"[Bot] ✓ Wyczyszczono: wyrzucono={discarded}, zabito={killed}")
            except Exception as e:
                print(f"[Bot] ❌ Błąd czyszczenia EQ: {e}")
                import traceback
                traceback.print_exc()
    
    def _main_loop(self):
        while self.is_running:
            if self.is_paused:
                time.sleep(0.5)
                continue
            
            try:
                if self.current_slot is None:
                    if not self._scan_for_bait():
                        self.play_alert()
                        self.update_status(BotState.NO_BAIT, "Brak robaków!")
                        self.is_paused = True
                        continue
                else:
                    self.update_status(BotState.EQUIPPING_BAIT, f"({self.current_slot.upper()})")
                    
                    x = self.cal[f'bait_{self.current_slot}_x']
                    y = self.cal[f'bait_{self.current_slot}_y']
                    
                    jx, jy = self._micro_jitter()
                    self.mouse.right_click_at(x + jx, y + jy)
                    self._micro_delay(50, 30)
                    
                    self.update_status(BotState.CASTING, "Zarzucam...")
                    self.mouse.press_key('space')
                    
                    self.update_status(BotState.WAITING_WINDOW, "Czekam...")
                    
                    if not self._wait_for_window_open():
                        # Slot się skończył
                        self.current_slot_index = self.all_slots.index(self.current_slot) + 1
                        self.current_slot = None
                        
                        if self.current_slot_index >= 4:
                            self.play_alert()
                            self.update_status(BotState.NO_BAIT, "Brak robaków!")
                            self.is_paused = True
                        continue
                    else:
                        self.stats['baits_used'] += 1
                
                if self._is_fishing_window_open():
                    self.update_status(BotState.FISHING, "Łowię...")
                    fish_result = self._catch_fish()
                    
                    if fish_result:
                        self.stats['fish_caught'] += 1
                        print(f"[Bot] 🐟 Złowiono rybę #{self.stats['fish_caught']}")
                        
                        # Sprawdź czy czas na czyszczenie
                        self._process_trash_if_needed()
                
                self._micro_delay(100, 50)
                
                if not self._is_fishing_window_open():
                    if self.cal.get('armor_enabled', True):
                        self.update_status(BotState.SKIPPING_ANIMATION, "Pomijam...")
                        self.mouse.skip_animation()
                        time.sleep(self.after_armor_delay)
                    else:
                        wait = round(self.no_armor_wait, 1)
                        self.update_status(BotState.SKIPPING_ANIMATION, f"Czekam {wait}s...")
                        time.sleep(self.no_armor_wait)
                
                self._micro_delay(80, 40)
                
            except Exception as e:
                print(f"[Bot] ❌ {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1.0)
    
    def _catch_fish(self):
        clicks_done = 0
        start_time = time.time()
        last_click_time = 0
        first_click = True
        
        self.update_status(BotState.CLICKING_FISH, "Śledzę...")
        
        while True:
            if time.time() - start_time > FISHING_TIMEOUT:
                return False
            
            if self.is_paused or not self.is_running:
                return False
            
            if not self._is_fishing_window_open():
                return True
            
            fish_pos = self.detector.get_fish_if_clickable()
            
            if fish_pos:
                current_time = time.time()
                
                if first_click:
                    fish_x, fish_y = fish_pos
                    jx, jy = self._micro_jitter()
                    
                    self.mouse.click_fish(fish_x + jx, fish_y + jy)
                    clicks_done += 1
                    last_click_time = current_time
                    first_click = False
                    self.stats['fish_clicks'] += 1
                    
                    self.update_status(BotState.CLICKING_FISH, f"Klik #{clicks_done}")
                    
                    if not self._is_fishing_window_open():
                        return True
                
                elif current_time - last_click_time >= self.fish_click_delay:
                    fish_x, fish_y = fish_pos
                    jx, jy = self._micro_jitter()
                    
                    self.mouse.click_fish(fish_x + jx, fish_y + jy)
                    clicks_done += 1
                    last_click_time = current_time
                    self.stats['fish_clicks'] += 1
                    
                    self.update_status(BotState.CLICKING_FISH, f"Klik #{clicks_done}")
                    
                    if not self._is_fishing_window_open():
                        return True
            
            time.sleep(0.005)