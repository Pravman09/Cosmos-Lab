"""Physical constants and reference bodies."""

from __future__ import annotations

import math

try:
    from astropy import constants as const
except Exception:  # pragma: no cover - app intentionally explains missing deps at runtime.
    const = None


def _value(name: str, fallback: float) -> float:
    if const is None:
        return fallback
    try:
        return float(getattr(const, name).value)
    except AttributeError:
        return fallback


G = _value("G", 6.67430e-11)
C = _value("c", 299792458.0)
AU = _value("au", 1.495978707e11)
M_SUN = _value("M_sun", 1.98847e30)
R_SUN = _value("R_sun", 6.957e8)
M_EARTH = _value("M_earth", 5.9722e24)
R_EARTH = _value("R_earth", 6.371e6)
M_JUPITER = _value("M_jup", 1.89813e27)
R_JUPITER = _value("R_jup", 6.9911e7)

DAY = 86400.0
YEAR = 365.25 * DAY

REFERENCE = {
    "Sun": dict(type="Star", mass=M_SUN, radius=R_SUN, density=1408.0, temperature=5772.0, color=(255, 213, 122)),
    "Mercury": dict(type="Planet", mass=3.3011e23, radius=2.4397e6, density=5427.0, temperature=440.0, color=(178, 168, 150)),
    "Venus": dict(type="Planet", mass=4.8675e24, radius=6.0518e6, density=5243.0, temperature=737.0, color=(222, 176, 103)),
    "Earth": dict(type="Planet", mass=M_EARTH, radius=R_EARTH, density=5514.0, temperature=288.0, color=(82, 145, 240)),
    "Moon": dict(type="Moon", mass=7.342e22, radius=1.7374e6, density=3344.0, temperature=220.0, color=(188, 190, 198)),
    "Mars": dict(type="Planet", mass=6.4171e23, radius=3.3895e6, density=3933.0, temperature=210.0, color=(210, 104, 65)),
    "Jupiter": dict(type="Planet", mass=M_JUPITER, radius=R_JUPITER, density=1326.0, temperature=165.0, color=(218, 176, 134)),
    "Saturn": dict(type="Planet", mass=5.6834e26, radius=5.8232e7, density=687.0, temperature=134.0, color=(223, 199, 143)),
    "Uranus": dict(type="Planet", mass=8.6810e25, radius=2.5362e7, density=1271.0, temperature=76.0, color=(154, 218, 220)),
    "Neptune": dict(type="Planet", mass=1.02413e26, radius=2.4622e7, density=1638.0, temperature=72.0, color=(75, 116, 235)),
}


def circular_orbit_speed(parent_mass: float, distance: float) -> float:
    return math.sqrt(G * parent_mass / max(distance, 1.0))
