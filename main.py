import osmnx as ox
import folium

place_name = "Doha, Qatar"

G = ox.graph_from_place(place_name, network_type="drive")

print(f"node: {len(G.nodes)}")
print(f"edges: {len(G.edges)}")


nodes, edges = ox.graph_to_gdfs(G)

m = folium.Map(location=[25.2854, 51.5310], zoom_start=12)

for _, row in edges.iterrows():
    coords = [(lat, lon) for lon, lat in row['geometry'].coords]
    folium.PolyLine(coords, color="blue", weight=1, opacity=0.5).add_to(m)


depots = {
    "Hamad General Hospital": (25.2867, 51.5157),
    "Doha Industrial Area": (25.1631, 51.4644),
    "West Bay": (25.3260, 51.5310),
}

need_points = {
    "Al Sadd": (25.2704, 51.5228),
    "Al Rayyan": (25.2919, 51.4241),
    "Al Waab": (25.2447, 51.4622),
    "Msheireb": (25.2867, 51.5333),
    "Al Wakrah": (25.1656, 51.6033),
}


depot_nodes = {name: ox.nearest_nodes(G, lon, lat) for name, (lat, lon) in depots.items()}
need_nodes = {name: ox.nearest_nodes(G, lon, lat) for name, (lat, lon) in need_points.items()}

print(depot_nodes)
print(need_nodes)
m.save("doha_map.html")
print("Map saved.")