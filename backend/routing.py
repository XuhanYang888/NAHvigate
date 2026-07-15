import os
import osmnx as ox
import networkx as nx

GRAPH_FILENAME = "toronto.graphml"
PLACE_NAME = "Toronto, Ontario, Canada"

G = None


def load_graph():
    global G
    if os.path.exists(GRAPH_FILENAME):
        print(f"Loading graph from {GRAPH_FILENAME}...")
        G = ox.load_graphml(GRAPH_FILENAME)
    else:
        print(
            f"Downloading road network for {PLACE_NAME}... (This takes a minute)")
        G = ox.graph_from_place(PLACE_NAME, network_type="drive")
        ox.save_graphml(G, GRAPH_FILENAME)
        print("Graph downloaded and saved!")
    return G


def get_shortest_path(start_lat, start_lon, end_lat, end_lon):
    global G
    if G is None:
        load_graph()

    orig_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    dest_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

    try:
        route_nodes = nx.shortest_path(
            G, orig_node, dest_node, weight="length")
    except nx.NetworkXNoPath:
        return []

    route_coords = []
    for node in route_nodes:
        lat = G.nodes[node]['y']
        lon = G.nodes[node]['x']
        route_coords.append([lat, lon])

    return route_coords
