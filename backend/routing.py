import os
import random
import osmnx as ox
import networkx as nx
import json

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

    # chaotic weights js for testing
    for u, v, k, data in G.edges(keys=True, data=True):
        physical_length = data.get('length', 1.0)
        data['chaos_weight'] = physical_length * random.uniform(1.0, 20.0)

    return G


def get_boundary():
    gdf = ox.geocode_to_gdf(PLACE_NAME)
    geojson_data = json.loads(gdf.to_json())
    return geojson_data


def get_routes(start_lat, start_lon, end_lat, end_lon):
    global G
    if G is None:
        load_graph()

    orig_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    dest_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

    routes = {"normal": [], "nah": []}

    try:
        normal_nodes = nx.shortest_path(
            G, orig_node, dest_node, weight="length")
        routes["normal"] = [[G.nodes[n]['y'], G.nodes[n]['x']]
                            for n in normal_nodes]

        nah_nodes = nx.shortest_path(
            G, orig_node, dest_node, weight="chaos_weight")
        routes["nah"] = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in nah_nodes]

    except nx.NetworkXNoPath:
        pass

    return routes
