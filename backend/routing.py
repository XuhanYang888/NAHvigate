import os
import random
import json
import osmnx as ox
import networkx as nx

GRAPH_FILENAME = "toronto_v2.graphml"
PLACE_NAME = "Toronto, Ontario, Canada"

G = None


def load_graph():
    global G
    if os.path.exists(GRAPH_FILENAME):
        print(f"Loading graph from {GRAPH_FILENAME}...")
        G = ox.load_graphml(GRAPH_FILENAME)
    else:
        print(
            f"Downloading road network for {PLACE_NAME}... this takes a minute.")
        G = ox.graph_from_place(PLACE_NAME, network_type="drive")

        fallback_speeds = {
            "motorway": 100,
            "motorway_link": 80,
            "trunk": 80,
            "trunk_link": 60,
            "primary": 60,
            "primary_link": 50,
            "secondary": 50,
            "secondary_link": 40,
            "tertiary": 40,
            "tertiary_link": 30,
            "residential": 30,
            "unclassified": 30
        }

        print("Calculating realistic speed limits and travel times...")
        G = ox.add_edge_speeds(G, hwy_speeds=fallback_speeds, fallback=30)
        G = ox.add_edge_travel_times(G)

        for u, v, k, data in G.edges(keys=True, data=True):
            if isinstance(data.get('highway'), list):
                data['highway'] = data['highway'][0]
            if isinstance(data.get('bridge'), list):
                data['bridge'] = data['bridge'][0]

        ox.save_graphml(G, GRAPH_FILENAME)
        print("Graph downloaded and saved successfully!")
    return G


def get_boundary():
    gdf = ox.geocode_to_gdf(PLACE_NAME)
    return json.loads(gdf.to_json())


def calculate_route_stats(path_nodes):
    global G
    distance = 0.0
    travel_time = 0.0
    bridges = 0

    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i+1]

        edge_data = min(G[u][v].values(), key=lambda x: float(
            x.get('travel_time', x.get('length', 1.0))))

        distance += float(edge_data.get('length', 1.0))
        travel_time += float(edge_data.get('travel_time', distance / 10.0))

        if edge_data.get('bridge') == 'yes':
            bridges += 1

    return {
        "distance_km": round(distance / 1000, 2),
        "time_mins": round(travel_time / 60),
        "bridges": bridges
    }


def get_routes(req):
    global G
    if G is None:
        load_graph()

    orig_node = ox.distance.nearest_nodes(G, X=req.start_lon, Y=req.start_lat)
    dest_node = ox.distance.nearest_nodes(G, X=req.end_lon, Y=req.end_lat)

    routes = {
        "normal": [], "nah": [],
        "normal_stats": {}, "nah_stats": {}
    }

    def safe_float(val, default=1.0):
        try:
            return float(val)
        except:
            return default

    def normal_weight(u, v, d):
        return safe_float(d.get('travel_time', 10.0))

    try:
        normal_nodes = nx.shortest_path(
            G, orig_node, dest_node, weight=normal_weight)
        routes["normal"] = [[G.nodes[n]['y'], G.nodes[n]['x']]
                            for n in normal_nodes]
        routes["normal_stats"] = calculate_route_stats(normal_nodes)

        if req.chaos == 0 and req.avoid_highways == 0 and req.love_bridges == 0:
            routes["nah"] = routes["normal"]
            routes["nah_stats"] = routes["normal_stats"]
            return routes

    except nx.NetworkXNoPath:
        return routes

    def nah_cost_function(u, v, d):
        tt = safe_float(d.get('travel_time', 10.0))
        highway = d.get('highway', '')
        bridge = d.get('bridge', 'no')

        cost = tt

        if req.avoid_highways > 0:
            if highway in ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary']:
                cost *= (1.0 + (req.avoid_highways / 2.0))

        if req.love_bridges > 0:
            if bridge == 'yes':
                cost *= 0.05
            else:
                cost *= (1.0 + (req.love_bridges / 5.0))

        if req.chaos > 0:
            cost *= random.uniform(1.0, 1.0 + (req.chaos / 10.0))

        return max(cost, 0.001)

    try:
        nah_nodes = nx.shortest_path(
            G, orig_node, dest_node, weight=nah_cost_function)
        routes["nah"] = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in nah_nodes]
        routes["nah_stats"] = calculate_route_stats(nah_nodes)
    except nx.NetworkXNoPath:
        pass

    return routes
