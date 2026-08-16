import osmnx as ox
import folium
from queue import PriorityQueue

DEBUG = False  # flip to True for MCMF tracing

G = ox.load_graphml("doha_graph.graphml")
nodes, edges = ox.graph_to_gdfs(G)

depots = {
    "Aster Hospital": (25.2585615, 51.5557181),
    "Al-Ahli Hospital": (25.3075536, 51.4996276),
    "HAMAD SUPPLY CHAIN MANAGEMENT": (25.295206, 51.5026573),
}

needs = {
    "Al Sadd": (25.2704, 51.5228),
    "New Doha Complex (Al Sadd area)": (25.2786312, 51.533198),
    "Ezdan C3 (Al Rayyan)": (25.2877821, 51.5177418),
    "Msheireb": (25.2867, 51.5333),
    "Awqaf housing complex": (25.2960399, 51.4994293),
}

depots_supply = {
    "Aster Hospital": 500,
    "Al-Ahli Hospital": 400,
    "HAMAD SUPPLY CHAIN MANAGEMENT": 700,
}

needs_demand = {
    "Al Sadd": 300,
    "New Doha Complex (Al Sadd area)": 250,
    "Ezdan C3 (Al Rayyan)": 350,
    "Msheireb": 200,
    "Awqaf housing complex": 300,
}

closable_roads = {
    "al_rayyan": {
        "edges": [(4823743493, 12247715582), (12247715582, 12247715668)],
        "label": "Al Rayyan Road (طريق الريان)"
    },
    "al_hurriya": {
        "edges": [(1526472865, 5871569482), (5871569482, 5871569691)],
        "label": "Al Hurriya Street (الحرية)"
    },
    "al_salah": {
        "edges": [(5871569691, 6166133928)],
        "label": "Al Salah Street (الصلاح)"
    },
}

def build_closed_edges_set(closed_roads, closable_roads):
    closed = set()
    for road_id, is_closed in closed_roads.items():
        if is_closed:
            for u, v in closable_roads[road_id]["edges"]:
                closed.add((u, v))
                closed.add((v, u))
    return closed

depots_nodes = {
    name: ox.nearest_nodes(G, lon, lat)
    for name, (lat, lon) in depots.items()
}

needs_nodes = {
    name: ox.nearest_nodes(G, lon, lat)
    for name, (lat, lon) in needs.items()
}

def recompute_all_paths(closed_edges):
    paths = {}
    distances = {}
    for depot_name, depot_node in depots_nodes.items():
        for need_name, need_node in needs_nodes.items():
            path, distance = dijkstra(G, depot_node, need_node, closed_edges)
            key = f"{depot_name} to {need_name}"
            paths[key] = path
            distances[key] = distance
    return paths, distances


def dijkstra(graph, start_node, end_node, closed_edges =None):
    if closed_edges is None:
        closed_edges = set()

    visited = set()
    distances = {node: float('inf') for node in graph.nodes}
    distances[start_node] = 0
    queue = PriorityQueue()
    queue.put((0, start_node))
    previous = {}

    while not queue.empty():
        current_distance, current_node = queue.get()
        if current_node in visited:
            continue

        visited.add(current_node)

        if current_node == end_node:
            break

        for neighbor, edge_data in graph[current_node].items():
            if (current_node, neighbor) in closed_edges:
                continue
            min_length = min(edge_data.values(), key=lambda x: x['length'])['length']
            tentative_distance = current_distance + min_length

            if tentative_distance < distances[neighbor]:
                distances[neighbor] = tentative_distance
                queue.put((tentative_distance, neighbor))
                previous[neighbor] = current_node

    path = []
    current = end_node
    while current is not None:
        path.append(current)
        current = previous.get(current, None)

    path.reverse()

    return path, distances[end_node]


class Edge:
    def __init__(self, to, capacity, cost):
        self.to = to
        self.capacity = capacity
        self.cost = cost
        self.flow = 0
        self.reverse = None


def add_edge(graph, from_node, to_node, capacity, cost):
    forward = Edge(to=to_node, capacity=capacity, cost=cost)
    backward = Edge(to=from_node, capacity=0, cost=-cost)

    forward.reverse = backward
    backward.reverse = forward
    graph[from_node].append(forward)
    graph[to_node].append(backward)


def bellman_ford(graph, source, sink):
    distance = {node: float('inf') for node in graph}
    parent = {node: None for node in graph}
    distance[source] = 0

    for _ in range(len(graph) - 1):
        new_distance = distance.copy()
        new_parent = parent.copy()

        for u in graph:
            if distance[u] == float('inf'):
                continue

            for edge in graph[u]:
                if edge.capacity > 0:
                    new_distance_value = distance[u] + edge.cost

                    if new_distance_value < new_distance[edge.to] - 1e-9:
                        new_distance[edge.to] = new_distance_value
                        new_parent[edge.to] = edge

        if new_distance == distance:
            break

        distance = new_distance
        parent = new_parent

    return distance, parent


def min_cost_max_flow(graph, source, sink):
    flow = 0
    cost = 0

    while True:
        distance, parent = bellman_ford(graph, source, sink)

        if distance[sink] == float('inf'):
            break

        # Find bottleneck
        bottleneck = float('inf')
        node = sink
        visited = set()

        while node != source:
            if node in visited:
                if DEBUG:
                    print("ERROR: parent cycle detected at", node)
                break

            visited.add(node)

            edge = parent[node]
            if DEBUG:
                print("walking:", node, "via", edge.reverse.to)

            bottleneck = min(bottleneck, edge.capacity)
            node = edge.reverse.to

        # Send flow
        node = sink
        while node != source:
            edge = parent[node]

            edge.capacity -= bottleneck
            edge.reverse.capacity += bottleneck

            node = edge.reverse.to

        flow += bottleneck
        cost += bottleneck * distance[sink]

    return flow, cost

def extract_flow_per_pair(graph, depots, needs):
    """
    After min_cost_max_flow runs, reverse_edge.capacity == flow currently
    pushed on the matching forward edge (standard residual-graph property).
    """
    flow_per_pair = {}
    for depot_name in depots:
        for edge in graph[depot_name]:
            if edge.to in needs:  # forward depot->need edge, not the S-reverse edge
                flow_per_pair[(depot_name, edge.to)] = edge.reverse.capacity
    return flow_per_pair


def build_flow_network(depots, needs, depots_supply, needs_demand, all_distances):
    graph = {}
    for depot in depots:
        graph[depot] = []
    for need in needs:
        graph[need] = []
    graph["S"] = []
    graph["T"] = []

    for depot, supply in depots_supply.items():
        add_edge(graph, "S", depot, capacity=supply, cost=0)

    for need, demand in needs_demand.items():
        add_edge(graph, need, "T", capacity=demand, cost=0)

    for depot_name, depot_node in depots_nodes.items():
        for need_name, _ in needs_demand.items():
            key = f"{depot_name} to {need_name}"
            cost = all_distances[key]
            add_edge(graph, depot_name, need_name, capacity=float('inf'), cost=cost)

    return graph


# ── Run Dijkstra for every depot→need pair (cached) ──────────
all_paths = {}
all_distances = {}

for depot_name, depot_node in depots_nodes.items():
    for need_name, need_node in needs_nodes.items():
        path, distance = dijkstra(G, depot_node, need_node)
        key = f"{depot_name} to {need_name}"
        all_paths[key] = path
        all_distances[key] = distance


# ── Example single-route visualization ────────────────────────
start_node = depots_nodes["Aster Hospital"]
end_node = needs_nodes["Al Sadd"]
example_path, example_distance = dijkstra(G, start_node, end_node)
route_coords = [
    (G.nodes[node]["y"], G.nodes[node]["x"])
    for node in example_path
]

def build_map(flow_result, active_depots, active_needs, depots, needs, paths):
    m = folium.Map(location=[25.2854, 51.5310], zoom_start=12)

    # background road network (once, static)
    # for _, row in edges.iterrows():
    #     coords = [(lat, lon) for lon, lat in row["geometry"].coords]
    #     folium.PolyLine(coords, color="blue", weight=1, opacity=0.3).add_to(m)

    # depot markers  colored if active, greyed if not
    for name, (lat, lon) in depots.items():
        color = "green" if active_depots[name] else "gray"
        popup_html = f"""
        <b>{name}</b><br>
        Supply: {depots_supply[name]}<br>
        <form action="/toggle" method="post">
            <input type="hidden" name="node_id" value="{name}">
            <input type="hidden" name="node_type" value="depot">
            <button type="submit">{'Deactivate' if active_depots[name] else 'Activate'}</button>
        </form>
        """
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=color)
        ).add_to(m)

    # need markers  same active/inactive pattern
    for name, (lat, lon) in needs.items():
        color = "red" if active_needs[name] else "gray"
        popup_html = f"""
        <b>{name}</b><br>
        Demand: {needs_demand[name]}<br>
        <form action="/toggle" method="post">
            <input type="hidden" name="node_id" value="{name}">
            <input type="hidden" name="node_type" value="need">
            <button type="submit">{'Deactivate' if active_needs[name] else 'Activate'}</button>
        </form>
        """
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=color)
        ).add_to(m)
    # flow lines one PolyLine per depot-need pair that actually has flow
    for (depot_name, need_name), flow_amount in flow_result.items():
        if flow_amount > 0:
            route_coords = [
                (G.nodes[node]["y"], G.nodes[node]["x"])
                for node in paths[f"{depot_name} to {need_name}"]
            ]
            folium.PolyLine(
                route_coords,
                color="darkred",
                weight=max(1, flow_amount / 50),  # thicker line = more flow
                opacity=0.8
            ).add_to(m)

    return m
from collections import Counter

# find the edge row matching a given (u, v) pair and grab its name
def get_road_name(edges, u, v):
    match = edges[(edges.index.get_level_values(0) == u) & (edges.index.get_level_values(1) == v)]
    if not match.empty and 'name' in match.columns:
        name = match.iloc[0]['name']
        return name if isinstance(name, str) else "Unnamed road"
    return "Unnamed road"
edges_to_check = [
    (4823743493, 12247715582),
    (12247715582, 12247715668),
    (1526472865, 5871569482),
    (5871569482, 5871569691),
    (5871569691, 6166133928),
]

for u, v in edges_to_check:
    print(u, v, "->", get_road_name(edges, u, v))
if __name__ == "__main__":
    graph = build_flow_network(depots, needs, depots_supply, needs_demand, all_distances)
    flow, cost = min_cost_max_flow(graph, "S", "T")
    print(f"MCMF result — flow: {flow}, cost: {cost}")

    # verification test (Day 7) — confirmed working, road closures correctly
    # reroute affected depot-need pairs. Left commented for reference.
    # test_closed = build_closed_edges_set(
    #     {"al_rayyan": True, "al_hurriya": False, "al_salah": False},
    #     closable_roads
    # )
    # new_paths, new_distances = recompute_all_paths(test_closed)
    # for key in all_distances:
    #     before = all_distances[key]
    #     after = new_distances[key]
    #     if abs(before - after) > 1:
    #         print(f"{key}: {before:.1f}m -> {after:.1f}m (CHANGED)")
    #     else:
    #         print(f"{key}: unchanged")