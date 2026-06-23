"""Universe state and REBOUND-backed simulation."""

from __future__ import annotations

import math
import os
import random
import warnings
from typing import Iterable

import numpy as np
import rebound

from body import CelestialBody
from physics import collision_response, orbital_info, stable_orbit_velocity
from settings import (
    AUTOSAVE_FILE,
    BASE_DT,
    COLLISION_MERGE,
    DEFAULT_GRAVITY_MULTIPLIER,
    DEFAULT_TIME_SPEED_INDEX,
    FAST_INTEGRATOR_BODY_COUNT,
    LARGE_SYSTEM_MAX_STEP_SECONDS,
    LARGE_SYSTEM_MAX_SUBSTEPS,
    MAX_STEP_SECONDS,
    MAX_SUBSTEPS,
    MIN_STEP_SECONDS,
    INTEGRATOR_WARNING_SPLITS,
    SAVES_DIR,
    TIME_SPEEDS,
    TRAIL_LENGTH,
)
from utils import ensure_dirs, magnitude, pairwise, read_json, write_json


class Universe:
    def __init__(self) -> None:
        self.bodies: list[CelestialBody] = []
        self.time = 0.0
        self.paused = False
        self.time_speed_index = DEFAULT_TIME_SPEED_INDEX
        self.gravity_multiplier = DEFAULT_GRAVITY_MULTIPLIER
        self.collision_enabled = True
        self.collision_mode = COLLISION_MERGE
        self.trails_enabled = True
        self.labels_enabled = True
        self.velocity_vectors = True
        self.gravity_indicators = False
        self.predictions_enabled = True
        self.selected_id: str | None = None
        self._accumulator = 0.0
        ensure_dirs(SAVES_DIR)

    @property
    def time_speed(self) -> float:
        if self.paused:
            return 0.0
        return TIME_SPEEDS[self.time_speed_index]

    @property
    def selected_body(self) -> CelestialBody | None:
        return self.get_body(self.selected_id)

    def get_body(self, body_id: str | None) -> CelestialBody | None:
        if body_id is None:
            return None
        for body in self.bodies:
            if body.id == body_id:
                return body
        return None

    def add_body(self, body: CelestialBody) -> CelestialBody:
        body.created_at = self.time
        self.bodies.append(body)
        self.selected_id = body.id
        return body

    def delete_body(self, body_id: str | None) -> None:
        if body_id is None:
            return
        self.bodies = [body for body in self.bodies if body.id != body_id]
        if self.selected_id == body_id:
            self.selected_id = None

    def clone_selected(self) -> None:
        body = self.selected_body
        if body is not None:
            offset = np.array([body.radius * 5.0, body.radius * 2.0])
            self.add_body(body.clone(offset))

    def clear(self) -> None:
        self.bodies.clear()
        self.selected_id = None
        self.time = 0.0

    def cycle_time_speed(self, direction: int) -> None:
        self.time_speed_index = int(np.clip(self.time_speed_index + direction, 0, len(TIME_SPEEDS) - 1))
        if self.time_speed_index > 0:
            self.paused = False

    def update(self, real_dt: float) -> None:
        sim_speed = self.time_speed
        if sim_speed <= 0.0 or len(self.bodies) == 0:
            return
        target = BASE_DT * sim_speed * real_dt
        self._accumulator += target
        substeps = 0
        max_substeps = LARGE_SYSTEM_MAX_SUBSTEPS if len(self.bodies) >= FAST_INTEGRATOR_BODY_COUNT else MAX_SUBSTEPS
        max_step = LARGE_SYSTEM_MAX_STEP_SECONDS if len(self.bodies) >= FAST_INTEGRATOR_BODY_COUNT else MAX_STEP_SECONDS
        while self._accumulator > 0.0 and substeps < max_substeps:
            step = min(self._accumulator, max_step)
            self._integrate(step)
            self.time += step
            self._accumulator -= step
            substeps += 1
            if self.collision_enabled:
                self._handle_black_holes()
                self._handle_collisions()
        if self.trails_enabled:
            self._record_trails()

    def _make_simulation(self) -> rebound.Simulation:
        sim = rebound.Simulation()
        sim.G = 6.67430e-11 * self.gravity_multiplier
        if len(self.bodies) >= FAST_INTEGRATOR_BODY_COUNT:
            sim.integrator = "whfast"
            sim.dt = LARGE_SYSTEM_MAX_STEP_SECONDS
        else:
            sim.integrator = "ias15"
        for body in self.bodies:
            if body.frozen:
                sim.add(m=body.mass, x=body.position[0], y=body.position[1], z=0.0, vx=0.0, vy=0.0, vz=0.0)
            else:
                sim.add(m=body.mass, x=body.position[0], y=body.position[1], z=0.0, vx=body.velocity[0], vy=body.velocity[1], vz=0.0)
        return sim

    def _integrate(self, dt: float) -> None:
        movable = [body for body in self.bodies if not body.frozen]
        if len(movable) == 0:
            return
        if dt <= 0.0:
            return
        try:
            self._integrate_once(dt)
        except RuntimeWarning:
            self._integrate_with_smaller_steps(dt)

    def _integrate_with_smaller_steps(self, dt: float) -> None:
        pieces = INTEGRATOR_WARNING_SPLITS
        small_dt = max(dt / pieces, MIN_STEP_SECONDS)
        remaining = dt
        while remaining > 0.0:
            step = min(small_dt, remaining)
            try:
                self._integrate_once(step)
            except RuntimeWarning:
                if step <= MIN_STEP_SECONDS:
                    self.paused = True
                    self._accumulator = 0.0
                    return
                half = step * 0.5
                self._integrate_with_smaller_steps(half)
                self._integrate_with_smaller_steps(step - half)
            remaining -= step

    def _integrate_once(self, dt: float) -> None:
        sim = self._make_simulation()
        with warnings.catch_warnings():
            warnings.filterwarnings("error", message=".*IAS15 did not converge.*", category=RuntimeWarning)
            sim.integrate(dt)
        for body, particle in zip(self.bodies, sim.particles):
            if body.frozen:
                continue
            body.position[:] = [particle.x, particle.y]
            body.velocity[:] = [particle.vx, particle.vy]

    def _record_trails(self) -> None:
        stride = max(1, len(self.bodies) // 80)
        for index, body in enumerate(self.bodies):
            if index % stride != 0 or body.body_type in ("Asteroid", "Comet") and len(self.bodies) > 220:
                if len(body.trail) > TRAIL_LENGTH // 3:
                    body.trail = body.trail[-TRAIL_LENGTH // 3 :]
                continue
            point = (float(body.position[0]), float(body.position[1]))
            if not body.trail or magnitude(np.array(point) - np.array(body.trail[-1])) > max(body.display_radius * 0.15, 1.0e6):
                body.trail.append(point)
                if len(body.trail) > TRAIL_LENGTH:
                    body.trail.pop(0)

    def _handle_black_holes(self) -> None:
        survivors = list(self.bodies)
        for hole in [body for body in self.bodies if body.is_black_hole]:
            horizon = max(hole.schwarzschild_radius, hole.radius)
            accretion = horizon * 18.0
            for body in list(survivors):
                if body is hole:
                    continue
                dist = magnitude(body.position - hole.position)
                if dist < horizon + body.radius or dist < accretion and body.mass < hole.mass * 0.2:
                    total = hole.mass + body.mass
                    hole.velocity = (hole.velocity * hole.mass + body.velocity * body.mass) / total
                    hole.position = (hole.position * hole.mass + body.position * body.mass) / total
                    hole.mass = total
                    hole.radius = max(hole.radius, hole.schwarzschild_radius)
                    if body in survivors:
                        survivors.remove(body)
        self.bodies = survivors
        if self.selected_id and self.get_body(self.selected_id) is None:
            self.selected_id = None

    def _handle_collisions(self) -> None:
        removed: set[str] = set()
        additions: list[CelestialBody] = []
        for a, b in pairwise(self.bodies):
            if a.id in removed or b.id in removed:
                continue
            dist = magnitude(a.position - b.position)
            if dist <= max(a.display_radius + b.display_radius, 1.0):
                result = collision_response(a, b, self.collision_mode)
                removed.add(a.id)
                removed.add(b.id)
                additions.extend(result)
        if removed:
            self.bodies = [body for body in self.bodies if body.id not in removed]
            self.bodies.extend(additions)
            if self.selected_id in removed:
                self.selected_id = additions[0].id if additions else None

    def nearest_body(self, world_position: np.ndarray, max_distance: float) -> CelestialBody | None:
        best = None
        best_d = max_distance
        for body in self.bodies:
            d = magnitude(body.position - world_position)
            if d < best_d:
                best = body
                best_d = d
        return best

    def apply_stable_orbit_to_selected(self) -> None:
        body = self.selected_body
        parent = self.find_primary_for(body)
        if body is not None and parent is not None:
            body.velocity = stable_orbit_velocity(parent, body.position)

    def find_primary_for(self, body: CelestialBody | None) -> CelestialBody | None:
        if body is None:
            return None
        candidates = [other for other in self.bodies if other.id != body.id and other.mass > body.mass]
        if not candidates:
            return None
        return min(candidates, key=lambda other: magnitude(other.position - body.position))

    def selected_orbital_info(self):
        body = self.selected_body
        parent = self.find_primary_for(body)
        if body is None or parent is None:
            return None, None
        return parent, orbital_info(body, parent)

    def to_dict(self) -> dict:
        return {
            "app": "Cosmos Lab",
            "time": self.time,
            "paused": self.paused,
            "time_speed_index": self.time_speed_index,
            "gravity_multiplier": self.gravity_multiplier,
            "collision_enabled": self.collision_enabled,
            "collision_mode": self.collision_mode,
            "trails_enabled": self.trails_enabled,
            "labels_enabled": self.labels_enabled,
            "velocity_vectors": self.velocity_vectors,
            "gravity_indicators": self.gravity_indicators,
            "predictions_enabled": self.predictions_enabled,
            "selected_id": self.selected_id,
            "bodies": [body.to_dict() for body in self.bodies],
        }

    def load_dict(self, payload: dict) -> None:
        self.time = float(payload.get("time", 0.0))
        self.paused = bool(payload.get("paused", False))
        self.time_speed_index = int(payload.get("time_speed_index", DEFAULT_TIME_SPEED_INDEX))
        self.gravity_multiplier = float(payload.get("gravity_multiplier", DEFAULT_GRAVITY_MULTIPLIER))
        self.collision_enabled = bool(payload.get("collision_enabled", True))
        self.collision_mode = payload.get("collision_mode", COLLISION_MERGE)
        self.trails_enabled = bool(payload.get("trails_enabled", True))
        self.labels_enabled = bool(payload.get("labels_enabled", True))
        self.velocity_vectors = bool(payload.get("velocity_vectors", True))
        self.gravity_indicators = bool(payload.get("gravity_indicators", False))
        self.predictions_enabled = bool(payload.get("predictions_enabled", True))
        self.bodies = [CelestialBody.from_dict(item) for item in payload.get("bodies", [])]
        self.selected_id = payload.get("selected_id")
        if self.get_body(self.selected_id) is None:
            self.selected_id = self.bodies[0].id if self.bodies else None

    def save(self, path: str | None = None) -> str:
        target = path or os.path.join(SAVES_DIR, "cosmos_lab_save.json")
        write_json(target, self.to_dict())
        return target

    def load(self, path: str | None = None) -> None:
        self.load_dict(read_json(path or os.path.join(SAVES_DIR, "cosmos_lab_save.json")))

    def autosave(self) -> None:
        self.save(AUTOSAVE_FILE)

    def try_autoload(self) -> bool:
        if os.path.exists(AUTOSAVE_FILE):
            self.load(AUTOSAVE_FILE)
            return True
        return False

    def spawn_random_system(self, count: int = 80) -> None:
        from presets import random_galaxy

        self.load_dict(random_galaxy(count).to_dict())
