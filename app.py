from flask import Flask, render_template, request, redirect, url_for
from main import (
    depots, needs, depots_supply, needs_demand,
    build_flow_network, all_distances, min_cost_max_flow,
    build_map, extract_flow_per_pair, build_closed_edges_set,
    closable_roads, recompute_all_paths,
     all_paths
)

app = Flask(__name__)

active_depots = {name: True for name in depots}
active_needs = {name: True for name in needs}
closed_roads = {road_id: False for road_id in closable_roads}   

@app.route('/')
def index():
    filtered_supply = {k: v for k, v in depots_supply.items() if active_depots[k]}
    filtered_demand = {k: v for k, v in needs_demand.items() if active_needs[k]}
    
    closed_edges = build_closed_edges_set(closed_roads, closable_roads)
    if closed_edges:
        current_paths, current_distances = recompute_all_paths(closed_edges)
    else:
        current_paths, current_distances = all_paths, all_distances
        
    graph = build_flow_network(depots, needs, filtered_supply, filtered_demand, current_distances)  
    flow, cost = min_cost_max_flow(graph, "S", "T")
    flow_result = extract_flow_per_pair(graph, depots, needs)

    folium_map = build_map(flow_result, active_depots, active_needs, depots, needs, current_paths, closed_roads)
    return render_template("index.html", map_html=folium_map.get_root().render(), closable_roads=closable_roads, closed_roads=closed_roads, active_depots=active_depots, flow=flow, cost=cost)

@app.route('/toggle', methods=['POST'])
def toggle():
    node_id = request.form.get("node_id") # e.g "Aster Hospital"
    node_type = request.form.get("node_type") # e.g "depot"
    if node_type == "depot":
        active_depots[node_id] = not active_depots[node_id]
    else:
        active_needs[node_id] = not active_needs[node_id]
    return redirect(url_for('index'))


@app.route('/update_roads', methods=['POST'])
def update_roads():
    checked_ids = request.form.getlist("closed")
    for road_id in closable_roads:
        closed_roads[road_id] = road_id in checked_ids
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)