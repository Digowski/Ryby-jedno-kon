# test_detection.py - v2.1 (naprawiony + obie grupy)

import cv2
import numpy as np
import os
import json
from PIL import ImageGrab

print("="*60)
print("TEST ROZPOZNAWANIA - v2.1")
print("="*60)

# Wczytaj kalibrację EQ
if not os.path.exists('calibration_eq.json'):
    print("❌ Brak calibration_eq.json!")
    exit()

with open('calibration_eq.json', 'r') as f:
    eq_cal = json.load(f)

eq_left = eq_cal.get('eq_left', 0)
eq_top = eq_cal.get('eq_top', 0)
eq_right = eq_cal.get('eq_right', 0)
eq_bottom = eq_cal.get('eq_bottom', 0)

eq_width = eq_right - eq_left
eq_height = eq_bottom - eq_top

print(f"EQ: ({eq_left}, {eq_top}) - ({eq_right}, {eq_bottom})")
print(f"Rozmiar: {eq_width}x{eq_height}")

# Grid 5x9
cols, rows = 5, 9
slot_width = eq_width / cols
slot_height = eq_height / rows

print(f"Sloty: {cols}x{rows}, rozmiar slotu: {slot_width:.1f}x{slot_height:.1f}")

# Skip slots (zbroja)
skip_slots = [0, 5]
print(f"Skip slots: {skip_slots}")

def pos_to_slot(local_x, local_y):
    col = int(local_x / slot_width)
    row = int(local_y / slot_height)
    col = max(0, min(col, cols - 1))
    row = max(0, min(row, rows - 1))
    return row * cols + col

def get_slot_bbox(slot_idx):
    col = slot_idx % cols
    row = slot_idx // cols
    x1 = int(col * slot_width)
    y1 = int(row * slot_height)
    x2 = int((col + 1) * slot_width)
    y2 = int((row + 1) * slot_height)
    return x1, y1, x2, y2

def load_templates(folder):
    templates = []
    if not os.path.exists(folder):
        return templates
    for f in os.listdir(folder):
        if f.lower().endswith(('.bmp', '.png', '.jpg')):
            filepath = os.path.join(folder, f)
            img = cv2.imread(filepath)
            if img is not None:
                h, w = img.shape[:2]
                templates.append({'name': f, 'image': img, 'width': w, 'height': h})
    return templates

# Wczytaj templates
print("\n--- ŚMIECI (trash/) ---")
trash_templates = load_templates('trash')
for t in trash_templates:
    print(f"  ✅ {t['name']} ({t['width']}x{t['height']})")
print(f"Razem: {len(trash_templates)}")

print("\n--- RYBY DO ZABICIA (fish_kill/) ---")
kill_templates = load_templates('fish_kill')
for t in kill_templates:
    print(f"  ✅ {t['name']} ({t['width']}x{t['height']})")
print(f"Razem: {len(kill_templates)}")

# Screenshot
print("\n" + "="*60)
print("Naciśnij ENTER aby zrobić screenshot EQ...")
input()

bbox = (eq_left, eq_top, eq_right, eq_bottom)
screenshot = ImageGrab.grab(bbox)
eq_img = np.array(screenshot)
eq_img = cv2.cvtColor(eq_img, cv2.COLOR_RGB2BGR)

print(f"Screenshot: {eq_img.shape}")

# SKANOWANIE
threshold = 0.75
all_found = {}

def scan_templates(templates, category_name, color):
    print(f"\n{'='*60}")
    print(f"SKANOWANIE: {category_name} (threshold={threshold})")
    print(f"{'='*60}")
    
    found = {}
    
    for template_data in templates:
        template = template_data['image']
        name = template_data['name']
        t_w, t_h = template_data['width'], template_data['height']
        
        try:
            result = cv2.matchTemplate(eq_img, template, cv2.TM_CCOEFF_NORMED)
        except cv2.error as e:
            print(f"  ⚠️ Błąd {name}: {e}")
            continue
        
        locations = np.where(result >= threshold)
        
        if len(locations[0]) > 0:
            print(f"\n{name}: {len(locations[0])} punktów")
        
        for pt_y, pt_x in zip(*locations):
            score = result[pt_y, pt_x]
            center_x = pt_x + t_w // 2
            center_y = pt_y + t_h // 2
            slot_idx = pos_to_slot(center_x, center_y)
            
            if slot_idx in skip_slots:
                print(f"  → SKIP slot {slot_idx}")
                continue
            
            if slot_idx < 0 or slot_idx >= 45:
                continue
            
            if slot_idx not in found or score > found[slot_idx][3]:
                found[slot_idx] = (center_x, center_y, name, score, color, category_name)
                col = slot_idx % cols
                row = slot_idx // cols
                print(f"  ✓ Slot {slot_idx} (k={col}, w={row}): {name} score={score:.3f}")
    
    return found

# Skanuj obie grupy
trash_found = scan_templates(trash_templates, "ŚMIECI", (0, 255, 0))  # Zielony
kill_found = scan_templates(kill_templates, "RYBY DO ZABICIA", (0, 0, 255))  # Czerwony

# Połącz wyniki
all_found.update(trash_found)
all_found.update(kill_found)

# RYSOWANIE
print(f"\n{'='*60}")
print(f"ZNALEZIONE PRZEDMIOTY: {len(all_found)}")
print(f"  - Śmieci: {len(trash_found)}")
print(f"  - Ryby do zabicia: {len(kill_found)}")
print(f"{'='*60}")

img_debug = eq_img.copy()

# Grid
for i in range(1, cols):
    x = int(i * slot_width)
    cv2.line(img_debug, (x, 0), (x, eq_height), (100, 100, 100), 1)
for i in range(1, rows):
    y = int(i * slot_height)
    cv2.line(img_debug, (0, y), (eq_width, y), (100, 100, 100), 1)

# Skip slots
for slot_idx in skip_slots:
    x1, y1, x2, y2 = get_slot_bbox(slot_idx)
    cv2.rectangle(img_debug, (x1, y1), (x2, y2), (0, 255, 255), 2)
    cv2.putText(img_debug, "SKIP", (x1 + 2, y1 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

# Znalezione przedmioty
for slot_idx, (cx, cy, name, score, color, category) in all_found.items():
    x1, y1, x2, y2 = get_slot_bbox(slot_idx)
    
    cv2.rectangle(img_debug, (x1, y1), (x2, y2), color, 2)
    cv2.drawMarker(img_debug, (int(cx), int(cy)), color, cv2.MARKER_CROSS, 10, 2)
    
    # Tekst
    label = f"{name[:10]}"
    cv2.putText(img_debug, label, (x1 + 2, y1 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
    
    col = slot_idx % cols
    row = slot_idx // cols
    icon = "🗑️" if category == "ŚMIECI" else "🔪"
    print(f"{icon} Slot {slot_idx:2d} (k={col}, w={row}): {name:20s} score={score:.3f}")

# Zapisz
cv2.imwrite('eq_detected_v2.png', img_debug)
cv2.imwrite('eq_screenshot_v2.png', eq_img)

print(f"\n✅ Zapisano eq_detected_v2.png")
print(f"✅ Zapisano eq_screenshot_v2.png")

print(f"\n{'='*60}")
print("LEGENDA:")
print("  🟢 ZIELONY = śmieci do wyrzucenia")
print("  🔴 CZERWONY = ryby do zabicia")
print("  🟡 ŻÓŁTY = skip slots (zbroja)")
print(f"{'='*60}")