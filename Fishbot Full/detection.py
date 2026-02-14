# detection.py - Detekcja v4.0 (jeden screenshot)

import cv2
import numpy as np
import threading
from PIL import ImageGrab

class FishDetector:
    def __init__(self, calibration_data):
        self.cal = calibration_data
        
        self.window_left = self.cal['fishing_window_left']
        self.window_top = self.cal['fishing_window_top']
        self.window_right = self.cal['fishing_window_right']
        self.window_bottom = self.cal['fishing_window_bottom']
        
        self.circle_x = self.cal['circle_center_x']
        self.circle_y = self.cal['circle_center_y']
        self.circle_radius = self.cal['circle_radius']
        
        self.local_circle_x = self.circle_x - self.window_left
        self.local_circle_y = self.circle_y - self.window_top
        
        # Kolory ryby
        self.fish_hsv_lower = np.array([90, 80, 100])
        self.fish_hsv_upper = np.array([120, 160, 150])
        
        # Kolory czerwonego koła
        self.circle_red_lower1 = np.array([0, 40, 120])
        self.circle_red_upper1 = np.array([15, 255, 255])
        self.circle_red_lower2 = np.array([155, 40, 120])
        self.circle_red_upper2 = np.array([180, 255, 255])
        
        self.lock = threading.Lock()
        
        print(f"[Detector] v4.0 - Jeden screenshot")
    
    def capture_window(self):
        with self.lock:
            bbox = (self.window_left, self.window_top, self.window_right, self.window_bottom)
            screenshot = ImageGrab.grab(bbox)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return img
    
    def capture_circle_area(self):
        margin = 20
        left = self.circle_x - self.circle_radius - margin
        top = self.circle_y - self.circle_radius - margin
        right = self.circle_x + self.circle_radius + margin
        bottom = self.circle_y + self.circle_radius + margin
        
        with self.lock:
            bbox = (left, top, right, bottom)
            screenshot = ImageGrab.grab(bbox)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return img, left, top
    
    def _check_circle_red_on_image(self, img_hsv):
        mask_circle = np.zeros(img_hsv.shape[:2], dtype=np.uint8)
        cv2.circle(mask_circle, (self.local_circle_x, self.local_circle_y), 
                   self.circle_radius, 255, -1)
        
        mask1 = cv2.inRange(img_hsv, self.circle_red_lower1, self.circle_red_upper1)
        mask2 = cv2.inRange(img_hsv, self.circle_red_lower2, self.circle_red_upper2)
        mask_red = cv2.bitwise_or(mask1, mask2)
        
        mask_red_in_circle = cv2.bitwise_and(mask_red, mask_circle)
        red_pixels = cv2.countNonZero(mask_red_in_circle)
        
        return red_pixels > 200
    
    def _find_fish_on_image(self, img_hsv):
        mask = cv2.inRange(img_hsv, self.fish_hsv_lower, self.fish_hsv_upper)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        
        if area < 30:
            return None
        
        M = cv2.moments(largest)
        if M['m00'] == 0:
            return None
        
        local_x = int(M['m10'] / M['m00'])
        local_y = int(M['m01'] / M['m00'])
        
        return (local_x, local_y)
    
    def get_fish_if_clickable(self):
        try:
            img = self.capture_window()
            img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            is_red = self._check_circle_red_on_image(img_hsv)
            
            if not is_red:
                return None
            
            fish_local = self._find_fish_on_image(img_hsv)
            
            if fish_local is None:
                return (self.circle_x, self.circle_y)
            
            local_x, local_y = fish_local
            
            screen_x = self.window_left + local_x
            screen_y = self.window_top + local_y
            
            return (screen_x, screen_y)
        except:
            return None
    
    def is_circle_red(self):
        try:
            img = self.capture_window()
            img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            return self._check_circle_red_on_image(img_hsv)
        except:
            return False