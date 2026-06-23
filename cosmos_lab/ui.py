"""Immediate-mode Pygame UI for Cosmos Lab."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from data import AU, M_SUN
from physics import escape_velocity, estimate_luminosity_solar, habitable_zone, hill_sphere, roche_limit, surface_gravity
from settings import (
    ACCENT,
    ACCENT_2,
    BODY_TYPES,
    BOTTOM_BAR_HEIGHT,
    COLLISION_MODES,
    DANGER,
    KEY_HELP,
    MUTED_TEXT,
    PANEL_BG,
    PANEL_BG_2,
    PANEL_BORDER,
    SCREEN_HEIGHT,
    SIDEBAR_WIDTH,
    TEXT,
    TIME_SPEEDS,
    TOP_BAR_HEIGHT,
    WARNING,
)
from utils import fmt_si, fmt_time, magnitude


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: str


class UI:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("Segoe UI", 14)
        self.small = pygame.font.SysFont("Segoe UI", 12)
        self.bold = pygame.font.SysFont("Segoe UI Semibold", 16)
        self.title = pygame.font.SysFont("Segoe UI Semibold", 20)
        self.buttons: list[Button] = []
        self.show_presets = False
        self.status = "Ready"
        self.edit_field = 0
        self.fields = ["mass", "radius", "vx", "vy", "x", "y"]
        self.sidebar_scroll = 0
        self.sidebar_content_height = 0

    def resize(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def scroll_sidebar(self, amount: int) -> None:
        visible_height = max(1, self.screen.get_height())
        max_scroll = max(0, self.sidebar_content_height - visible_height + 24)
        self.sidebar_scroll = max(0, min(max_scroll, self.sidebar_scroll + amount))

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                return button.action
        return None

    def draw(self, universe, active_type: str, dragging_info=None) -> None:
        self.buttons.clear()
        w, h = self.screen.get_size()
        self._panel(pygame.Rect(w - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, h), PANEL_BG)
        self._panel(pygame.Rect(0, h - BOTTOM_BAR_HEIGHT, w - SIDEBAR_WIDTH, BOTTOM_BAR_HEIGHT), PANEL_BG)
        self._topbar(universe, active_type)
        self._sidebar(universe, active_type)
        self._bottombar(universe, dragging_info)
        if self.show_presets:
            self._preset_overlay()

    def _panel(self, rect: pygame.Rect, color) -> None:
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, PANEL_BORDER, rect, 1)

    def _text(self, text: str, x: int, y: int, color=TEXT, font=None) -> pygame.Rect:
        surface = (font or self.font).render(text, True, color)
        rect = surface.get_rect(topleft=(x, y))
        self.screen.blit(surface, rect)
        return rect

    def _button(self, label: str, rect: pygame.Rect, action: str, active: bool = False, danger: bool = False) -> None:
        color = (38, 52, 74) if not active else (42, 95, 135)
        if danger:
            color = (90, 40, 48)
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        pygame.draw.rect(self.screen, ACCENT if active else PANEL_BORDER, rect, 1, border_radius=5)
        text = self.small.render(label, True, TEXT)
        self.screen.blit(text, text.get_rect(center=rect.center))
        self.buttons.append(Button(rect, label, action))

    def _topbar(self, universe, active_type: str) -> None:
        w = self.screen.get_width() - SIDEBAR_WIDTH
        self._panel(pygame.Rect(0, 0, w, TOP_BAR_HEIGHT), (10, 15, 25))
        self._text("Cosmos Lab", 16, 11, TEXT, self.title)
        state = "PAUSED" if universe.paused else f"{TIME_SPEEDS[universe.time_speed_index]:g}x"
        self._text(f"t = {fmt_time(universe.time)}   speed {state}   bodies {len(universe.bodies)}   tool {active_type}", 160, 15, MUTED_TEXT, self.font)

    def _sidebar(self, universe, active_type: str) -> None:
        x = self.screen.get_width() - SIDEBAR_WIDTH + 18
        clip = pygame.Rect(self.screen.get_width() - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, self.screen.get_height())
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip)
        y = 16 - self.sidebar_scroll
        self._text("Laboratory Controls", x, y, TEXT, self.title)
        y += 36
        for i, body_type in enumerate(BODY_TYPES):
            rect = pygame.Rect(x + (i % 2) * 158, y + (i // 2) * 32, 148, 26)
            self._button(f"{i + 1}. {body_type}", rect, f"type:{body_type}", active=body_type == active_type)
        y += 144
        self._text("Simulation", x, y, TEXT, self.bold)
        y += 28
        self._button("Pause/Play", pygame.Rect(x, y, 100, 26), "pause", active=universe.paused)
        self._button("Slower", pygame.Rect(x + 108, y, 78, 26), "slower")
        self._button("Faster", pygame.Rect(x + 194, y, 78, 26), "faster")
        y += 34
        self._button("Merge", pygame.Rect(x, y, 78, 26), "collision_mode:Merge", active=universe.collision_mode == "Merge")
        self._button("Elastic", pygame.Rect(x + 86, y, 78, 26), "collision_mode:Elastic", active=universe.collision_mode == "Elastic")
        self._button("Break", pygame.Rect(x + 172, y, 78, 26), "collision_mode:Destructive", active=universe.collision_mode == "Destructive")
        y += 36
        toggles = [
            ("Collisions", universe.collision_enabled, "toggle_collisions"),
            ("Trails", universe.trails_enabled, "toggle_trails"),
            ("Labels", universe.labels_enabled, "toggle_labels"),
            ("Vectors", universe.velocity_vectors, "toggle_vectors"),
            ("Gravity", universe.gravity_indicators, "toggle_gravity"),
            ("Predict", universe.predictions_enabled, "toggle_predictions"),
        ]
        for i, (label, active, action) in enumerate(toggles):
            self._button(label, pygame.Rect(x + (i % 3) * 94, y + (i // 3) * 31, 86, 25), action, active=active)
        y += 76
        self._text(f"Gravity multiplier: {universe.gravity_multiplier:.2f}", x, y, MUTED_TEXT, self.font)
        y += 24
        self._button("-G", pygame.Rect(x, y, 58, 25), "gravity_down")
        self._button("+G", pygame.Rect(x + 66, y, 58, 25), "gravity_up")
        self._button("Stable Orbit", pygame.Rect(x + 132, y, 118, 25), "stable_orbit", active=False)
        y += 43
        self._text("Body Inspector", x, y, TEXT, self.bold)
        y += 26
        y = self._inspector(universe, x, y)
        self.sidebar_content_height = y + self.sidebar_scroll + 20
        self.screen.set_clip(old_clip)
        if self.sidebar_content_height > self.screen.get_height():
            self._scrollbar()

    def _scrollbar(self) -> None:
        panel_x = self.screen.get_width() - SIDEBAR_WIDTH
        h = self.screen.get_height()
        track = pygame.Rect(panel_x + SIDEBAR_WIDTH - 8, 8, 4, h - 16)
        max_scroll = max(1, self.sidebar_content_height - h + 24)
        thumb_h = max(36, int(track.height * h / max(self.sidebar_content_height, h)))
        thumb_y = track.y + int((track.height - thumb_h) * self.sidebar_scroll / max_scroll)
        pygame.draw.rect(self.screen, (34, 44, 62), track, border_radius=3)
        pygame.draw.rect(self.screen, ACCENT, pygame.Rect(track.x, thumb_y, track.width, thumb_h), border_radius=3)

    def _inspector(self, universe, x: int, y: int) -> int:
        body = universe.selected_body
        if body is None:
            self._text("Right-click or spawn a body to inspect it.", x, y, MUTED_TEXT, self.font)
            return y + 30
        parent, orbit = universe.selected_orbital_info()
        rows = [
            ("Name", body.name),
            ("Type", body.body_type),
            ("Mass", fmt_si(body.mass, "kg")),
            ("Radius", fmt_si(body.radius, "m")),
            ("Density", fmt_si(body.density, "kg/m3")),
            ("Temp", fmt_si(body.temperature, "K")),
            ("Speed", fmt_si(body.speed, "m/s")),
            ("Escape v", fmt_si(body.escape_velocity(), "m/s")),
            ("Surface g", f"{surface_gravity(body.mass, body.radius):.3g} m/s2"),
        ]
        if body.is_black_hole:
            rows.append(("Schwarzschild", fmt_si(body.schwarzschild_radius, "m")))
        if parent is not None and orbit is not None:
            rows += [
                ("Primary", parent.name),
                ("Distance", fmt_si(orbit.distance, "m")),
                ("Period", fmt_time(orbit.period) if orbit.period else "unbound"),
                ("Eccentricity", f"{orbit.eccentricity:.3f}" if orbit.eccentricity is not None else "n/a"),
                ("Hill sphere", fmt_si(hill_sphere(orbit.distance, body.mass, parent.mass), "m")),
                ("Roche limit", fmt_si(roche_limit(parent.radius, parent.density, body.density), "m")),
            ]
            if parent.body_type == "Star":
                hz = habitable_zone(estimate_luminosity_solar(parent.mass, M_SUN))
                rows.append(("Habitable zone", f"{hz[0] / AU:.2f}-{hz[1] / AU:.2f} AU"))
        for label, value in rows[:20]:
            self._text(label, x, y, MUTED_TEXT, self.small)
            self._text(str(value), x + 118, y, TEXT, self.small)
            y += 18
        y += 8
        self._button("Delete", pygame.Rect(x, y, 70, 25), "delete", danger=True)
        self._button("Clone", pygame.Rect(x + 78, y, 70, 25), "clone")
        self._button("Freeze", pygame.Rect(x + 156, y, 70, 25), "freeze", active=body.frozen)
        y += 31
        self._button("Rename", pygame.Rect(x, y, 70, 25), "rename")
        self._button("Mass +", pygame.Rect(x + 78, y, 70, 25), "mass_up")
        self._button("Mass -", pygame.Rect(x + 156, y, 70, 25), "mass_down")
        y += 31
        self._button("Radius +", pygame.Rect(x, y, 70, 25), "radius_up")
        self._button("Radius -", pygame.Rect(x + 78, y, 70, 25), "radius_down")
        self._button("Stop", pygame.Rect(x + 156, y, 70, 25), "stop_body")
        return y + 31

    def _bottombar(self, universe, dragging_info) -> None:
        h = self.screen.get_height()
        x = 16
        y = h - BOTTOM_BAR_HEIGHT + 12
        status = self.status
        if dragging_info is not None:
            speed = magnitude(dragging_info)
            status = f"Spawn velocity: {fmt_si(speed, 'm/s')}  release to create"
        self._text(status, x, y, TEXT, self.bold)
        y += 28
        self._button("Presets (P)", pygame.Rect(x, y, 92, 26), "presets", active=self.show_presets)
        self._button("Save (S)", pygame.Rect(x + 102, y, 78, 26), "save")
        self._button("Load (O)", pygame.Rect(x + 188, y, 78, 26), "load")
        self._button("Random", pygame.Rect(x + 274, y, 82, 26), "random_system")
        self._button("Reset", pygame.Rect(x + 366, y, 68, 26), "reset", danger=True)
        self._button("Fullscreen", pygame.Rect(x + 442, y, 92, 26), "fullscreen")
        help_text = "   ".join(KEY_HELP[:6])
        self._text(help_text, x + 548, y + 6, MUTED_TEXT, self.small)

    def _preset_overlay(self) -> None:
        w, h = self.screen.get_size()
        rect = pygame.Rect(180, 90, min(520, w - SIDEBAR_WIDTH - 220), 420)
        pygame.draw.rect(self.screen, (14, 20, 31), rect, border_radius=8)
        pygame.draw.rect(self.screen, ACCENT, rect, 1, border_radius=8)
        self._text("Preset Simulations", rect.x + 20, rect.y + 18, TEXT, self.title)
        names = [
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
        for i, name in enumerate(names):
            r = pygame.Rect(rect.x + 20 + (i % 2) * 235, rect.y + 62 + (i // 2) * 58, 216, 42)
            self._button(f"{i + 1}. {name}", r, f"preset:{name}")

    def rename_selected(self, universe) -> None:
        body = universe.selected_body
        if body is None:
            return
        base = body.body_type
        siblings = [b for b in universe.bodies if b.body_type == base]
        body.name = f"{base} {len(siblings)}"
        self.status = f"Renamed selected body to {body.name}"
