# color_picker.py - Narzędzie do analizy kolorów pod kursorem

import cv2
import numpy as np
import pyautogui
import keyboard
import time

def main():
    print("="*60)
    print("NARZĘDZIE DO ANALIZY KOLORÓW - Fishing Bot")
    print("="*60)
    print("\nInstrukcja:")
    print("1. Najedź myszką na RYBĘ w oknie łowienia")
    print("2. Naciśnij SPACJĘ aby zapisać kolor")
    print("3. Naciśnij ESC aby zakończyć")
    print("\nKolory będą wyświetlane na bieżąco pod kursorem.\n")
    
    saved_colors = []
    running = True
    
    def on_escape(e):
        nonlocal running
        running = False
    
    def on_space(e):
        x, y = pyautogui.position()
        
        # Pobierz kolor pod kursorem (bezpieczna metoda)
        try:
            screenshot = pyautogui.screenshot(region=(x, y, 1, 1))
            pixel = screenshot.getpixel((0, 0))
            r, g, b = pixel[0], pixel[1], pixel[2]
            
            # Konwersja do HSV
            pixel_bgr = np.uint8([[[b, g, r]]])
            pixel_hsv = cv2.cvtColor(pixel_bgr, cv2.COLOR_BGR2HSV)
            h, s, v = pixel_hsv[0][0]
            
            saved_colors.append({
                'pos': (x, y),
                'bgr': (b, g, r),
                'hsv': (int(h), int(s), int(v))
            })
            
            print(f"\n💾 ZAPISANO KOLOR #{len(saved_colors)}:")
            print(f"   Pozycja: ({x}, {y})")
            print(f"   BGR: ({b}, {g}, {r})")
            print(f"   HSV: ({int(h)}, {int(s)}, {int(v)})")
            print()
        except Exception as ex:
            print(f"\n❌ Błąd: {ex}")
    
    keyboard.on_press_key('space', on_space)
    keyboard.on_press_key('esc', on_escape)
    
    print("Ruszaj myszką... (kolory na żywo)\n")
    
    last_print = 0
    while running:
        current_time = time.time()
        
        # Aktualizuj co 200ms
        if current_time - last_print > 0.2:
            x, y = pyautogui.position()
            
            try:
                screenshot = pyautogui.screenshot(region=(x, y, 1, 1))
                pixel = screenshot.getpixel((0, 0))
                r, g, b = pixel[0], pixel[1], pixel[2]
                
                pixel_bgr = np.uint8([[[b, g, r]]])
                pixel_hsv = cv2.cvtColor(pixel_bgr, cv2.COLOR_BGR2HSV)
                h, s, v = pixel_hsv[0][0]
                
                print(f"Pos: ({x:4d}, {y:4d}) | BGR: ({r:3d}, {g:3d}, {b:3d}) | HSV: ({int(h):3d}, {int(s):3d}, {int(v):3d})   ", end='\r')
                
            except:
                pass
            
            last_print = current_time
        
        time.sleep(0.05)
    
    keyboard.unhook_all()
    
    # Podsumowanie
    print("\n\n" + "="*60)
    print("PODSUMOWANIE ZAPISANYCH KOLORÓW:")
    print("="*60)
    
    if saved_colors:
        # Oblicz zakresy
        h_min = min(c['hsv'][0] for c in saved_colors)
        h_max = max(c['hsv'][0] for c in saved_colors)
        s_min = min(c['hsv'][1] for c in saved_colors)
        s_max = max(c['hsv'][1] for c in saved_colors)
        v_min = min(c['hsv'][2] for c in saved_colors)
        v_max = max(c['hsv'][2] for c in saved_colors)
        
        print(f"\nZapisano {len(saved_colors)} kolorów:")
        for i, c in enumerate(saved_colors, 1):
            print(f"  #{i}: HSV({c['hsv'][0]:3d}, {c['hsv'][1]:3d}, {c['hsv'][2]:3d})")
        
        # Sugerowane zakresy (z marginesem)
        margin_h = 10
        margin_s = 30
        margin_v = 30
        
        suggested_lower = (
            max(0, h_min - margin_h),
            max(0, s_min - margin_s),
            max(0, v_min - margin_v)
        )
        suggested_upper = (
            min(180, h_max + margin_h),
            min(255, s_max + margin_s),
            min(255, v_max + margin_v)
        )
        
        print(f"\n📋 SUGEROWANE ZAKRESY DLA config.py:")
        print(f"   FISH_COLOR_HSV = {{")
        print(f"       'lower': {suggested_lower},")
        print(f"       'upper': {suggested_upper}")
        print(f"   }}")
        
    else:
        print("\nNie zapisano żadnych kolorów.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()