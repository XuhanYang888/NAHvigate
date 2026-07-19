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
        print(f"Downloading road network... this takes a minute.")
        G = ox.graph_from_place(PLACE_NAME, network_type="drive")

        print("Calculating speed limits and travel times...")
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)

        ox.save_graphml(G, GRAPH_FILENAME)
        print("Graph downloaded and saved!")
    return G


def get_boundary():
    gdf = ox.geocode_to_gdf(PLACE_NAME)
    return json.loads(gdf.to_json())


def calculate_route_stats(path_nodes):
    global G
    distance = 0
    travel_time = 0
    bridges = 0

    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i+1]

        edge_data = min(G[u][v].values(), key=lambda x: float(
            x.get('travel_time', x.get('length', 1.0))))

        distance += float(edge_data.get('length', 1.0))
        travel_time += float(edge_data.get('travel_time', distance / 10.0))

        bridge = edge_data.get('bridge', '')
        if isinstance(bridge, list):
            bridge = bridge[0]
        if bridge == 'yes':
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

    def get_travel_time(u, v, d):
        return float(d.get('travel_time', d.get('length', 1.0)))

    try:
        normal_nodes = nx.shortest_path(
            G, orig_node, dest_node, weight=get_travel_time)
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
        cost = float(d.get('travel_time', d.get('length', 1.0)))
        highway = d.get('highway', '')
        bridge = d.get('bridge', '')

        if isinstance(highway, list):
            highway = highway[0]
        if isinstance(bridge, list):
            bridge = bridge[0]

        if req.avoid_highways > 0:
            if highway in ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary']:
                cost *= (1 + req.avoid_highways)

        if req.love_bridges > 0:
            if bridge == 'yes':
                cost /= (1 + (req.love_bridges / 5))
            else:
                cost *= (1 + (req.love_bridges / 20))

        if req.chaos > 0:
            chaos_multiplier = 1.0 + (req.chaos / 10.0)
            cost *= random.uniform(1.0, chaos_multiplier)

        return max(cost, 0.1)

    try:
        nah_nodes = nx.shortest_path(
            G, orig_node, dest_node, weight=nah_cost_function)
        routes["nah"] = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in nah_nodes]
        routes["nah_stats"] = calculate_route_stats(nah_nodes)
    except nx.NetworkXNoPath:
        pass

    return routes
