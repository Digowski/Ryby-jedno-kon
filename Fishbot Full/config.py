# config.py - Konfiguracja Bota v1.4 (przyspieszone)

# === OPÓŹNIENIA (w sekundach) ===
DELAYS = {
    'after_bait': 0.15,          # Po założeniu robaka (było 0.3, teraz 2x szybciej)
    'after_cast': 0.5,           # Po zarzuceniu wędki
    'detection_speed': 0.012,    # Skanowanie ryby (~83 FPS)
    'between_fish_clicks': 0.075, # Między klikami w rybę (było 0.15, teraz 2x szybciej)
    'after_click_fish': 0.05,    # Po kliknięciu w rybę
    'skip_animation': 0.3,       # Po kliknięciu zbroi
    'animation_wait': 4.0,       # Czekanie bez zbroi (gdy pominięto kalibrację)
    'after_discard': 0.3,        # Po wyrzuceniu śmiecia
    'check_bait': 1.0,           # Co ile sprawdzać robaka
    'window_appear': 1.2         # Czas na pojawienie się okna
}

# === LIMITY ===
MAX_FISH_ATTEMPTS = 3         # Informacyjne (już nie używane - klikamy do zamknięcia)
FISHING_TIMEOUT = 18          # Maksymalny czas na złowienie
TRASH_CHECK_INTERVAL = 10     # Co ile ryb sprawdzać śmieci
BAIT_STACK_SIZE = 200
MIN_BAIT_WARNING = 20

# === ROZDZIELCZOŚCI ===
GAME_WINDOW_SIZE = (800, 600)
SCREEN_RESOLUTION = (1920, 1080)
SCALE = 1.0

# === KOŁO ŁOWIENIA ===
CIRCLE_DIAMETER = 304
CIRCLE_RADIUS = 152
SAFE_CLICK_MARGIN = 10

# === POZYCJE (wczytywane z calibration.json) ===
POSITIONS = {
    'bait_f1_x': 0,
    'bait_f1_y': 0,
    'bait_f2_x': 0,
    'bait_f2_y': 0,
    'bait_f3_x': 0,
    'bait_f3_y': 0,
    'bait_f4_x': 0,
    'bait_f4_y': 0,
    'active_bait_slot': 'f1',
    'armor_slot_x': 0,
    'armor_slot_y': 0,
    'armor_enabled': True,       # Czy pomijamy animację zbroją
    'fishing_window_left': 0,
    'fishing_window_top': 0,
    'fishing_window_right': 0,
    'fishing_window_bottom': 0,
    'circle_center_x': 0,        # Obliczany automatycznie
    'circle_center_y': 0,        # Obliczany automatycznie
    'circle_radius': 152,
}

# === KOLORY RYBY (HSV) ===
FISH_COLOR_HSV = {
    'lower': (95, 100, 110),
    'upper': (115, 150, 140)
}

# === ŚMIECI DO WYRZUCENIA ===
TRASH_ITEMS = [
    'far1.bmp',
    'far2.bmp',
    'far3.bmp',
    'far4.bmp',
    'far5.bmp',
    'wyb.bmp'
]

# === RYBY DO ZABICIA ===
DEAD_FISH = [
    'mkaras.bmp',
    'mmandaryna.bmp'
]

# === HOTKEYS ===
HOTKEY_START = 'home'
HOTKEY_PAUSE = 'end'
HOTKEY_STOP = 'esc'
HOTKEY_CAST = 'space'

# === USTAWIENIA DETEKCJI ===
DETECTION_THRESHOLD = 0.7
FISH_MIN_SIZE = 15
SCAN_REGION_PADDING = 5

# === MULTI-WINDOW ===
ACTIVE_PROFILE = 1

# === SUWAKI PRĘDKOŚCI (dla GUI) ===
SPEED_SLIDERS = {
    'fish_click_speed': {
        'min': 0.05,
        'max': 0.3,
        'default': 0.075,
        'label': 'Szybkość klikania ryby (s)'
    },
    'after_armor_delay': {
        'min': 0.1,
        'max': 0.5,
        'default': 0.15,
        'label': 'Opóźnienie po zbroi (s)'
    },
    'window_timeout': {
        'min': 3.0,
        'max': 15.0,
        'default': 5.0,
        'label': 'Timeout na okno (s)'
    },
    'scan_speed': {
        'min': 0.01,
        'max': 0.05,
        'default': 0.012,
        'label': 'Szybkość skanowania (s)'
    },
    'animation_wait': {
        'min': 5.0,
        'max': 15.0,
        'default': 8.0,
        'label': 'Czekanie bez zbroi (s)'
    }
}