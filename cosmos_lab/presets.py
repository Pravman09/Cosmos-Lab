"""Scientific preset systems for Cosmos Lab."""

from __future__ import annotations

import math
import random

import numpy as np

from body import CelestialBody
from data import AU, G, M_EARTH, M_SUN, R_EARTH, R_SUN, REFERENCE, circular_orbit_speed
from physics import stable_orbit_velocity
from universe import Universe
from utils import random_color


PRESET_NAMES = [
    "Earth-Moon System",
    "Inner Solar System",
    "Full Solar System",
    "Binary Star System",
    "Triple Star System",
    "Black Hole + Star",
    "Asteroid Belt",
    "Planetary Ring System",
    "Rogue Planet",
    "Random Galaxy",
]


def make_body(name: str, position=(0.0, 0.0), velocity=(0.0, 0.0), **overrides) -> CelestialBody:
    source = dict(REFERENCE.get(name, REFERENCE["Earth"]))
    source.update(overrides)
    return CelestialBody(
        name=name,
        body_type=source.pop("type"),
        mass=source.pop("mass"),
        radius=source.pop("radius"),
        density=source.pop("density"),
        temperature=source.pop("temperature"),
        position=np.array(position, dtype=float),
        velocity=np.array(velocity, dtype=float),
        color=source.pop("color"),
    )


def universe_with(*bodies: CelestialBody) -> Universe:
    universe = Universe()
    for body in bodies:
        universe.add_body(body)
    if bodies:
        universe.selected_id = bodies[0].id
    return universe


def earth_moon() -> Universe:
    earth = make_body("Earth")
    moon_distance = 384_400_000.0
    moon = make_body("Moon", (moon_distance, 0.0), (0.0, circular_orbit_speed(earth.mass, moon_distance)))
    earth.velocity[1] = -moon.velocity[1] * moon.mass / earth.mass
    return universe_with(earth, moon)


def inner_solar_system() -> Universe:
    bodies = [make_body("Sun")]
    planets = [("Mercury", 0.387), ("Venus", 0.723), ("Earth", 1.0), ("Mars", 1.524)]
    for name, dist_au in planets:
        dist = dist_au * AU
        bodies.append(make_body(name, (dist, 0.0), (0.0, circular_orbit_speed(M_SUN, dist))))
    return universe_with(*bodies)


def full_solar_system() -> Universe:
    bodies = [make_body("Sun")]
    planets = [
        ("Mercury", 0.387),
        ("Venus", 0.723),
        ("Earth", 1.0),
        ("Mars", 1.524),
        ("Jupiter", 5.203),
        ("Saturn", 9.537),
        ("Uranus", 19.191),
        ("Neptune", 30.07),
    ]
    for index, (name, dist_au) in enumerate(planets):
        angle = index * 0.72
        dist = dist_au * AU
        pos = np.array([math.cos(angle), math.sin(angle)]) * dist
        tangent = np.array([-math.sin(angle), math.cos(angle)])
        bodies.append(make_body(name, pos, tangent * circular_orbit_speed(M_SUN, dist)))
    return universe_with(*bodies)


def binary_stars() -> Universe:
    separation = 0.55 * AU
    m1 = M_SUN
    m2 = 0.72 * M_SUN
    total = m1 + m2
    r1 = separation * m2 / total
    r2 = separation * m1 / total
    omega = math.sqrt(G * total / separation**3)
    a = make_body("Alpha A", (-r1, 0.0), (0.0, -omega * r1), type="Star", mass=m1, radius=R_SUN, density=1408.0, temperature=5900, color=(255, 220, 130))
    b = make_body("Alpha B", (r2, 0.0), (0.0, omega * r2), type="Star", mass=m2, radius=0.78 * R_SUN, density=2200.0, temperature=4900, color=(255, 166, 95))
    planet = make_body("Circumbinary Planet", (0.0, 2.0 * AU), (-circular_orbit_speed(total, 2.0 * AU), 0.0), type="Planet", mass=8.0 * M_EARTH, radius=1.9 * R_EARTH, density=4700.0, temperature=240, color=(95, 180, 210))
    return universe_with(a, b, planet)


def triple_stars() -> Universe:
    uni = binary_stars()
    c = make_body("Outer Red Dwarf", (0.0, -3.2 * AU), (circular_orbit_speed(1.72 * M_SUN, 3.2 * AU), 0.0), type="Star", mass=0.28 * M_SUN, radius=0.34 * R_SUN, density=9000.0, temperature=3200, color=(255, 100, 75))
    uni.add_body(c)
    return uni


def black_hole_star() -> Universe:
    hole_mass = 8.0 * M_SUN
    hole = make_body("Cygnus Lab BH", type="Black Hole", mass=hole_mass, radius=2.0 * G * hole_mass / (299792458.0**2), density=1e18, temperature=0, color=(5, 5, 8))
    star = make_body("Donor Star", (0.42 * AU, 0.0), (0.0, circular_orbit_speed(hole.mass, 0.42 * AU)), type="Star", mass=0.9 * M_SUN, radius=0.95 * R_SUN, density=1700.0, temperature=5400, color=(255, 210, 120))
    return universe_with(hole, star)


def asteroid_belt() -> Universe:
    sun = make_body("Sun")
    jupiter = make_body("Jupiter", (5.2 * AU, 0), (0, circular_orbit_speed(M_SUN, 5.2 * AU)))
    uni = universe_with(sun, jupiter)
    for i in range(150):
        dist = random.uniform(2.0, 3.4) * AU
        angle = random.random() * math.tau
        pos = np.array([math.cos(angle), math.sin(angle)]) * dist
        tangent = np.array([-math.sin(angle), math.cos(angle)])
        speed = circular_orbit_speed(M_SUN, dist) * random.uniform(0.94, 1.06)
        uni.add_body(make_body(f"Asteroid {i + 1}", pos, tangent * speed, type="Asteroid", mass=random.uniform(1e15, 5e19), radius=random.uniform(2e3, 8e4), density=2200.0, temperature=160, color=random_color((145, 128, 112), 35)))
    return uni


def ring_system() -> Universe:
    planet = make_body("Ring World", type="Planet", mass=4.8e26, radius=5.5e7, density=850.0, temperature=110, color=(184, 196, 155))
    uni = universe_with(planet)
    for i in range(220):
        dist = random.uniform(1.45, 2.25) * planet.radius
        angle = random.random() * math.tau
        pos = np.array([math.cos(angle), math.sin(angle)]) * dist
        tangent = np.array([-math.sin(angle), math.cos(angle)])
        speed = circular_orbit_speed(planet.mass, dist) * random.uniform(0.985, 1.015)
        uni.add_body(make_body(f"Ring Particle {i + 1}", pos, tangent * speed, type="Asteroid", mass=random.uniform(1e8, 8e11), radius=random.uniform(100.0, 700.0), density=920.0, temperature=95, color=random_color((188, 178, 150), 20)))
    return uni


def rogue_planet() -> Universe:
    star = make_body("Distant Star", (-1.8 * AU, 0.0), (0, 0), type="Star", mass=0.75 * M_SUN, radius=0.82 * R_SUN, density=2100.0, temperature=4700, color=(255, 175, 105))
    rogue = make_body("Rogue Planet", (2.1 * AU, -0.55 * AU), (-16_000, 7_500), type="Planet", mass=12 * M_EARTH, radius=2.1 * R_EARTH, density=6200.0, temperature=44, color=(80, 110, 145))
    return universe_with(star, rogue)


def random_galaxy(count: int = 260) -> Universe:
    core_mass = 1.0e36
    core = make_body("Central Massive Black Hole", type="Black Hole", mass=core_mass, radius=2.0 * G * core_mass / (299792458.0**2), density=1e18, temperature=0, color=(3, 3, 6))
    uni = universe_with(core)
    for i in range(count):
        dist = random.uniform(0.15, 9.0) * AU * 80.0
        angle = random.random() * math.tau
        spiral = angle + dist / (AU * 250.0)
        pos = np.array([math.cos(spiral), math.sin(spiral)]) * dist
        tangent = np.array([-math.sin(spiral), math.cos(spiral)])
        speed = circular_orbit_speed(core_mass, dist) * random.uniform(0.65, 1.15)
        kind = "Star" if random.random() < 0.62 else "Asteroid"
        mass = random.uniform(0.08, 2.2) * M_SUN if kind == "Star" else random.uniform(1e18, 1e23)
        radius = random.uniform(0.2, 1.5) * R_SUN if kind == "Star" else random.uniform(5e4, 6e5)
        color = random.choice([(255, 220, 140), (170, 205, 255), (255, 145, 105), (235, 238, 255)])
        uni.add_body(make_body(f"{kind} {i + 1}", pos, tangent * speed, type=kind, mass=mass, radius=radius, density=1600.0, temperature=random.uniform(2500, 9000), color=color))
    uni.time_speed_index = 2
    return uni


def get_preset(name: str) -> Universe:
    factories = {
        "Earth-Moon System": earth_moon,
        "Inner Solar System": inner_solar_system,
        "Full Solar System": full_solar_system,
        "Binary Star System": binary_stars,
        "Triple Star System": triple_stars,
        "Black Hole + Star": black_hole_star,
        "Asteroid Belt": asteroid_belt,
        "Planetary Ring System": ring_system,
        "Rogue Planet": rogue_planet,
        "Random Galaxy": random_galaxy,
    }
    return factories.get(name, earth_moon)()
