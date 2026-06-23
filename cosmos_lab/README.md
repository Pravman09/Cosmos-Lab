# Cosmos Lab

Cosmos Lab is a scientific 2D space sandbox and gravity laboratory written in Python. It uses Pygame for visualization, NumPy for vector math, Astropy constants for real units, and REBOUND for N-body orbital integration.

## Install

```bash
pip install pygame numpy astropy rebound
```

## Run

```bash
cd cosmos_lab
python main.py
```

## Controls

- Left click and drag in space: spawn the active body type with initial velocity
- Right click a body: inspect/select it
- Mouse wheel: zoom
- Mouse wheel over right panel: scroll controls
- Middle drag or WASD/arrow keys: pan camera
- F11 or Fullscreen button: toggle fullscreen
- Space: pause/play
- `+` / `-`: faster/slower simulation speed
- `1`-`8`: choose Star, Planet, Moon, Asteroid, Comet, Black Hole, Neutron Star, White Dwarf
- `P`: preset browser
- `S`: save to `saves/cosmos_lab_save.json`
- `O`: load from `saves/cosmos_lab_save.json`
- `T`: trails
- `L`: labels
- `V`: velocity vectors
- `G`: gravity influence indicators
- `C`: collisions
- `F`: follow selected body
- `H`: apply stable orbit helper to selected body
- Delete/Backspace: delete selected body

## Presets

Cosmos Lab includes Earth-Moon, Inner Solar System, Full Solar System, Binary Star, Triple Star, Black Hole + Star, Asteroid Belt, Planetary Ring System, Rogue Planet, and Random Galaxy presets.

## Notes

All simulation values are SI units: meters, kilograms, and seconds. The renderer scales those distances into screen space through the camera. REBOUND integrates gravity using the IAS15 integrator, which is well suited to accurate orbital mechanics for varied time steps.
