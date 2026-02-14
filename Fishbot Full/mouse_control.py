# mouse_control.py - v4.3 (drag & drop)

import time
import ctypes
from ctypes import windll, Structure, c_long, c_ulong, sizeof, byref
import win32gui
import win32con
import win32api
from config import DELAYS

class MOUSEINPUT(Structure):
    _fields_ = [
        ('dx', c_long), ('dy', c_long), ('mouseData', c_ulong),
        ('dwFlags', c_ulong), ('time', c_ulong),
        ('dwExtraInfo', ctypes.POINTER(c_ulong))
    ]

class INPUT(Structure):
    _fields_ = [
        ('type', c_ulong),
        ('mi', MOUSEINPUT)
    ]

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

class MouseController:
    def __init__(self, calibration_data):
        self.cal = calibration_data
        self.screen_width = windll.user32.GetSystemMetrics(0)
        self.screen_height = windll.user32.GetSystemMetrics(1)
        print("[Mouse] v4.3 - drag & drop")
    
    def _to_absolute(self, x, y):
        return int(x * 65535 / self.screen_width), int(y * 65535 / self.screen_height)
    
    def move_to(self, x, y):
        abs_x, abs_y = self._to_absolute(x, y)
        mi = MOUSEINPUT()
        mi.dx, mi.dy = abs_x, abs_y
        mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.mi = mi
        windll.user32.SendInput(1, byref(inp), sizeof(inp))
    
    def mouse_down(self, button='left'):
        """Wciśnij przycisk myszy (bez puszczania)"""
        flag = MOUSEEVENTF_LEFTDOWN if button == 'left' else MOUSEEVENTF_RIGHTDOWN
        mi = MOUSEINPUT()
        mi.dwFlags = flag
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.mi = mi
        windll.user32.SendInput(1, byref(inp), sizeof(inp))
    
    def mouse_up(self, button='left'):
        """Puść przycisk myszy"""
        flag = MOUSEEVENTF_LEFTUP if button == 'left' else MOUSEEVENTF_RIGHTUP
        mi = MOUSEINPUT()
        mi.dwFlags = flag
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.mi = mi
        windll.user32.SendInput(1, byref(inp), sizeof(inp))
    
    def click_at(self, x, y, button='left'):
        self.move_to(x, y)
        time.sleep(0.015)
        
        down_flag = MOUSEEVENTF_LEFTDOWN if button == 'left' else MOUSEEVENTF_RIGHTDOWN
        up_flag = MOUSEEVENTF_LEFTUP if button == 'left' else MOUSEEVENTF_RIGHTUP
        
        abs_x, abs_y = self._to_absolute(x, y)
        
        mi_down = MOUSEINPUT()
        mi_down.dx, mi_down.dy = abs_x, abs_y
        mi_down.dwFlags = down_flag | MOUSEEVENTF_ABSOLUTE
        inp_down = INPUT()
        inp_down.type = INPUT_MOUSE
        inp_down.mi = mi_down
        
        mi_up = MOUSEINPUT()
        mi_up.dx, mi_up.dy = abs_x, abs_y
        mi_up.dwFlags = up_flag | MOUSEEVENTF_ABSOLUTE
        inp_up = INPUT()
        inp_up.type = INPUT_MOUSE
        inp_up.mi = mi_up
        
        windll.user32.SendInput(1, byref(inp_down), sizeof(inp_down))
        time.sleep(0.03)
        windll.user32.SendInput(1, byref(inp_up), sizeof(inp_up))
    
    def right_click_at(self, x, y):
        self.click_at(x, y, button='right')
    
    def drag_and_drop(self, from_x, from_y, to_x, to_y):
        """Przeciągnij z punktu A do B"""
        self.move_to(from_x, from_y)
        time.sleep(0.05)
        self.mouse_down('left')
        time.sleep(0.1)
        self.move_to(to_x, to_y)
        time.sleep(0.1)
        self.mouse_up('left')
        time.sleep(0.05)
    
    def press_key(self, key_name):
        if key_name == 'space':
            vk_code = win32con.VK_SPACE
            scan_code = 0x39
        elif key_name == 'enter':
            vk_code = win32con.VK_RETURN
            scan_code = 0x1C
        else:
            vk_code = ord(key_name.upper())
            scan_code = 0
        
        win32api.keybd_event(vk_code, scan_code, 0, 0)
        time.sleep(0.1)
        win32api.keybd_event(vk_code, scan_code, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
    
    def click_fish(self, fish_x, fish_y):
        self.click_at(fish_x, fish_y, button='left')
        time.sleep(DELAYS['after_click_fish'])
    
    def skip_animation(self):
        armor_x = self.cal.get('armor_slot_x', 0)
        armor_y = self.cal.get('armor_slot_y', 0)
        if armor_x > 0 and armor_y > 0:
            self.right_click_at(armor_x, armor_y)
            time.sleep(DELAYS['skip_animation'])
    
    def sweep_eq(self, eq_left, eq_top, eq_right, eq_bottom):
        """Przejedź myszką po EQ (usuwa ramki 'nowe')"""
        # Przejedź zygzakiem
        y = eq_top
        step = 30
        while y < eq_bottom:
            self.move_to(eq_left, y)
            time.sleep(0.02)
            self.move_to(eq_right, y)
            time.sleep(0.02)
            y += step
        print("[Mouse] Przejazd po EQ zakończony")