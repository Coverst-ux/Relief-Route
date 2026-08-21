# ReliefRoute — Project Documentation

## Purpose

ReliefRoute is a disaster resource routing tool built for Doha, Qatar. It calculates the fastest road routes from supply depots to areas in need during a crisis, then decides how much aid should move along each route based on what each depot can actually supply and what each area actually needs. It runs on Doha's real road network rather than simplified or synthetic map data.

This project was built as a proof of concept to explore real routing and flow-optimization algorithms end to end, not as a claim that Qatar's existing disaster-response infrastructure has a gap this fills.

## Target Audience

- Hackathon judges and reviewers evaluating the Software Development track submission
- Developers interested in shortest-path and min-cost max-flow algorithms applied to real-world geographic data
- Anyone curious about how disaster logistics and resource allocation problems can be modeled computationally

## Main Features

- **Custom Dijkstra shortest-path algorithm**, built from scratch and verified against NetworkX's built-in implementation, run on Doha's real OSMnx road graph (16,498 nodes, 36,060 edges)
- **Custom Min-Cost Max-Flow algorithm**, built from scratch using Bellman-Ford for shortest augmenting paths, deciding how much supply moves from each depot to each need point based on capacity and demand constraints
- **Live toggling** of depots and need points, with routes recalculating instantly on every change
- **Road closure simulation**, with closed roads shown as dashed red lines on the map and all affected routes automatically rerouted
- **Interactive map** built with Folium, showing active/inactive depots and need points, flow-weighted route lines, and closed roads
- **Custom frontend**, built by hand with HTML and CSS, no frameworks used

## Technology Stack

- **Python** -> core language
- **Flask** -> web framework and routing
- **OSMnx** -> real-world road network data for Doha
- **NetworkX** -> underlying graph structure (OSMnx is built on top of it), also used to verify the custom Dijkstra implementation
- **Folium** -> interactive map rendering
- **HTML/CSS** -> custom frontend, no framework
- **Gunicorn** -> production WSGI server
- **Render** -> live deployment hosting

## Installation Guide

### Prerequisites

- Python 3.10 or higher
- pip

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/Coverst-ux/Relief-Route
   cd ReliefRoute
   ```

2. (Recommended) Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Ensure `doha_graph.graphml` is present in the project root. This file contains the pre-downloaded Doha road network used by the app.

5. Run the app locally:
   ```
   python app.py
   ```

6. Open a browser and go to `http://127.0.0.1:5000`.

### Running in Production

The app is configured to run with Gunicorn for production deployment:
```
gunicorn app:app --bind 0.0.0.0:$PORT
```
`$PORT` should be set by the hosting environment (e.g. Render sets this automatically).

## User Manual

### Viewing the Map

On loading the page, the map displays:
- **Green markers** -> active supply depots
- **Gray markers** -> inactive (deactivated) depots or need points
- **Red markers** -> active need points
- **Dark red lines** -> active flow routes, with line thickness proportional to the amount of supply moving along that route
- **Dashed red lines** -> closed roads

### Toggling Depots and Need Points

Click any marker to open its popup. The popup shows the location's name and its supply or demand amount, along with an Activate/Deactivate button. Clicking the button toggles that location on or off, and the page reloads with routes recalculated to reflect the change.

### Simulating Road Closures

In the "Road Closures" panel, check the box next to any closable road and click "Apply Closures." The map will redraw with the closed road shown as a dashed red line, and any routes that previously used that road will reroute automatically.

### Reading the Stats

The header displays three live statistics:
- **Units Flowing** -> total supply currently being routed across all active routes
- **Total Route Cost** -> combined distance (in meters) of all active routes
- **Depots Active** -> how many of the total depots are currently active

## Configuration

- **Depots, need points, supply, and demand values** are defined in `main.py` as Python dictionaries (`depots`, `needs`, `depots_supply`, `needs_demand`). These can be edited directly to model different scenarios.
- **Closable roads** are defined in the `closable_roads` dictionary in `main.py`, each with a list of node-pair edges and a display label.
- **The road network itself** comes from `doha_graph.graphml`. To use a different city, this file would need to be replaced with an OSMnx-exported graph for that city, and the depot/need coordinates updated accordingly.

## References and Attribution

- **OSMnx** -> Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*.
- **NetworkX** -> used both as the underlying graph library for OSMnx and as a verification reference for the custom Dijkstra implementation.
- **Folium** -> used for map rendering, built on Leaflet.js.
- **OpenStreetMap** -> underlying map tile and road data source, via OSMnx.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.