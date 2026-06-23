"""Utility functions used across Cosmos Lab."""

from __future__ import annotations

import json
import math
import os
import random
from typing import Iterable, Sequence

import numpy as np


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def vec2(value: Sequence[float] | np.ndarray) -> np.ndarray:
    return np.array([float(value[0]), float(value[1])], dtype=float)


def magnitude(value: Sequence[float] | np.ndarray) -> float:
    return float(np.linalg.norm(value))


def normalize(value: Sequence[float] | np.ndarray) -> np.ndarray:
    v = vec2(value)
    mag = magnitude(v)
    if mag <= 0.0:
        return np.zeros(2, dtype=float)
    return v / mag


def fmt_si(value: float, unit: str = "", precision: int = 3) -> str:
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    prefixes = [
        (1e24, "Y"),
        (1e21, "Z"),
        (1e18, "E"),
        (1e15, "P"),
        (1e12, "T"),
        (1e9, "G"),
        (1e6, "M"),
        (1e3, "k"),
        (1.0, ""),
        (1e-3, "m"),
        (1e-6, "u"),
        (1e-9, "n"),
    ]
    for factor, prefix in prefixes:
        if value >= factor or factor == 1e-9:
            return f"{sign}{value / factor:.{precision}g} {prefix}{unit}".strip()
    return f"{sign}{value:.{precision}g} {unit}".strip()


def fmt_time(seconds: float) -> str:
    seconds = abs(float(seconds))
    if seconds < 120:
        return f"{seconds:.1f} s"
    if seconds < 86400:
        return f"{seconds / 3600:.2f} h"
    if seconds < 365.25 * 86400:
        return f"{seconds / 86400:.2f} d"
    return f"{seconds / (365.25 * 86400):.2f} yr"


def safe_filename(name: str) -> str:
    cleaned = "".join(ch for ch in name if ch.isalnum() or ch in "-_ .").strip()
    return cleaned or "simulation"


def ensure_dirs(*paths: str) -> None:
    for path in paths:
        os.makedirs(path, exist_ok=True)


def read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str, payload: dict) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def random_color(base: tuple[int, int, int], spread: int = 28) -> tuple[int, int, int]:
    return tuple(int(clamp(channel + random.randint(-spread, spread), 30, 255)) for channel in base)


def pairwise(items: Iterable):
    items = list(items)
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            yield items[i], items[j]
