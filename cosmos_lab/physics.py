"""Physics calculations and collision helpers."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import numpy as np

from data import AU, C, G
from settings import COLLISION_DESTRUCTIVE, COLLISION_ELASTIC, COLLISION_MERGE
from utils import magnitude, normalize


@dataclass
class OrbitalInfo:
    distance: float
    relative_speed: float
    semi_major_axis: float | None
    eccentricity: float | None
    period: float | None
    is_bound: bool


def schwarzschild_radius(mass: float) -> float:
    return 2.0 * G * mass / (C * C)


def escape_velocity(mass: float, radius: float) -> float:
    return math.sqrt(2.0 * G * mass / max(radius, 1.0))


def surface_gravity(mass: float, radius: float) -> float:
    return G * mass / max(radius * radius, 1.0)


def roche_limit(primary_radius: float, primary_density: float, satellite_density: float) -> float:
    if satellite_density <= 0.0:
        return float("nan")
    return 2.44 * primary_radius * (primary_density / satellite_density) ** (1.0 / 3.0)


def hill_sphere(distance: float, body_mass: float, parent_mass: float) -> float:
    if parent_mass <= 0.0:
        return float("nan")
    return distance * (body_mass / (3.0 * parent_mass)) ** (1.0 / 3.0)


def habitable_zone(star_luminosity_solar: float) -> tuple[float, float]:
    luminosity = max(star_luminosity_solar, 1.0e-9)
    return math.sqrt(luminosity / 1.1) * AU, math.sqrt(luminosity / 0.53) * AU


def estimate_luminosity_solar(mass: float, solar_mass: float) -> float:
    ratio = max(mass / solar_mass, 1.0e-6)
    if ratio < 0.43:
        return 0.23 * ratio**2.3
    if ratio < 2.0:
        return ratio**4.0
    return 1.5 * ratio**3.5


def orbital_info(body, parent) -> OrbitalInfo:
    r_vec = body.position - parent.position
    v_vec = body.velocity - parent.velocity
    r = magnitude(r_vec)
    v = magnitude(v_vec)
    mu = G * (body.mass + parent.mass)
    if r <= 0.0 or mu <= 0.0:
        return OrbitalInfo(r, v, None, None, None, False)
    energy = 0.5 * v * v - mu / r
    h = abs(float(r_vec[0] * v_vec[1] - r_vec[1] * v_vec[0]))
    e_sq = 1.0 + (2.0 * energy * h * h) / (mu * mu)
    e = math.sqrt(max(0.0, e_sq))
    if energy < 0.0:
        a = -mu / (2.0 * energy)
        period = 2.0 * math.pi * math.sqrt(a**3 / mu)
        return OrbitalInfo(r, v, a, e, period, True)
    return OrbitalInfo(r, v, None, e, None, False)


def stable_orbit_velocity(parent, position: np.ndarray, clockwise: bool = False) -> np.ndarray:
    r_vec = np.asarray(position, dtype=float) - parent.position
    dist = max(magnitude(r_vec), 1.0)
    tangent = np.array([-r_vec[1], r_vec[0]], dtype=float)
    if clockwise:
        tangent *= -1.0
    return parent.velocity + normalize(tangent) * math.sqrt(G * parent.mass / dist)


def collision_response(a, b, mode: str) -> list:
    if mode == COLLISION_ELASTIC:
        n = normalize(b.position - a.position)
        if magnitude(n) <= 0.0:
            n = np.array([1.0, 0.0])
        rel = np.dot(a.velocity - b.velocity, n)
        if rel > 0.0:
            return [a, b]
        impulse = (2.0 * rel) / (a.mass + b.mass)
        if not a.frozen:
            a.velocity -= impulse * b.mass * n
        if not b.frozen:
            b.velocity += impulse * a.mass * n
        return [a, b]

    if mode == COLLISION_DESTRUCTIVE:
        relative_speed = magnitude(a.velocity - b.velocity)
        impact_energy = 0.5 * min(a.mass, b.mass) * relative_speed**2
        binding = G * a.mass * b.mass / max(a.radius + b.radius, 1.0)
        if impact_energy > 12.0 * binding and max(a.radius, b.radius) > 5.0e4:
            big = a if a.mass >= b.mass else b
            small = b if big is a else a
            big.damage = min(1.0, big.damage + 0.18)
            fragments = []
            for index in range(5):
                angle = random.random() * math.tau
                speed = relative_speed * random.uniform(0.08, 0.22)
                fragment = small.clone()
                fragment.name = f"Fragment {index + 1}"
                fragment.body_type = "Asteroid"
                fragment.mass = small.mass / 12.0
                fragment.radius = max(small.radius * 0.28, 100.0)
                fragment.density = small.density
                fragment.position = small.position + np.array([math.cos(angle), math.sin(angle)]) * small.radius * 1.4
                fragment.velocity = small.velocity + np.array([math.cos(angle), math.sin(angle)]) * speed
                fragment.color = (155, 130, 110)
                fragments.append(fragment)
            return [big] + fragments

    return [merge_bodies(a, b)]


def merge_bodies(a, b):
    from body import CelestialBody

    total_mass = a.mass + b.mass
    position = (a.position * a.mass + b.position * b.mass) / total_mass
    velocity = (a.velocity * a.mass + b.velocity * b.mass) / total_mass
    volume = (4.0 / 3.0) * math.pi * (a.radius**3 + b.radius**3)
    radius = (3.0 * volume / (4.0 * math.pi)) ** (1.0 / 3.0)
    density = total_mass / max(volume, 1.0)
    temperature = (a.temperature * a.mass + b.temperature * b.mass) / total_mass
    dominant = a if a.mass >= b.mass else b
    other = b if dominant is a else a
    color = tuple(int((ca * dominant.mass + cb * other.mass) / total_mass) for ca, cb in zip(dominant.color, other.color))
    body_type = dominant.body_type
    if a.body_type == "Black Hole" or b.body_type == "Black Hole":
        body_type = "Black Hole"
        radius = schwarzschild_radius(total_mass)
        color = (8, 8, 12)
    return CelestialBody(
        name=f"{dominant.name}+{other.name}",
        body_type=body_type,
        mass=total_mass,
        radius=radius,
        density=density,
        temperature=temperature,
        position=position,
        velocity=velocity,
        color=color,
        frozen=a.frozen and b.frozen,
        damage=max(a.damage, b.damage),
    )
