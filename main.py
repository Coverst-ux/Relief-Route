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

m.save("doha_map.html")
print("Map saved.")