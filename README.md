*This project has been created as part of the 42 curriculum by jbarreir.*

# Fly-in

<div align="center">


<img width="800" height="418" alt="fly_in_kv" src="https://github.com/user-attachments/assets/0120dad2-f25d-45b7-8e95-cb3a5c93ae61" />

#### *Like a traffic light, but for the sky.*


![Version](https://img.shields.io/badge/version-v1.1.0-blue.svg)
![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

</div>

## Description

**Fly-in** is a dynamic, terminal-based drone network simulation application. The project combines graph theory, pathfinding algorithms, and dynamic resource allocation to simulate a swarm of drones navigating through a complex network of hubs and constrained links.

The primary goal is to optimize the routing of a given number of drones from a starting hub to an end hub. The algorithm must intelligently manage link capacities and hub storage limits to minimize the total number of turns required for complete delivery. This project proved to be a highly interesting challenge for deepening our knowledge of algorithmic design, traffic management, and real-time terminal UI rendering.

## Instructions

### Prerequisites

- Python 3.10+
- A terminal supporting ANSI escape codes

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd fly-in
   ```

2. Use the provided `Makefile` to automatically set up the virtual environment, install the required dependencies (`pydantic`, `blessed`, `simple-term-menu`), and download the preconfigured maps:
   ```bash
   make install
   ```

### Execution

Run the main application using the Makefile:
```bash
make run
```
This will launch the interactive terminal menu where you can:
1. Select a map file from the directory browser.
2. Confirm the loaded map layout.
3. Choose a simulation speed (Manual step-by-step, Automatic, Fast, or Direct).

### UX Demo
<div align=center>
<img width="800" height="611" alt="fly_in_demo" src="https://github.com/user-attachments/assets/3872247a-4eed-419a-a94e-193e61de0178" />
</div>


## Algorithm Choices & Implementation Strategy

The simulation relies heavily on graph theory to resolve routing paths and bypass traffic bottlenecks.

### 1. Route Discovery (Depth-First Search)
To find all possible valid paths from the `start_hub` to the `end_hub`, the simulator utilizes a recursive **Depth-First Search (DFS)** algorithm paired with a backtracking mechanism.
- **Deep Exploration:** The algorithm starts at the origin and aggressively traverses down a single continuous branch of connected hubs until it reaches the destination or a dead end.
- **Cycle Prevention (Backtracking):** It maintains a dynamically updated set of `visited` nodes. Once a path reaches the `end_hub` or gets stuck, the algorithm *backtracks*—stepping back and unmarking the last node to explore alternative branches. This ensures every unique route is discovered without ever falling into infinite loops.
- **Dynamic Filtering:** During the recursive search, any hub tagged with a `BLOCKED` zone is immediately bypassed, guaranteeing that the generated flight plans never route drones through impassable airspace.



> **💡 Time Complexity Note:** While a standard DFS traversal operates in **$O(V + E)$** (where $V$ is vertices/hubs and $E$ is edges/links), discovering *all* unique non-cyclic paths in a dense graph approaches an exponential worst-case time complexity of **$O(2^V)$**. By immediately pruning `BLOCKED` zones and utilizing efficient backtracking, the algorithm aggressively bounds the search space while maintaining a minimal linear space complexity of **$O(V)$**.

### 2. Flight Planning & Traffic Management
At every turn, drones dynamically evaluate their available routes. The flight planner logic evaluates the network state based on strictly enforced rules:
- **Capacity Checks:** Ensures the target hub has physical drone bay space available.
- **Link Limits:** Checks if the connection between hubs has not exceeded its maximum simultaneous traffic capacity.
- **Zone Routing:** Prioritizes routes that contain priority zones or have structurally shorter turn lengths.

If primary paths are blocked by traffic congestion, drones will wait in a `STANDBY` state until bottlenecks clear, preventing complete network gridlock.

### 3. Efficiency, Scalability & Caching
To ensure the simulation can work seamlessly with a large number of drones, the algorithmic approach strictly avoids redundant calculations:
- **Caching vs Recalculating:** Instead of dynamically recalculating routing trees at every step, the simulator pre-calculates and **caches** all valid network paths during initialization (`self.all_paths`). Furthermore, the GUI rendering engine caches all A* calculated visual lines (`link_paths_cache`). During active flight, drones merely evaluate the *current capacity state* of the pre-cached routes.
- **Algorithm Complexity:** Because paths are cached, the per-turn flight planner operates with an efficient time complexity of **$O(D \times P)$**, where $D$ is the number of active drones and $P$ is the number of pre-calculated paths. The upfront route discovery operates at a worst-case of **$O(2^V)$** for fully connected graphs, but is aggressively pruned.
- **Memory Impact:** Storing path sequences in memory trades a negligible amount of RAM for massive CPU savings. The overall space complexity remains bounded to **$O(V + P)$** (Vertices + Paths). This ensures the application footprint remains tiny and impact on memory usage is almost completely unnoticeable, even when simulating hundreds of drones simultaneously.

## Map Parsing & Data Validation

To ensure the simulation operates flawlessly, the application employs a rigorous map parsing and validation layer powered by **Pydantic**. Instead of relying on manual dictionary checks, the map topology is ingested and validated through strongly typed data models (`Network`, `Hub`, `Drone`).

### Structural Integrity Checks
Before a single drone takes flight, a custom `@model_validator` analyzes the entire network graph to guarantee its topological integrity. It actively prevents silent runtime errors by catching invalid configurations immediately upon loading:
- **Unique Constraints:** Ensures all hubs have unique names and do not share overlapping coordinate placements.
- **Link Validations:** Detects self-referential links (a hub connecting to itself), duplicate connection entries, and connections referencing non-existent hubs.
- **Capacity Boundaries:** Enforces strict mathematical limits using Pydantic's `Field` constraints, ensuring variables like `max_drones` and `max_link_capacity` are logically sound (e.g., $\ge 1$).

By leveraging this robust validation pipeline, the engine guarantees that any loaded map—no matter how complex—is geometrically and logically viable before execution begins, making custom map creation safe and debuggable.

```
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

## Visual Representation & User Experience

Visualizing the network graph dynamically within a terminal environment was one of the most significant challenges of this project. The graphics layer utilizes the `blessed` library to render a clean, color-coded, and responsive UI. **This visual representation drastically enhances the understanding of the simulation by translating raw, abstract algorithmic decisions into a tangible, easy-to-monitor 2D system. Users can instantly pinpoint traffic bottlenecks, observe physical capacity loads, and intuitively understand exactly why the flight planner forces a drone into standby.**

### The GUI Line Routing Challenge
Drawing the connection links between hubs required much more than just drawing straight lines. To prevent lines from overlapping hubs and creating an illegible map, we implemented an **A* (A-Star) Pathfinding Algorithm** specifically dedicated to the UI rendering engine.
- The A* algorithm utilizes a Manhattan distance heuristic to find the shortest obstacle-free path for the ASCII lines.
- It actively penalizes unnecessary directional changes, ensuring the visual links remain orthogonal and structurally pleasing.
- This allows lines to dynamically route around hubs, mapping complex graph topologies beautifully without visual collisions.

Instead of simply finding the shortest path, our custom A* implementation balances spatial efficiency with visual aesthetics:
- **State Representation:** The algorithm tracks not only the current `(x, y)` coordinates of the line but also its current vector direction `(dx, dy)`. This allows the pathfinder to detect exactly when a line bends.
- **Heuristic Function:** It utilizes a **Manhattan distance** heuristic (`|x1 - x2| + |y1 - y2|`). Unlike straight-line (Euclidean) distance, Manhattan distance calculates the path exactly as a taxi would navigate a city block—moving strictly horizontally and vertically. This is mathematically ideal for terminal environments, as characters are bound to a rigid grid and true diagonal movement is impossible.
- **Turn Penalization:** Within the priority queue, paths are sorted first by their total projected length (`f-score`), and secondly by the number of directional changes (`turns`). This heavily penalizes zigzagging, forcing the algorithm to prefer long, straight, orthogonal lines that are visually legible.
- **Smart Crossings & Obstacle Evasion:** The algorithm treats hubs as solid obstacles. Furthermore, when evaluating the next step, it reads the terminal matrix to allow **perpendicular crossings** over existing lines (e.g., a vertical line traversing a horizontal one) but explicitly forbids overlapping parallel lines to prevent visual merging.

### UX Enhancements
- **Live Traffic Metrics:** Connection lines embed real-time traffic capacities in their center (e.g., `2/5` indicates 2 drones out of a 5-drone capacity are currently traversing).
- **Status Panels:** A split-pane text view provides live logs of drone statuses and turn completions, paired with color-coded warnings and success messages.
- **Drone Bays:** Hubs visually reflect their current drone occupancy with clear `[●●○○]` indicators, allowing users to see network load at a glance.

## Performance Benchmarks

Below is a performance overview comparing the actual turns our algorithm took against reference target turns for various map topologies, along with their estimated difficulty:

| Map Name | Drones | Target Turns | Actual Turns | Efficiency | Difficulty |
|----------|--------|--------------|--------------|------------|------------|
| `linear_path` | 2 | 6 | 4 | 75% | Easy |
| `simple_fork` | 4 | 8 | 4 | 75% | Easy |
| `basic_capacity` | 4 | 6 | 4 | 75% | Easy |
| `dead_end_trap` | 5 | 12 | 8 | 50% | Medium |
| `circular_loop` | 6 | 15 | 15 | 33% | Medium |
| `priority_puzzle` | 5 | 12 | 7 | 57% | Medium |
| `maze_nightmare` | 8 | 30 | 13 | 55% | Hard |
| `capacity_hell` | 12 | 35 | 15 | 35% | Hard |
| `ultimate_challenge` | 15 | 40 | 26 | 48% | Hard |
| `the_impossible_dream` | 25 | 45 | 43 | 34% | Challenge |

*(Note: The "Impossible Dream" is a custom challenger map designed to test the limits of the pathfinding traffic controller rather than competing against a target.)*

## Resources & References

### Documentation & References
- **Python Documentation**: Standard libraries such as `heapq` used heavily for priority queues in our A* line-routing implementation.
- **Blessed Library**: [blessed.readthedocs.io](blessed.readthedocs.io) - Used for terminal sequence formatting and advanced screen control.
- **Pydantic**: Utilized for rigorous data validation and schema mapping during map parsing.
- **Graph Theory**: References regarding DFS optimization and spanning tree variants for path discovery.

### AI Usage Disclosure
In compliance with the project guidelines, Artificial Intelligence was utilized in the following capacities:
- **Algorithm Brainstorming:** Used to discuss and refine the A* heuristic logic specifically tailored for aesthetic 2D grid line-drawing in the terminal (penalizing turns).
- **Documentation:** AI assisted in structuring this README, ensuring all required 42 subject criteria were covered, and translating technical implementation notes into comprehensive documentation.
- **Code Quality Review:** Utilized to suggest optimizations for Python type hinting, exception handling, and edge-case resolution.
