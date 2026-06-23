"""Celestial body data model."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any
from uuid import uuid4

import numpy as np

from data import C, G
from utils import magnitude, vec2


@dataclass
class CelestialBody:
    name: str
    body_type: str
    mass: float
    radius: float
    density: float
    temperature: float
    position: np.ndarray
    velocity: np.ndarray
    color: tuple[int, int, int]
    frozen: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)
    trail: list[tuple[float, float]] = field(default_factory=list)
    damage: float = 0.0
    created_at: float = 0.0

    def __post_init__(self) -> None:
        self.position = vec2(self.position)
        self.velocity = vec2(self.velocity)
        self.color = tuple(int(c) for c in self.color)
        if self.density <= 0.0 and self.radius > 0.0:
            self.density = self.mass / ((4.0 / 3.0) * math.pi * self.radius**3)

    @property
    def speed(self) -> float:
        return magnitude(self.velocity)

    @property
    def is_black_hole(self) -> bool:
        return self.body_type == "Black Hole"

    @property
    def schwarzschild_radius(self) -> float:
        if not self.is_black_hole:
            return 0.0
        return 2.0 * G * self.mass / (C * C)

    @property
    def display_radius(self) -> float:
        return max(self.radius, self.schwarzschild_radius)

    def escape_velocity(self, distance: float | None = None) -> float:
        r = max(float(distance if distance is not None else self.radius), 1.0)
        return math.sqrt(2.0 * G * self.mass / r)

    def surface_gravity(self) -> float:
        return G * self.mass / max(self.radius * self.radius, 1.0)

    def clone(self, offset: tuple[float, float] = (0.0, 0.0)) -> "CelestialBody":
        return CelestialBody(
            name=f"{self.name} Copy",
            body_type=self.body_type,
            mass=self.mass,
            radius=self.radius,
            density=self.density,
            temperature=self.temperature,
            position=self.position + vec2(offset),
            velocity=self.velocity.copy(),
            color=self.color,
            frozen=self.frozen,
            damage=self.damage,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.body_type,
            "mass": self.mass,
            "radius": self.radius,
            "density": self.density,
            "temperature": self.temperature,
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "color": list(self.color),
            "frozen": self.frozen,
            "damage": self.damage,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CelestialBody":
        body = cls(
            name=payload["name"],
            body_type=payload.get("type", payload.get("body_type", "Planet")),
            mass=float(payload["mass"]),
            radius=float(payload["radius"]),
            density=float(payload.get("density", 0.0)),
            temperature=float(payload.get("temperature", 0.0)),
            position=payload.get("position", [0.0, 0.0]),
            velocity=payload.get("velocity", [0.0, 0.0]),
            color=tuple(payload.get("color", (180, 200, 255))),
            frozen=bool(payload.get("frozen", False)),
            damage=float(payload.get("damage", 0.0)),
            created_at=float(payload.get("created_at", 0.0)),
        )
        body.id = payload.get("id", body.id)
        return body
