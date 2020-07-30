"""
Name: Erel Shtossel
ID: 316297696
"""
import random

from igraph import Graph

from my_utils import to_state, key_max_value_from_actions
import breadcrumbs


class executer(object):
    def __init__(self, q_table, graph):
        self.goal_states = q_table.goal_states
        self.best_way = breadcrumbs.scatter(graph, self.goal_states)[0]
        self.last_step = self.best_way.pop(0)
        self.graph = graph

    def initialize(self, services):
        self.services = services

    def next_action(self):
        if self.services.goal_tracking.reached_all_goals():
            return None

        # find current state
        go_to = self.best_way.pop(0)
        try:
            step = self.graph.es.find(self.graph.get_eid(self.last_step, go_to))["name"].replace(
                self.graph.vs.find(self.last_step)["name"], "").replace(
                self.graph.vs.find(go_to)["name"], "")
        except(Exception):
            0
        self.last_step = go_to
        return step
