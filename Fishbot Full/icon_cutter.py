# icon_cutter.py - Narzędzie do wycinania ikon z EQ

import cv2
import numpy as np
import json
import os
from PIL import ImageGrab
import keyboard

print("="*60)
print("NARZĘDZIE DO WYCINANIA IKON Z EQ")
print("="*60)

# Wczytaj kalibrację
if not os.path.exists('calibration_eq.json'):
    print("❌ Brak calibration_eq.json - zrób najpierw KALIBRACJA EQ!")
    exit()

with open('calibration_eq.json', 'r') as f:
    eq_cal = json.load(f)

eq_left = eq_cal.get('eq_left', 0)
eq_top = eq_cal.get('eq_top', 0)
eq_right = eq_cal.get('eq_right', 0)
eq_bottom = eq_cal.get('eq_bottom', 0)

eq_width = eq_right - eq_left
eq_height = eq_bottom - eq_top

cols, rows = 5, 9
slot_width = eq_width / cols
slot_height = eq_height / rows

print(f"EQ: ({eq_left}, {eq_top}) -> ({eq_right}, {eq_bottom})")
print(f"Grid: {cols}x{rows}, slot: {slot_width:.1f}x{slot_height:.1f}")

# Zrób screenshot
print("\nOtwórz EQ w grze i naciśnij ENTER...")
input()

bbox = (eq_left, eq_top, eq_right, eq_bottom)
screenshot = ImageGrab.grab(bbox)
eq_img = np.array(screenshot)
eq_img = cv2.cvtColor(eq_img, cv2.COLOR_RGB2BGR)

# Wytnij wszystkie sloty
output_folder = 'eq_slots'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

print(f"\nWycinam sloty do folderu: {output_folder}/")

skip_slots = [0, 5]  # Zbroja

for slot_idx in range(45):
    if slot_idx in skip_slots:
        continue
    
    col = slot_idx % cols
    row = slot_idx // cols
    
    # Bbox slotu (z marginesem 2px)
    x1 = int(col * slot_width) + 2
    y1 = int(row * slot_height) + 2
    x2 = int((col + 1) * slot_width) - 2
    y2 = int((row + 1) * slot_height) - 2
    
    # Wytnij
    slot_img = eq_img[y1:y2, x1:x2]
    
    # Sprawdź czy slot nie jest pusty (średnia jasność)
    gray = cv2.cvtColor(slot_img, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    
    if mean_brightness > 30:  # Slot niepusty
        filename = f"{output_folder}/slot_{slot_idx:02d}_k{col}_w{row}.png"
        cv2.imwrite(filename, slot_img)
        print(f"  ✅ Slot {slot_idx:2d} (k={col}, w={row}): {slot_img.shape[1]}x{slot_img.shape[0]}px")

print(f"\n✅ Gotowe! Sprawdź folder {output_folder}/")
print("\nTeraz:")
print("  1. Przejrzyj pliki w folderze eq_slots/")
print("  2. Zmień nazwy na np: karas.png, butelka.png, ...")
print("  3. Przenieś do trash/ lub fish_kill/")