# Cosmos Lab

Cosmos Lab is a professional Python space sandbox and gravity simulation laboratory. It is designed as a scientific-style desktop application, not an arcade game. Users can create, inspect, edit, and experiment with planets, moons, stars, asteroids, comets, black holes, neutron stars, white dwarfs, and complete solar systems.

The simulator uses real physical units and an N-body physics engine to model gravitational interactions, orbital motion, collisions, and extreme astronomical objects.

## Technology Stack

- Python
- Pygame for visualization and input
- NumPy for vector math
- Astropy for astronomy constants
- REBOUND for N-body gravity simulation
- JSON for save/load files
- Object-oriented multi-file architecture

## Project Structure

```text
cosmos_lab/
├── main.py
├── settings.py
├── universe.py
├── body.py
├── physics.py
├── renderer.py
├── camera.py
├── ui.py
├── presets.py
├── data.py
├── utils.py
├── README.md
├── COSMOS_LAB_OVERVIEW.md
├── assets/
└── saves/
```

## Main Goal

Cosmos Lab lets users build and study 2D space systems in a sandbox environment. Users can spawn bodies, give them velocity, watch gravity shape their paths, inspect orbital data, test collisions, and load preset astronomical systems.

The application is intended to feel like a dark-themed scientific simulation tool.

## Celestial Bodies

Cosmos Lab supports the following body types:

- Stars
- Planets
- Moons
- Asteroids
- Comets
- Black holes
- Neutron stars
- White dwarfs

Each body has:

- Name
- Type
- Mass
- Radius
- Density
- Temperature
- Position
- Velocity
- Color
- Frozen/unfrozen state
- Orbit trail history
- Damage value for destructive collisions

All simulation values use realistic SI units:

- Meters
- Kilograms
- Seconds

## Physics System

The simulation uses REBOUND for N-body gravity. Bodies attract each other according to their mass and distance.

Supported physics features include:

- Real gravitational attraction
- Orbital mechanics
- Stable orbits
- Binary star behavior
- Triple star behavior
- Escape velocity calculations
- Orbital period estimation
- Orbital eccentricity estimation
- Surface gravity calculation
- Roche limit calculation
- Hill sphere calculation
- Habitable zone estimation
- Schwarzschild radius calculation

## Simulation Speed

The simulator includes multiple time speeds:

- Pause
- 1x
- 10x
- 100x
- 1000x
- 10000x

Large systems automatically use a faster REBOUND integrator configuration for better performance.

## Black Hole Physics

Black holes include:

- Schwarzschild radius
- Event horizon
- Accretion zone
- Absorption of nearby bodies
- Mass growth after absorption
- Event horizon visualization
- Animated accretion disk visualization

Objects that pass too close to a black hole can be absorbed, increasing the black hole's mass.

## Collision System

Cosmos Lab supports three collision modes:

1. Merge collisions
2. Elastic collisions
3. Destructive collisions

Collision behavior depends on:

- Mass
- Radius
- Density
- Relative velocity
- Impact energy

Merge collisions combine bodies into a larger body. Destructive collisions can damage larger bodies and create asteroid fragments.

## Sandbox Tools

Users can:

- Spawn bodies
- Delete bodies
- Clone bodies
- Rename bodies
- Change mass
- Change radius
- Stop a body's velocity
- Freeze/unfreeze bodies
- Apply a stable orbit helper
- Change gravity strength
- Toggle collisions
- Toggle orbit trails
- Toggle labels
- Toggle velocity vectors
- Toggle gravity influence indicators
- Toggle predicted trajectories
- Generate random systems

Bodies are spawned by clicking and dragging. The drag direction and length set the starting velocity.

## Camera System

The camera supports:

- Smooth panning
- Smooth zoom
- Very large zoom range
- Follow selected body
- Center on body
- Free camera mode
- Fullscreen mode

## Body Inspector

The right-side inspector panel displays information about the selected body.

Displayed data includes:

- Name
- Type
- Mass
- Radius
- Density
- Temperature
- Speed
- Escape velocity
- Surface gravity
- Primary body
- Distance from primary
- Orbital period
- Orbital eccentricity
- Hill sphere
- Roche limit
- Schwarzschild radius for black holes
- Habitable zone estimate for star systems

The panel is scrollable so all controls remain accessible on smaller screens.

## Visualization Features

The renderer draws:

- Dark space background
- Procedural star field
- Glowing stars
- Planets with simple shading
- Planetary rings
- Comet tails
- Black holes
- Animated accretion disks
- Orbit trails
- Predicted trajectories
- Body labels
- Velocity vectors
- Gravity influence indicators

No external image assets are required.

## Preset Simulations

Cosmos Lab includes these built-in presets:

1. Earth-Moon System
2. Inner Solar System
3. Full Solar System
4. Binary Star System
5. Triple Star System
6. Black Hole + Star
7. Asteroid Belt
8. Planetary Ring System
9. Rogue Planet
10. Random Galaxy

These presets allow quick experimentation with common astronomy scenarios.

## Save System

Cosmos Lab supports JSON-based persistence:

- Manual save
- Manual load
- Autosave

Save files are stored in:

```text
cosmos_lab/saves/
```

The default manual save file is:

```text
cosmos_lab/saves/cosmos_lab_save.json
```

The autosave file is:

```text
cosmos_lab/saves/autosave.json
```

## Controls

| Control | Action |
|---|---|
| Left click + drag | Spawn body with starting velocity |
| Right click body | Select/inspect body |
| Mouse wheel | Zoom camera |
| Mouse wheel over right panel | Scroll UI panel |
| Middle mouse drag | Pan camera |
| WASD / Arrow keys | Move camera |
| Space | Pause/play |
| `+` / `-` | Increase/decrease simulation speed |
| `1`-`8` | Select body type |
| `P` | Open preset menu |
| `S` | Save |
| `O` | Load |
| `T` | Toggle trails |
| `L` | Toggle labels |
| `V` | Toggle velocity vectors |
| `G` | Toggle gravity indicators |
| `C` | Toggle collisions |
| `F` | Follow selected body |
| `H` | Apply stable orbit helper |
| Delete / Backspace | Delete selected body |
| F11 | Toggle fullscreen |

## Performance Notes

Cosmos Lab can simulate hundreds of bodies, but large systems are naturally more demanding because gravity calculations become expensive as body count increases.

The heaviest presets are:

- Random Galaxy
- Planetary Ring System
- Asteroid Belt

For smoother performance on weaker laptops:

- Use 1x, 10x, or 100x simulation speed
- Turn off predicted trajectories
- Turn off labels for large systems
- Turn off gravity influence indicators
- Avoid spawning bodies directly inside stars or black holes
- Use shorter drag arrows when spawning new bodies

Large systems automatically switch to a faster physics integrator configuration to reduce crashes and slowdowns.

## Installation

Install dependencies:

```bash
pip install pygame numpy astropy rebound
```

## Running

From the project folder:

```bash
cd cosmos_lab
python main.py
```

Or from the parent workspace:

```bash
python cosmos_lab/main.py
```

## Design Philosophy

Cosmos Lab is designed to be:

- Scientific
- Experimental
- Educational
- Dark-themed
- Professional-looking
- Useful for testing gravity and orbital behavior

It is not designed as an arcade game. The focus is exploration, observation, and experimentation with realistic space physics.
