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

    return G


def get_boundary():
    gdf = ox.geocode_to_gdf(PLACE_NAME)
    geojson_data = json.loads(gdf.to_json())
    return geojson_data


def get_routes(req):
    global G
    if G is None:
        load_graph()

    orig_node = ox.distance.nearest_nodes(G, X=req.start_lon, Y=req.start_lat)
    dest_node = ox.distance.nearest_nodes(G, X=req.end_lon, Y=req.end_lat)

    routes = {"normal": [], "nah": []}

    try:
        normal_nodes = nx.shortest_path(
            G, orig_node, dest_node, weight="length")
        routes["normal"] = [[G.nodes[n]['y'], G.nodes[n]['x']]
                            for n in normal_nodes]
    except nx.NetworkXNoPath:
        return routes

    def nah_cost_function(u, v, d):
        cost = d.get('length', 1.0)

        highway = d.get('highway', '')
        junction = d.get('junction', '')

        if isinstance(highway, list):
            highway = highway[0]
        if isinstance(junction, list):
            junction = junction[0]

        if req.avoid_highways > 0:
            if highway in ['motorway', 'motorway_link', 'trunk', 'trunk_link']:
                cost += cost * req.avoid_highways

        if req.love_roundabouts > 0:
            if junction == 'roundabout':
                cost = cost / (req.love_roundabouts * 2)
            else:
                cost += (req.love_roundabouts * 2)

        if req.chaos > 0:
            chaos_multiplier = 1.0 + (req.chaos / 10.0)
            cost *= random.uniform(1.0, chaos_multiplier)

        return max(cost, 0.1)

    try:
        nah_nodes = nx.shortest_path(
            G, orig_node, dest_node, weight=nah_cost_function)
        routes["nah"] = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in nah_nodes]
    except nx.NetworkXNoPath:
        pass

    return routes
