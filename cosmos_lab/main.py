"""Cosmos Lab entry point."""

from __future__ import annotations

import math
import os
import sys

try:
    import numpy as np
    import pygame
except Exception as exc:
    print("Cosmos Lab requires pygame and numpy. Install with: pip install pygame numpy astropy rebound")
    raise

from body import CelestialBody
from camera import Camera
from presets import get_preset
from renderer import Renderer
from settings import (
    APP_NAME,
    AUTOSAVE_SECONDS,
    BODY_TYPES,
    FPS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SIDEBAR_WIDTH,
    SPAWN_TEMPLATES,
)
from ui import UI
from universe import Universe
from utils import magnitude


class CosmosLabApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(APP_NAME)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        self.fullscreen = False
        self.windowed_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.clock = pygame.time.Clock()
        self.camera = Camera(self.screen.get_size())
        self.renderer = Renderer(self.screen, self.camera)
        self.ui = UI(self.screen)
        self.universe = get_preset("Earth-Moon System")
        self.active_type = "Planet"
        self.running = True
        self.drag_start_world: np.ndarray | None = None
        self.drag_current_world: np.ndarray | None = None
        self.autosave_timer = 0.0
        self.camera.center_on(np.zeros(2))

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._events()
            keys = pygame.key.get_pressed()
            followed = self.universe.get_body(self.camera.follow_id)
            self.camera.update(dt, keys, followed)
            self.universe.update(dt)
            self.autosave_timer += dt
            if self.autosave_timer >= AUTOSAVE_SECONDS:
                self.autosave_timer = 0.0
                self.universe.autosave()
            self.renderer.draw(self.universe, dt)
            drag_vec = None
            if self.drag_start_world is not None and self.drag_current_world is not None:
                start = self.camera.world_to_screen(self.drag_start_world).astype(int)
                end = self.camera.world_to_screen(self.drag_current_world).astype(int)
                pygame.draw.line(self.screen, (126, 231, 135), start, end, 2)
                pygame.draw.circle(self.screen, (126, 231, 135), end, 4)
                drag_vec = self._drag_velocity()
            self.ui.draw(self.universe, self.active_type, drag_vec)
            pygame.display.flip()
        self.universe.autosave()
        pygame.quit()

    def _events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.windowed_size = event.size
                    self._apply_display(event.size, pygame.RESIZABLE)
            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[0] >= self.screen.get_width() - SIDEBAR_WIDTH:
                    self.ui.scroll_sidebar(-event.y * 42)
                else:
                    self.camera.zoom_at(mouse_pos, event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._mouse_down(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self._mouse_up(event)
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[1]:
                    self.camera.pan_pixels(event.rel)
                if self.drag_start_world is not None:
                    self.drag_current_world = self.camera.screen_to_world(event.pos)
            elif event.type == pygame.KEYDOWN:
                self._key_down(event.key)

    def _mouse_down(self, event) -> None:
        if event.button == 1:
            action = self.ui.handle_click(event.pos)
            if action:
                self._action(action)
                return
            if event.pos[0] < self.screen.get_width() - SIDEBAR_WIDTH:
                self.drag_start_world = self.camera.screen_to_world(event.pos)
                self.drag_current_world = self.drag_start_world.copy()
        elif event.button == 3:
            world = self.camera.screen_to_world(event.pos)
            max_distance = 24 * self.camera.meters_per_pixel()
            body = self.universe.nearest_body(world, max_distance)
            self.universe.selected_id = body.id if body else None
        elif event.button == 2:
            self.camera.follow_id = None

    def _mouse_up(self, event) -> None:
        if event.button == 1 and self.drag_start_world is not None:
            if event.pos[0] < self.screen.get_width() - SIDEBAR_WIDTH:
                self.drag_current_world = self.camera.screen_to_world(event.pos)
                self._spawn_body()
            self.drag_start_world = None
            self.drag_current_world = None

    def _drag_velocity(self) -> np.ndarray:
        if self.drag_start_world is None or self.drag_current_world is None:
            return np.zeros(2)
        return (self.drag_start_world - self.drag_current_world) / 4000.0

    def _spawn_body(self) -> None:
        assert self.drag_start_world is not None
        template = SPAWN_TEMPLATES[self.active_type]
        velocity = self._drag_velocity()
        number = sum(1 for b in self.universe.bodies if b.body_type == self.active_type) + 1
        body = CelestialBody(
            name=f"{self.active_type} {number}",
            body_type=self.active_type,
            mass=template["mass"],
            radius=template["radius"],
            density=template["density"],
            temperature=template["temperature"],
            position=self.drag_start_world.copy(),
            velocity=velocity,
            color=template["color"],
        )
        if self.active_type == "Black Hole":
            body.radius = max(body.radius, body.schwarzschild_radius)
        self.universe.add_body(body)
        self.ui.status = f"Created {body.name}"

    def _key_down(self, key: int) -> None:
        if pygame.K_1 <= key <= pygame.K_8:
            self.active_type = BODY_TYPES[key - pygame.K_1]
            return
        actions = {
            pygame.K_SPACE: "pause",
            pygame.K_r: "reset",
            pygame.K_DELETE: "delete",
            pygame.K_BACKSPACE: "delete",
            pygame.K_t: "toggle_trails",
            pygame.K_l: "toggle_labels",
            pygame.K_v: "toggle_vectors",
            pygame.K_g: "toggle_gravity",
            pygame.K_c: "toggle_collisions",
            pygame.K_p: "presets",
            pygame.K_s: "save",
            pygame.K_o: "load",
            pygame.K_EQUALS: "faster",
            pygame.K_PLUS: "faster",
            pygame.K_MINUS: "slower",
            pygame.K_f: "follow",
            pygame.K_h: "stable_orbit",
            pygame.K_F11: "fullscreen",
        }
        action = actions.get(key)
        if action:
            self._action(action)

    def _action(self, action: str) -> None:
        if action.startswith("type:"):
            self.active_type = action.split(":", 1)[1]
        elif action.startswith("preset:"):
            self.universe = get_preset(action.split(":", 1)[1])
            self.camera.follow_id = None
            self.camera.center_on(np.zeros(2))
            self.ui.show_presets = False
            self.ui.status = "Preset loaded"
        elif action.startswith("collision_mode:"):
            self.universe.collision_mode = action.split(":", 1)[1]
        elif action == "pause":
            self.universe.paused = not self.universe.paused
        elif action == "slower":
            self.universe.cycle_time_speed(-1)
        elif action == "faster":
            self.universe.cycle_time_speed(1)
        elif action == "reset":
            self.universe = get_preset("Earth-Moon System")
            self.camera.center_on(np.zeros(2))
            self.ui.status = "Reset to Earth-Moon System"
        elif action == "delete":
            self.universe.delete_body(self.universe.selected_id)
        elif action == "clone":
            self.universe.clone_selected()
        elif action == "freeze":
            body = self.universe.selected_body
            if body:
                body.frozen = not body.frozen
        elif action == "rename":
            self.ui.rename_selected(self.universe)
        elif action == "mass_up":
            self._scale_selected(mass=1.25)
        elif action == "mass_down":
            self._scale_selected(mass=0.8)
        elif action == "radius_up":
            self._scale_selected(radius=1.2)
        elif action == "radius_down":
            self._scale_selected(radius=0.833333)
        elif action == "stop_body":
            body = self.universe.selected_body
            if body:
                body.velocity[:] = 0.0
        elif action == "presets":
            self.ui.show_presets = not self.ui.show_presets
        elif action == "save":
            path = self.universe.save()
            self.ui.status = f"Saved: {path}"
        elif action == "load":
            try:
                self.universe.load()
                self.ui.status = "Loaded save"
            except FileNotFoundError:
                self.ui.status = "No save file found"
        elif action == "random_system":
            self.universe = get_preset("Random Galaxy")
            self.camera.center_on(np.zeros(2))
            self.ui.status = "Generated random galaxy"
        elif action == "toggle_collisions":
            self.universe.collision_enabled = not self.universe.collision_enabled
        elif action == "toggle_trails":
            self.universe.trails_enabled = not self.universe.trails_enabled
        elif action == "toggle_labels":
            self.universe.labels_enabled = not self.universe.labels_enabled
        elif action == "toggle_vectors":
            self.universe.velocity_vectors = not self.universe.velocity_vectors
        elif action == "toggle_gravity":
            self.universe.gravity_indicators = not self.universe.gravity_indicators
        elif action == "toggle_predictions":
            self.universe.predictions_enabled = not self.universe.predictions_enabled
        elif action == "gravity_down":
            self.universe.gravity_multiplier = max(0.01, self.universe.gravity_multiplier / 1.25)
        elif action == "gravity_up":
            self.universe.gravity_multiplier = min(100.0, self.universe.gravity_multiplier * 1.25)
        elif action == "stable_orbit":
            self.universe.apply_stable_orbit_to_selected()
        elif action == "follow":
            body = self.universe.selected_body
            self.camera.follow_id = body.id if body else None
        elif action == "fullscreen":
            self._toggle_fullscreen()

    def _apply_display(self, size: tuple[int, int], flags: int) -> None:
        self.screen = pygame.display.set_mode(size, flags)
        self.camera.resize(self.screen.get_size())
        self.renderer.resize(self.screen)
        self.ui.resize(self.screen)

    def _toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self._apply_display((0, 0), pygame.FULLSCREEN)
            self.ui.status = "Fullscreen enabled - press F11 to return"
        else:
            self._apply_display(self.windowed_size, pygame.RESIZABLE)
            self.ui.status = "Windowed mode"

    def _scale_selected(self, mass: float = 1.0, radius: float = 1.0) -> None:
        body = self.universe.selected_body
        if body is None:
            return
        body.mass *= mass
        body.radius *= radius
        if body.body_type == "Black Hole":
            body.radius = max(body.radius, body.schwarzschild_radius)
        volume = 4.0 / 3.0 * math.pi * max(body.radius, 1.0) ** 3
        body.density = body.mass / volume


def main() -> None:
    try:
        app = CosmosLabApp()
        app.run()
    except ImportError as exc:
        print("Missing dependency. Install with:")
        print("pip install pygame numpy astropy rebound")
        raise


if __name__ == "__main__":
    main()
