import itertools
from collections import deque
from itertools import permutations
from random import choice

from igraph import *

from my_utils import RGBtoHex


class path_info:
    def __init__(self, way, length_of_way, satisfied_goal):
        self.way = way
        self.length_of_way = length_of_way
        self.satisfied_goal = satisfied_goal


class graph_actions():
    # Goal point has a "start" node and all other goal points saved as a dictionary
    def __init__(self, graph, goal_points):
        self.graph = graph
        self.goal_points = goal_points
        self.best_path = list()

    def calculate_best_path(self):
        self.best_path = scatter(self.graph, self.goal_points)

        if self.best_path is None:
            return None

        # while not queued_best_path.empty():
        #     self.best_path.append(queued_best_path.get())

        return self.best_path


def scatter(graph, goal_points):
    transetive_close_graph = transetive_close(deepcopy(goal_points), graph)

    if len(transetive_close_graph.es) == 0:
        final_best_path = find_best_way(goal_points, graph)
        if final_best_path is None:
            return None
        full_name_short_path = list()
        for vertex in final_best_path[0]:
            full_name_short_path.append(graph.vs.find(vertex)["name"])

        return (full_name_short_path, ([graph.vs.find(final_best_path[1])["name"]], 0, tuple([0])))

    return find_best_way2(deepcopy(goal_points), transetive_close_graph, graph)


def dict_tranpose(vertex_dict):
    inv_map = {}
    for k, v in vertex_dict.iteritems():
        inv_map[v] = inv_map.get(v, [])
        inv_map[v].append(k)
    return inv_map


def color_subgoals(graph, vertex_dict):
    inv_map = dict_tranpose(vertex_dict)
    for key in inv_map:
        vertex_color = known_colors[choice(known_colors.keys())]
        for iter in inv_map[key]:
            graph.vs.find(str(iter).encode('ascii', 'replace'))["Fill Color"] = RGBtoHex(vertex_color)


def transetive_close(goal_points, graph):
    starting_point = goal_points["start"]
    del goal_points["start"]

    # Color vertex
    color_subgoals(graph, goal_points)

    small_graph = Graph(directed=True)
    for vertex in goal_points:
        v = small_graph.add_vertex(name=vertex)
        v["Fill Color"] = graph.vs.find(vertex)["Fill Color"]

    for vertex in goal_points:
        all_shortest_path_lengths = graph.shortest_paths(vertex)[0]
        for target in goal_points:
            if target != vertex:
                path_length = all_shortest_path_lengths[graph.vs.find(target).index]
                if path_length == float("inf") or path_length == 0:
                    continue
                edge = small_graph.add_edge(vertex, target)
                edge["weight"] = path_length
    # DEBUG
    small_graph.save("small_graph_close.graphml", "graphml")
    return small_graph


def total_weight(vertex_list, base_graph):
    count_weight = 0
    for i in range(len(vertex_list) - 1):  # -2
        edge_id = base_graph.get_eid(vertex_list[i], vertex_list[i + 1])
        edge = base_graph.es.find(edge_id)
        count_weight += edge["weight"]
    return count_weight


def add_vertex_to_graph(graph, name_of_vertex):
    try:
        return graph.vs.find(name=name_of_vertex)
    except:
        return graph.add_vertex(name_of_vertex)


def weights_from_start_point_to_goal(starting_point, goal_points, org_graph):
    start_to_goal_dict = dict()
    for goal_point in goal_points:
        start_to_goal_dict[goal_point] = org_graph.shortest_paths(starting_point, goal_point)[0][0]
    return start_to_goal_dict


def is_valid_permutation(connectivety_dict, permutation):
    for key in connectivety_dict.keys():
        for value in connectivety_dict[key]:
            if permutation.index(key) + 1 == permutation.index(value):
                return False
    return True


def options_for_permutation(graph, num_of_groups, roots, goal_points):
    all_options = dict()
    vertex_level = roots.indices
    for i in range(0, num_of_groups):
        next_level = set()
        for vertex in vertex_level:
            next_level = next_level.union(set(graph.neighbors(vertex, mode=OUT)))
        all_options[i] = vertex_level
        vertex_level = next_level
    ret = dict()
    for i in range(len(all_options)):
        ret[i] = set()
        for vertex in all_options[i]:
            ret[i] = ret[i].union({goal_points[graph.vs[vertex]["name"]]})

    return ret


class iterhelp(object):
    def __init__(self):
        self.length = 0

    def __len__(self):
        return self.length

    def product(self, *args, **kwds):
        pools = map(tuple, args) * kwds.get('repeat', 1)
        result = [[]]
        for pool in pools:
            result = [x + [y] for x in result for y in pool if x.count(y) == 0]
        self.length = len(result)
        for prod in result:
            yield tuple(prod)


def find_best_way2(goal_points, transetive_graph, org_graph):
    starting_point = goal_points["start"]
    del goal_points["start"]
    groups_of_subgoals = dict_tranpose(goal_points)
    best_path = None

    if len(groups_of_subgoals) == 0:
        # No sub-goal was achieved
        return None

    start_to_goal_dict = weights_from_start_point_to_goal(starting_point, goal_points, org_graph)

    biggest_cluster = 0
    components = transetive_graph.components(mode=WEAK)
    components_to_delete = list()
    for cluster in components:
        biggest_cluster = max(len(cluster), biggest_cluster)
        if len(cluster) < len(groups_of_subgoals):
            components_to_delete += cluster
    transetive_graph.delete_vertices(components_to_delete)

    root_groups = set()
    leaf_groups = set()
    if biggest_cluster == len(groups_of_subgoals):
        roots = transetive_graph.vs.select(_indegree_eq=0)
        for root in roots:
            root_groups.add(goal_points[root["name"]])
        leafs = transetive_graph.vs.select(_outdegree_eq=0)
        for leaf in leafs:
            # check_group = goal_points[leaf["name"]]
            # for vertex in groups_of_subgoals[check_group]:
            # Only if all of the vertexes of this group are leafs- this gruop must be the last
            # try: if transetive_graph.vs.find(vertex).index not in leafs.indices: break
            leaf_groups.add(goal_points[leaf["name"]])
    else:
        roots = transetive_graph.vs
    if len(root_groups) == 0:
        root_groups = root_groups.union(set(groups_of_subgoals.keys()))
    if len(leaf_groups) == 0:
        leaf_groups = leaf_groups.union(set(groups_of_subgoals.keys()))

    connectivety_dict = dict()
    for edge in transetive_graph.es:
        # Checking if this edge answers to this permutation
        source = goal_points[edge.source_vertex["name"]]
        target = goal_points[edge.target_vertex["name"]]
        if connectivety_dict.has_key(source):
            connectivety_dict[source].add(target)
        else:
            connectivety_dict[source] = {target}

    # neighboring_groups = deepcopy(connectivety_dict)

    for the_set in connectivety_dict.keys():
        connectivety_dict[the_set] = set(groups_of_subgoals.keys()) - connectivety_dict[the_set]
    for key in connectivety_dict.keys():
        if len(connectivety_dict[key]) <= 1:
            del connectivety_dict[key]

    all_options_for_permutation = options_for_permutation(transetive_graph, len(groups_of_subgoals), roots, goal_points)

    num_of_permutations_done = 0.0
    # for permutation in permutations(groups_of_subgoals.keys()):
    len_of_result = []
    iterhelp_instance = iterhelp()
    for permutation in iterhelp_instance.product(*all_options_for_permutation.values()):

        num_of_permutations_done += 1
        if num_of_permutations_done % 1000 == 0:
            print "calculating bread crumbs: %" + str(
                num_of_permutations_done / len(iterhelp_instance) * 100)

            if not is_valid_permutation(connectivety_dict, permutation):
                continue

        base_graph = Graph(directed=True)

        for edge in transetive_graph.es:
            # Checking if this edge answers to this permutation
            source = goal_points[edge.source_vertex["name"]]
            target = goal_points[edge.target_vertex["name"]]
            if permutation.index(source) + 1 == permutation.index(target):
                vertex = add_vertex_to_graph(base_graph, edge.source_vertex["name"])
                vertex["Fill Color"] = edge.source_vertex["Fill Color"]
                vertex = add_vertex_to_graph(base_graph, edge.target_vertex["name"])
                vertex["Fill Color"] = edge.target_vertex["Fill Color"]
                new_edge = base_graph.add_edge(edge.source_vertex["name"], edge.target_vertex["name"])
                new_edge["weight"] = edge["weight"]

        # Add the start and sink point
        start = base_graph.add_vertex(starting_point)
        for vertex in groups_of_subgoals[permutation[0]]:
            try:
                base_graph.vs.find(vertex)
                edge = base_graph.add_edge(start["name"], vertex)
                edge["weight"] = start_to_goal_dict[vertex]
            except:
                0
        sink = base_graph.add_vertex("sink")
        for vertex in groups_of_subgoals[permutation[len(permutation) - 1]]:
            try:
                base_graph.vs.find(vertex)
                edge = base_graph.add_edge(vertex, sink)
                edge["weight"] = 0
            except:
                0
        if len(base_graph.es) == 0:
            # No possible path
            continue
        weight = base_graph.es["weight"]

        has_path = start.get_shortest_paths(sink["name"])[0]
        if len(has_path) == 0:
            continue

        short_path = start.get_shortest_paths(to=sink["name"], weights=weight)[0]
        short_path.remove(sink.index)

        short_path_weight = total_weight(short_path, base_graph)

        full_name_short_path = list()
        for vertex in short_path:
            full_name_short_path.append(base_graph.vs.find(vertex)["name"])

        if (best_path is None or len(best_path[0]) == 0) and len(short_path) > 0:
            # Make short path be with the original names
            best_path = (full_name_short_path, short_path_weight, permutation)
        elif len(short_path) > 0 and best_path[1] > short_path_weight:
            best_path = (full_name_short_path, short_path_weight, permutation)

    if best_path is None:
        # We didn't find no path
        return None

    final_best_path = list()
    for i in range(len(best_path[0]) - 1):
        if len(final_best_path) > 0:
            # Remove the trace of the last target because it is now the new source
            final_best_path.pop()
        source = org_graph.vs.find(best_path[0][i])
        target = org_graph.vs.find(best_path[0][i + 1])
        final_best_path.extend(source.get_shortest_paths(target)[0])

    full_name_short_path = list()
    for vertex in final_best_path:
        full_name_short_path.append(org_graph.vs.find(vertex)["name"])

    return (full_name_short_path, best_path)


def find_best_way(goal_points, graph):
    best_path = deque()
    paths_dict = dict()
    starting_point = goal_points["start"]
    del goal_points["start"]
    last = -1
    while len(goal_points) > 0:
        vertex_color = known_colors[choice(known_colors.keys())]
        for vertex in goal_points.keys():
            # Find shortest paths from vertex
            # Color vertex
            graph.vs.find(str(vertex).encode('ascii', 'replace'))["Fill Color"] = RGBtoHex(vertex_color)
            # Find shortest path if exist with igraph function
            way = graph.get_shortest_paths(starting_point, vertex)
            if len(way[0]) != 0:
                if (last != -1):
                    # Taking out the first node that is the end of the last route taken
                    way[0].pop(0)
                paths_dict[vertex] = path_info(way, len(way[0]), goal_points[vertex])

        # Find the closest node
        stage = min(paths_dict, key=lambda x: paths_dict[x].length_of_way)

        # Transfer from list to queue
        for step in paths_dict[stage].way[0]:
            best_path.append(step)
            last = step

        # Delete the other nodes with of the same group from the goal list
        for key, value in goal_points.items():
            if paths_dict.has_key(stage) and value == paths_dict[stage].satisfied_goal:
                del goal_points[key]
                if key != stage:
                    del paths_dict[key]
        del paths_dict[stage]

        # Saving the last node of this route
        starting_point = last
    return (list(best_path), last)
