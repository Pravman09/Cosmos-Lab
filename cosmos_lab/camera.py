"""Smooth pan and zoom camera."""

from __future__ import annotations

import numpy as np
import pygame

from settings import CAMERA_MOVE_SPEED, CAMERA_SMOOTHING, MAX_ZOOM, METERS_PER_PIXEL, MIN_ZOOM, SIDEBAR_WIDTH, ZOOM_STEP
from utils import clamp, vec2


class Camera:
    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size
        self.position = np.zeros(2, dtype=float)
        self.target_position = np.zeros(2, dtype=float)
        self.zoom = 1.0
        self.follow_id: str | None = None

    @property
    def center(self) -> np.ndarray:
        w, h = self.screen_size
        return np.array([(w - SIDEBAR_WIDTH) * 0.5, h * 0.5], dtype=float)

    def resize(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size

    def meters_per_pixel(self) -> float:
        return METERS_PER_PIXEL / self.zoom

    def world_to_screen(self, world: np.ndarray | tuple[float, float]) -> np.ndarray:
        return (vec2(world) - self.position) / self.meters_per_pixel() + self.center

    def screen_to_world(self, screen: tuple[int, int] | np.ndarray) -> np.ndarray:
        return (vec2(screen) - self.center) * self.meters_per_pixel() + self.position

    def zoom_at(self, mouse_pos: tuple[int, int], direction: int) -> None:
        before = self.screen_to_world(mouse_pos)
        factor = ZOOM_STEP if direction > 0 else 1.0 / ZOOM_STEP
        self.zoom = clamp(self.zoom * factor, MIN_ZOOM, MAX_ZOOM)
        after = self.screen_to_world(mouse_pos)
        delta = before - after
        self.position += delta
        self.target_position += delta

    def pan_pixels(self, delta: tuple[float, float]) -> None:
        self.target_position -= vec2(delta) * self.meters_per_pixel()

    def center_on(self, world_position: np.ndarray) -> None:
        self.target_position = vec2(world_position)
        self.position = self.target_position.copy()

    def update(self, dt: float, keys, followed_body=None) -> None:
        if followed_body is not None:
            self.target_position = followed_body.position.copy()
        move = np.zeros(2, dtype=float)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move[0] -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move[0] += 1.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move[1] -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move[1] += 1.0
        if np.linalg.norm(move) > 0.0:
            self.follow_id = None
            move /= np.linalg.norm(move)
            self.target_position += move * CAMERA_MOVE_SPEED * self.meters_per_pixel() * dt
        alpha = 1.0 - (1.0 - CAMERA_SMOOTHING) ** max(dt * 60.0, 1.0)
        self.position += (self.target_position - self.position) * alpha
