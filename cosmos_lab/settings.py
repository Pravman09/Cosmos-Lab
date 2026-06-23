"""Application settings for Cosmos Lab."""

from __future__ import annotations

import os

APP_NAME = "Cosmos Lab"
VERSION = "1.0.0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SAVES_DIR = os.path.join(BASE_DIR, "saves")
AUTOSAVE_FILE = os.path.join(SAVES_DIR, "autosave.json")

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 900
FPS = 60

SIDEBAR_WIDTH = 360
BOTTOM_BAR_HEIGHT = 86
TOP_BAR_HEIGHT = 46

BACKGROUND = (5, 8, 16)
PANEL_BG = (16, 22, 34)
PANEL_BG_2 = (24, 32, 48)
PANEL_BORDER = (60, 76, 102)
TEXT = (226, 234, 246)
MUTED_TEXT = (145, 160, 182)
ACCENT = (80, 170, 255)
ACCENT_2 = (126, 231, 135)
DANGER = (255, 96, 96)
WARNING = (255, 191, 92)

# Simulation units are SI: meters, kilograms, seconds.
# This scale means 1 screen pixel represents 2e8 meters at zoom=1.
METERS_PER_PIXEL = 2.0e8
MIN_ZOOM = 1.0e-5
MAX_ZOOM = 1.0e6
ZOOM_STEP = 1.13

CAMERA_MOVE_SPEED = 850.0
CAMERA_SMOOTHING = 0.16

G = 6.67430e-11
DEFAULT_GRAVITY_MULTIPLIER = 1.0
SOFTENING = 1.0e3

TIME_SPEEDS = [0.0, 1.0, 10.0, 100.0, 1000.0, 10000.0]
DEFAULT_TIME_SPEED_INDEX = 2
BASE_DT = 3600.0
MAX_SUBSTEPS = 18
MAX_STEP_SECONDS = 6.0 * 3600.0
MIN_STEP_SECONDS = 30.0
INTEGRATOR_WARNING_SPLITS = 6
FAST_INTEGRATOR_BODY_COUNT = 80
LARGE_SYSTEM_MAX_SUBSTEPS = 4
LARGE_SYSTEM_MAX_STEP_SECONDS = 24.0 * 3600.0

TRAIL_LENGTH = 620
PREDICTION_STEPS = 360
PREDICTION_DT = 12.0 * 3600.0

STAR_COUNT = 800
AUTOSAVE_SECONDS = 35.0

COLLISION_MERGE = "Merge"
COLLISION_ELASTIC = "Elastic"
COLLISION_DESTRUCTIVE = "Destructive"
COLLISION_MODES = [COLLISION_MERGE, COLLISION_ELASTIC, COLLISION_DESTRUCTIVE]

BODY_TYPES = [
    "Star",
    "Planet",
    "Moon",
    "Asteroid",
    "Comet",
    "Black Hole",
    "Neutron Star",
    "White Dwarf",
]

SPAWN_TEMPLATES = {
    "Star": {"mass": 1.98847e30, "radius": 6.957e8, "density": 1408.0, "temperature": 5772.0, "color": (255, 211, 105)},
    "Planet": {"mass": 5.9722e24, "radius": 6.371e6, "density": 5514.0, "temperature": 288.0, "color": (85, 145, 255)},
    "Moon": {"mass": 7.342e22, "radius": 1.7374e6, "density": 3344.0, "temperature": 220.0, "color": (185, 190, 198)},
    "Asteroid": {"mass": 9.5e20, "radius": 4.7e5, "density": 2160.0, "temperature": 160.0, "color": (150, 132, 116)},
    "Comet": {"mass": 2.2e14, "radius": 5.0e3, "density": 600.0, "temperature": 90.0, "color": (180, 230, 255)},
    "Black Hole": {"mass": 1.98847e31, "radius": 3.0e4, "density": 1.0e18, "temperature": 0.0, "color": (8, 8, 12)},
    "Neutron Star": {"mass": 2.8e30, "radius": 1.2e4, "density": 3.7e17, "temperature": 6.0e5, "color": (190, 218, 255)},
    "White Dwarf": {"mass": 1.0e30, "radius": 7.0e6, "density": 1.0e9, "temperature": 1.0e4, "color": (230, 238, 255)},
}

KEY_HELP = [
    "Left drag: spawn with velocity",
    "Right click: inspect",
    "WASD/Arrows: pan",
    "Mouse wheel: zoom",
    "Space: pause/play",
    "1-8: body type",
    "P: presets",
    "S/O: save/load",
    "T/L/V/G/C: toggles",
    "Delete: delete",
    "F: follow selected",
]
