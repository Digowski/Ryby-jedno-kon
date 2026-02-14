# trash_handler.py - v5.1 (szybszy sweep 75%, bez przekładania zbroi)

import cv2
import numpy as np
import os
import time
import random
from PIL import ImageGrab

class TrashHandler:
    def __init__(self, calibration_eq, mouse_controller):
        self.cal = calibration_eq
        self.mouse = mouse_controller
        
        self.eq_left = self.cal.get('eq_left', 0)
        self.eq_top = self.cal.get('eq_top', 0)
        self.eq_right = self.cal.get('eq_right', 0)
        self.eq_bottom = self.cal.get('eq_bottom', 0)
        
        self.empty_x = self.cal.get('empty_field_x', 0)
        self.empty_y = self.cal.get('empty_field_y', 0)
        self.tak_x = self.cal.get('tak_button_x', 0)
        self.tak_y = self.cal.get('tak_button_y', 0)
        
        # Grid 5x9
        self.eq_width = self.eq_right - self.eq_left
        self.eq_height = self.eq_bottom - self.eq_top
        self.cols = 5
        self.rows = 9
        
        if self.eq_width > 0 and self.eq_height > 0:
            self.slot_width = self.eq_width / self.cols
            self.slot_height = self.eq_height / self.rows
        else:
            self.slot_width = 32
            self.slot_height = 32
        
        # Sloty do pominięcia (zbroja) - NIE RUSZAMY!
        self.skip_slots = [0, 5]
        
        # Foldery
        self.trash_folder = 'trash'
        self.kill_folder = 'fish_kill'
        
        # Wczytaj pusty EQ
        self.empty_eq = None
        if os.path.exists('empty_eq.png'):
            self.empty_eq = cv2.imread('empty_eq.png')
            print("[Trash] ✅ Wczytano empty_eq.png")
        else:
            print("[Trash] ⚠️ Brak empty_eq.png")
        
        # Prędkości - SWEEP 75% SZYBSZY
        self.SWEEP_DELAY = 0.02   # 20ms zamiast 80ms (75% szybciej)
        self.MOVE_DELAY = 0.06    # 60ms - ruchy przy akcjach
        self.CLICK_DELAY = 0.12   # 120ms - po kliknięciu
        self.DRAG_DELAY = 0.15    # 150ms - podczas przeciągania
        self.ACTION_DELAY = 0.25  # 250ms - między akcjami
        
        print(f"[Trash] v5.1 - Szybki sweep, bez ruszania zbroi")
        print(f"[Trash] EQ: ({self.eq_left}, {self.eq_top}) -> ({self.eq_right}, {self.eq_bottom})")

    def _human_delay(self, base_ms, variance_ms=15):
        delay = (base_ms + random.uniform(-variance_ms, variance_ms)) / 1000.0
        if delay > 0:
            time.sleep(delay)

    def _load_templates_fresh(self, folder):
        """Wczytaj templates NA ŚWIEŻO"""
        templates = []
        
        if not os.path.exists(folder):
            os.makedirs(folder)
            return templates
        
        for f in os.listdir(folder):
            if f.lower().endswith(('.bmp', '.png', '.jpg')):
                filepath = os.path.join(folder, f)
                img = cv2.imread(filepath)
                if img is not None:
                    h, w = img.shape[:2]
                    templates.append({
                        'name': f,
                        'image': img,
                        'width': w,
                        'height': h
                    })
        
        return templates

    def capture_eq(self):
        bbox = (self.eq_left, self.eq_top, self.eq_right, self.eq_bottom)
        img = np.array(ImageGrab.grab(bbox))
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    def get_slot_center(self, slot_idx):
        col = slot_idx % self.cols
        row = slot_idx // self.cols
        x = int(self.eq_left + (col + 0.5) * self.slot_width)
        y = int(self.eq_top + (row + 0.5) * self.slot_height)
        return x, y

    def get_slot_bbox_local(self, slot_idx):
        col = slot_idx % self.cols
        row = slot_idx // self.cols
        x1 = int(col * self.slot_width)
        y1 = int(row * self.slot_height)
        x2 = int((col + 1) * self.slot_width)
        y2 = int((row + 1) * self.slot_height)
        return x1, y1, x2, y2

    def is_slot_changed(self, current_eq, slot_idx):
        """Sprawdź czy slot się zmienił względem pustego"""
        if self.empty_eq is None:
            return True
        
        x1, y1, x2, y2 = self.get_slot_bbox_local(slot_idx)
        
        margin = 5
        x1 += margin
        y1 += margin
        x2 -= margin
        y2 -= margin
        
        if x1 >= x2 or y1 >= y2:
            return False
        
        if y2 > current_eq.shape[0] or x2 > current_eq.shape[1]:
            return False
        
        if y2 > self.empty_eq.shape[0] or x2 > self.empty_eq.shape[1]:
            return False
        
        curr_slot = current_eq[y1:y2, x1:x2]
        empty_slot = self.empty_eq[y1:y2, x1:x2]
        
        diff = cv2.absdiff(curr_slot, empty_slot)
        mean_diff = np.mean(diff)
        
        return mean_diff > 15

    def match_template_in_slot(self, current_eq, slot_idx, templates):
        """Sprawdź czy template pasuje do slotu"""
        if not templates:
            return False, None
        
        x1, y1, x2, y2 = self.get_slot_bbox_local(slot_idx)
        slot_img = current_eq[y1:y2, x1:x2]
        
        best_match = 0.0
        best_name = None
        
        for template_data in templates:
            template = template_data['image']
            name = template_data['name']
            
            try:
                result = cv2.matchTemplate(slot_img, template, cv2.TM_CCOEFF_NORMED)
                max_val = np.max(result)
                
                if max_val > best_match:
                    best_match = max_val
                    best_name = name
            except cv2.error:
                continue
        
        if best_match >= 0.65:
            return True, best_name
        
        return False, None

    def sweep_eq(self):
        """
        Przejedź myszką po EQ - SZYBKO (75% szybciej)
        NIE RUSZA ZBROI (skip_slots)
        """
        print("[Trash] Szybki sweep EQ...")
        
        for row in range(self.rows):
            for col in range(self.cols):
                slot_idx = row * self.cols + col
                
                # WAŻNE: Pomijamy sloty ze zbroją!
                if slot_idx in self.skip_slots:
                    continue
                
                x, y = self.get_slot_center(slot_idx)
                
                # Mały jitter
                jx = random.randint(-2, 2)
                jy = random.randint(-2, 2)
                
                self.mouse.move_to(x + jx, y + jy)
                
                # Szybki delay (20ms ±5ms)
                time.sleep(self.SWEEP_DELAY + random.uniform(-0.005, 0.005))
        
        print("[Trash] Sweep zakończony")

    def process_trash_and_fish(self):
        """
        GŁÓWNA FUNKCJA:
        1. Szybki sweep (usuń ramki "nowe")
        2. Zabij ryby
        3. Wyrzuć śmieci
        """
        if self.eq_left == 0:
            print("[Trash] ❌ Brak kalibracji EQ!")
            return 0, 0
        
        killed = 0
        discarded = 0
        
        # Wczytaj templates
        print("[Trash] === ROZPOCZYNAM CZYSZCZENIE EQ ===")
        trash_templates = self._load_templates_fresh(self.trash_folder)
        kill_templates = self._load_templates_fresh(self.kill_folder)
        
        print(f"[Trash] Templates: {len(trash_templates)} śmieci, {len(kill_templates)} ryb")
        
        # SZYBKI sweep (bez ruszania zbroi)
        self.sweep_eq()
        self._human_delay(200, 30)
        
        # Screenshot
        current_eq = self.capture_eq()
        
        # ETAP 1: Zabij ryby
        if kill_templates:
            print("[Trash] Szukam ryb do zabicia...")
            for slot_idx in range(45):
                if slot_idx in self.skip_slots:
                    continue
                
                if not self.is_slot_changed(current_eq, slot_idx):
                    continue
                
                is_match, name = self.match_template_in_slot(current_eq, slot_idx, kill_templates)
                
                if is_match:
                    x, y = self.get_slot_center(slot_idx)
                    col = slot_idx % self.cols
                    row = slot_idx // self.cols
                    
                    print(f"[Trash] 🔪 Zabijam: {name} (slot {slot_idx}, k={col}, w={row})")
                    
                    self.mouse.move_to(x, y)
                    self._human_delay(self.MOVE_DELAY * 1000, 15)
                    
                    self.mouse.right_click_at(x, y)
                    self._human_delay(350, 40)
                    
                    killed += 1
            
            if killed > 0:
                self._human_delay(400, 50)
                current_eq = self.capture_eq()
        
        # ETAP 2: Wyrzuć śmieci
        if trash_templates:
            print("[Trash] Szukam śmieci do wyrzucenia...")
            for slot_idx in range(45):
                if slot_idx in self.skip_slots:
                    continue
                
                if not self.is_slot_changed(current_eq, slot_idx):
                    continue
                
                is_match, name = self.match_template_in_slot(current_eq, slot_idx, trash_templates)
                
                if is_match:
                    x, y = self.get_slot_center(slot_idx)
                    col = slot_idx % self.cols
                    row = slot_idx // self.cols
                    
                    print(f"[Trash] 🗑️ Wyrzucam: {name} (slot {slot_idx}, k={col}, w={row})")
                    
                    self.mouse.move_to(x, y)
                    self._human_delay(self.MOVE_DELAY * 1000, 15)
                    
                    # Drag & drop
                    self._human_drag_and_drop(x, y, self.empty_x, self.empty_y)
                    self._human_delay(150, 30)
                    
                    # Klik TAK
                    self.mouse.move_to(self.tak_x, self.tak_y)
                    self._human_delay(80, 20)
                    self.mouse.click_at(self.tak_x, self.tak_y)
                    self._human_delay(250, 40)
                    
                    discarded += 1
        
        print(f"[Trash] === ZAKOŃCZONO: zabito={killed}, wyrzucono={discarded} ===")
        return discarded, killed

    def _human_drag_and_drop(self, from_x, from_y, to_x, to_y):
        """Przeciągnij wolno jak człowiek"""
        self.mouse.move_to(from_x, from_y)
        self._human_delay(60, 15)
        
        self.mouse.mouse_down('left')
        self._human_delay(80, 20)
        
        # Ruch w 4 krokach
        steps = 4
        for i in range(1, steps + 1):
            progress = i / steps
            curr_x = int(from_x + (to_x - from_x) * progress)
            curr_y = int(from_y + (to_y - from_y) * progress)
            
            jx = random.randint(-2, 2)
            jy = random.randint(-2, 2)
            
            self.mouse.move_to(curr_x + jx, curr_y + jy)
            self._human_delay(40, 10)
        
        self.mouse.move_to(to_x, to_y)
        self._human_delay(60, 15)
        
        self.mouse.mouse_up('left')
        self._human_delay(80, 20)

    def process(self):
        """Alias"""
        return self.process_trash_and_fish()