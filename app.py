from flask import Flask, render_template, request, redirect, url_for
from main import (
    depots, needs, depots_supply, needs_demand,
    build_flow_network, all_distances, min_cost_max_flow,
    build_map, extract_flow_per_pair
)
import folium 

app = Flask(__name__)

active_depots = {name: True for name in depots}
active_needs = {name: True for name in needs}

@app.route('/')
def index():
    filtered_supply = {k: v for k, v in depots_supply.items() if active_depots[k]}
    filtered_demand = {k: v for k, v in needs_demand.items() if active_needs[k]}
    
    graph = build_flow_network(depots, needs, filtered_supply, filtered_demand, all_distances)
    flow, cost = min_cost_max_flow(graph, "S", "T")
    flow_result = extract_flow_per_pair(graph, depots, needs)

    folium_map = build_map(flow_result, active_depots, active_needs, depots, needs)
    return render_template("index.html", map_html=folium_map.get_root().render())

@app.route('/toggle', methods=['POST'])
def toggle():
    node_id = request.form.get("node_id") # e.g "Aster Hospital"
    node_type = request.form.get("node_type") # e.g "depot"
    if node_type == "depot":
        active_depots[node_id] = not active_depots[node_id]
    else:
        active_needs[node_id] = not active_needs[node_id]
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)