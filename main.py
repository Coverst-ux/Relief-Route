import osmnx as ox


place_name = "Doha, Qatar"

G = ox.graph_from_place(place_name, network_type="drive")

print(f"node: {len(G.nodes)}")
print(f"edges: {len(G.edges)}")

ox.save_graphml(G, "doha_graph.graphml")