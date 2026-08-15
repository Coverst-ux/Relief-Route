import osmnx as ox
import folium
from queue import PriorityQueue

# Load the graph
G = ox.load_graphml("doha_graph.graphml")
nodes, edges = ox.graph_to_gdfs(G)

# Define depots and need points
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

# Get nearest nodes for depots and need points
depots_nodes = {
    name: ox.nearest_nodes(G, lon, lat)
    for name, (lat, lon) in depots.items()
}

needs_nodes = {
    name: ox.nearest_nodes(G, lon, lat)
    for name, (lat, lon) in needs.items()
}

def dijkstra(graph, start_node, end_node):
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
            # Find the edge with the shortest length
            min_length = min(edge_data.values(),key=lambda x: x['length'])['length']
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

# Example usage
start_node = depots_nodes["Aster Hospital"]
end_node = needs_nodes["Al Sadd"]

path, distance = dijkstra(G, start_node, end_node)
route_coords = [
    (G.nodes[node]["y"], G.nodes[node]["x"])
    for node in path
]
print(f"Shortest path from {start_node} to {end_node}: {route_coords}")
print(f"Total distance: {distance} meters")


m = folium.Map(
    location=[25.2854, 51.5310],
    zoom_start=12
)

for _, row in edges.iterrows():
    coords = [(lat, lon) for lon, lat in row["geometry"].coords]

    folium.PolyLine(
        coords,
        color="blue",
        weight=1,
        opacity=0.5
    ).add_to(m)

folium.PolyLine(
    route_coords,
    color="red",
    weight=5,
    opacity=1
).add_to(m)

folium.Marker(
    route_coords[0],
    popup="Aster Hospital"
).add_to(m)

folium.Marker(
    route_coords[-1],
    popup="Al Sadd"
).add_to(m)


all_paths = {}
all_distances = {}

for depot_name, depot_node in depots_nodes.items():
    for need_name, need_node in needs_nodes.items():
        path, distance = dijkstra(G, depot_node, need_node)
        
        key = f"{depot_name} to {need_name}"
        all_paths[key] = path
        all_distances[key] = distance

for key in all_paths:
    print(f"Route from {key}:")
    print(f"  Distance: {all_distances[key]} meters")
    
    
class Edge:
    def __init__(self, to, capacity, cost):
        self.to = to
        self.capacity = capacity
        self.cost = cost
        self.flow = 0
        self.reverse = None  
        
def add_edge(graph, from_node, to_node, capacity, cost):
    forward = Edge(to = to_node, capacity= capacity, cost = cost)
    backward = Edge(to=from_node, capacity=0, cost=-cost)
    
    forward.reverse = backward
    backward.reverse = forward
    graph[from_node].append(forward)
    graph[to_node].append(backward)
    

def build_flow_network(depots, needs, depots_supply, needs_demand, all_distances):
    graph = {}
    for depot in depots:
        graph[depot] = []
    for need in needs:
        graph[need] = []
    graph["S"] = []
    graph["T"] = []
    
    for depot, supply in depots_supply.items():
        add_edge(graph, "S", depot, capacity = supply, cost = 0)
        
    for need, demand in needs_demand.items():
        add_edge(graph, need, "T", capacity = demand, cost = 0)
        
    for depot_name, depot_node in depots_nodes.items():
        for need_name, _ in needs_demand.items():
            key = f"{depot_name} to {need_name}"
            cost = all_distances[key]
            add_edge(graph, depot_name, need_name, capacity = float('inf'), cost = cost)

    return graph

graph = build_flow_network(depots, needs, depots_supply, needs_demand, all_distances)
# adjust arguments to match however you actually defined the function signature

print("S edges:")
for e in graph["S"]:
    print(f"  to={e.to}, capacity={e.capacity}, cost={e.cost}")

print("\nAster Hospital edges:")
for e in graph["Aster Hospital"]:
    print(f"  to={e.to}, capacity={e.capacity}, cost={e.cost}")

print("\nAl Sadd edges:")
for e in graph["Al Sadd"]:
    print(f"  to={e.to}, capacity={e.capacity}, cost={e.cost}")
m.save("doha_map.html")