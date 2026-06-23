"""Pygame renderer for the scientific sandbox."""

from __future__ import annotations

import math
import random
from typing import Iterable

import numpy as np
import pygame

from data import AU
from settings import BACKGROUND, BOTTOM_BAR_HEIGHT, METERS_PER_PIXEL, PREDICTION_DT, PREDICTION_STEPS, SIDEBAR_WIDTH, STAR_COUNT
from utils import clamp, magnitude


class Renderer:
    def __init__(self, screen: pygame.Surface, camera) -> None:
        self.screen = screen
        self.camera = camera
        self.font = pygame.font.SysFont("Segoe UI", 14)
        self.small_font = pygame.font.SysFont("Segoe UI", 12)
        self.label_font = pygame.font.SysFont("Segoe UI Semibold", 13)
        self.stars = self._make_stars()
        self.accretion_phase = 0.0

    def _make_stars(self) -> list[tuple[float, float, int, tuple[int, int, int]]]:
        rng = random.Random(42)
        return [
            (
                rng.uniform(-8000, 8000),
                rng.uniform(-8000, 8000),
                rng.choice([1, 1, 1, 2]),
                rng.choice([(120, 140, 180), (180, 195, 230), (90, 115, 155)]),
            )
            for _ in range(STAR_COUNT)
        ]

    def resize(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def draw(self, universe, dt: float) -> None:
        self.accretion_phase += dt
        self.screen.fill(BACKGROUND)
        self._draw_background()
        if universe.trails_enabled:
            self._draw_trails(universe.bodies)
        if universe.predictions_enabled and len(universe.bodies) <= 80:
            self._draw_predictions(universe)
        if universe.gravity_indicators:
            self._draw_gravity_indicators(universe.bodies)
        for body in sorted(universe.bodies, key=lambda b: b.mass):
            self._draw_body(body, selected=universe.selected_id == body.id, labels=universe.labels_enabled, velocity=universe.velocity_vectors)

    def _draw_background(self) -> None:
        w, h = self.screen.get_size()
        usable_w = w - SIDEBAR_WIDTH
        scale = 0.05 * self.camera.zoom
        for x, y, r, color in self.stars:
            sx = (x - self.camera.position[0] / METERS_PER_PIXEL * scale) % usable_w
            sy = (y - self.camera.position[1] / METERS_PER_PIXEL * scale) % h
            pygame.draw.circle(self.screen, color, (int(sx), int(sy)), r)

    def _screen_radius(self, body) -> int:
        raw = body.display_radius / self.camera.meters_per_pixel()
        if body.body_type in ("Asteroid", "Comet") and raw < 2:
            return 2
        if body.body_type == "Black Hole":
            return int(clamp(raw, 5, 120))
        return int(clamp(raw, 3, 80))

    def _draw_body(self, body, selected: bool, labels: bool, velocity: bool) -> None:
        pos = self.camera.world_to_screen(body.position)
        x, y = int(pos[0]), int(pos[1])
        if x < -160 or y < -160 or x > self.screen.get_width() - SIDEBAR_WIDTH + 160 or y > self.screen.get_height() + 160:
            return
        radius = self._screen_radius(body)
        if body.body_type in ("Star", "Neutron Star", "White Dwarf"):
            self._draw_glow((x, y), radius, body.color)
        if body.body_type == "Black Hole":
            self._draw_black_hole(body, (x, y), radius)
        elif body.body_type == "Comet":
            self._draw_comet(body, (x, y), radius)
        else:
            shade = tuple(max(0, c - 42) for c in body.color)
            pygame.draw.circle(self.screen, shade, (x + max(1, radius // 5), y + max(1, radius // 5)), radius)
            pygame.draw.circle(self.screen, body.color, (x, y), radius)
            if body.body_type == "Planet" and radius > 8:
                pygame.draw.arc(self.screen, (210, 210, 190), (x - radius * 2, y - radius // 2, radius * 4, radius), 0.05, math.pi - 0.05, max(1, radius // 8))
        if body.damage > 0.0:
            pygame.draw.circle(self.screen, (120, 40, 35), (x - radius // 3, y + radius // 5), max(1, int(radius * body.damage * 0.35)))
        if selected:
            pygame.draw.circle(self.screen, (90, 190, 255), (x, y), radius + 6, 2)
        if velocity:
            self._draw_velocity_vector(body, (x, y))
        if labels:
            label = self.label_font.render(body.name, True, (220, 230, 245))
            self.screen.blit(label, (x + radius + 5, y - 8))

    def _draw_glow(self, center: tuple[int, int], radius: int, color: tuple[int, int, int]) -> None:
        for factor, alpha in [(3.5, 26), (2.3, 42), (1.55, 64)]:
            r = int(radius * factor)
            surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, alpha), (r + 2, r + 2), r)
            self.screen.blit(surf, (center[0] - r - 2, center[1] - r - 2), special_flags=pygame.BLEND_PREMULTIPLIED)

    def _draw_black_hole(self, body, center: tuple[int, int], radius: int) -> None:
        x, y = center
        disk_r = radius * 4
        phase = self.accretion_phase * 1.8
        pygame.draw.circle(self.screen, (18, 19, 27), center, disk_r, 1)
        for i in range(34):
            angle = phase + i * math.tau / 34.0
            a2 = angle + 0.22
            color = (255, int(140 + 80 * math.sin(angle)), 70)
            rect = (x - disk_r, y - disk_r // 3, disk_r * 2, disk_r * 2 // 3)
            pygame.draw.arc(self.screen, color, rect, angle, a2, max(1, radius // 3))
        pygame.draw.circle(self.screen, (0, 0, 0), center, radius)
        pygame.draw.circle(self.screen, (120, 75, 255), center, radius + 2, 1)

    def _draw_comet(self, body, center: tuple[int, int], radius: int) -> None:
        speed = magnitude(body.velocity)
        if speed > 1.0:
            direction = -body.velocity / speed
            tail_end = np.array(center) + direction * min(90.0, speed / 420.0)
            pygame.draw.line(self.screen, (105, 180, 230), center, tail_end.astype(int), max(2, radius))
        pygame.draw.circle(self.screen, body.color, center, radius)

    def _draw_velocity_vector(self, body, center: tuple[int, int]) -> None:
        speed = magnitude(body.velocity)
        if speed <= 1.0:
            return
        vec = body.velocity / speed * clamp(speed / 160.0, 8.0, 70.0)
        end = (int(center[0] + vec[0]), int(center[1] + vec[1]))
        pygame.draw.line(self.screen, (126, 231, 135), center, end, 2)
        pygame.draw.circle(self.screen, (126, 231, 135), end, 3)

    def _draw_trails(self, bodies: Iterable) -> None:
        for body in bodies:
            if len(body.trail) < 2:
                continue
            points = [self.camera.world_to_screen(np.array(p)).astype(int) for p in body.trail[-360:]]
            clipped = [(int(p[0]), int(p[1])) for p in points if -200 < p[0] < self.screen.get_width() and -200 < p[1] < self.screen.get_height() + 200]
            if len(clipped) >= 2:
                color = tuple(int(c * 0.58) for c in body.color)
                pygame.draw.lines(self.screen, color, False, clipped, 1)

    def _draw_gravity_indicators(self, bodies: Iterable) -> None:
        for body in bodies:
            if body.mass <= 0:
                continue
            influence = math.sqrt(body.mass) * 1.0e-7 / self.camera.meters_per_pixel()
            r = int(clamp(influence, 8, 220))
            pos = self.camera.world_to_screen(body.position).astype(int)
            pygame.draw.circle(self.screen, (50, 80, 120), pos, r, 1)

    def _draw_predictions(self, universe) -> None:
        selected = universe.selected_body
        if selected is None:
            return
        parent = universe.find_primary_for(selected)
        if parent is None:
            return
        r = selected.position.copy()
        v = selected.velocity.copy()
        points = []
        mu = 6.67430e-11 * universe.gravity_multiplier * parent.mass
        for _ in range(PREDICTION_STEPS):
            diff = parent.position - r
            dist = max(magnitude(diff), 1.0)
            acc = diff / dist * (mu / (dist * dist))
            v += acc * PREDICTION_DT
            r += v * PREDICTION_DT
            points.append(tuple(self.camera.world_to_screen(r).astype(int)))
        if len(points) > 3:
            pygame.draw.lines(self.screen, (95, 160, 255), False, points, 1)
