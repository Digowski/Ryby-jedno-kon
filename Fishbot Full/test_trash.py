# test_trash.py - Test wyrzucania śmieci

import json
import os
from trash_handler import TrashHandler
from mouse_control import MouseController

print("="*50)
print("TEST WYRZUCANIA ŚMIECI")
print("="*50)

# Wczytaj kalibracje
if not os.path.exists('calibration.json'):
    print("❌ Brak calibration.json!")
    exit()

if not os.path.exists('calibration_eq.json'):
    print("❌ Brak calibration_eq.json - zrób KALIBRACJA EQ!")
    exit()

with open('calibration.json', 'r') as f:
    main_cal = json.load(f)

with open('calibration_eq.json', 'r') as f:
    eq_cal = json.load(f)

# Utwórz kontroler myszy i handler śmieci
mouse = MouseController(main_cal)
trash = TrashHandler(eq_cal, mouse)

print("\nNaciśnij ENTER aby rozpocząć test...")
input()

print("\n1. Przejeżdżam myszką po EQ...")
trash.sweep_eq()

print("\n2. Szukam śmieci...")
result = trash.find_trash()

if result:
    x, y, name = result
    print(f"✅ Znaleziono: {name} @ ({x}, {y})")
    
    print("\n3. Wyrzucam...")
    success = trash.discard_trash(x, y)
    
    if success:
        print("✅ Wyrzucono!")
    else:
        print("❌ Błąd wyrzucania")
else:
    print("❌ Nie znaleziono śmieci")

print("\n4. Pełny cykl (wszystkie śmieci)...")
discarded = trash.process_trash()
print(f"✅ Wyrzucono łącznie: {discarded} śmieci")

print("\nTest zakończony.")