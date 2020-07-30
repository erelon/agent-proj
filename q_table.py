"""
Name: Erel Shtossel
ID: 316297696
"""

import thread
from copy import deepcopy
import json


class q_table_Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, q_table):
            return {
                "path": obj.path,
                "q_table": obj.table,
                "time_running": obj.time_running,
                "actions_with_no_impact": obj.list_of_actions_with_no_impact,
                "goal_states": obj.goal_states,
                "has_keys": obj.has_keys
            }
        if isinstance(obj, float):
            return round(obj, 3)
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, bool):
            return str(obj)
            # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class q_table():
    def __init__(self):
        self.table = dict()
        self.goal_states = dict()
        self.time_running = int
        self.list_of_actions_with_no_impact = set()
        self.path = str
        self.has_keys = bool

    def build_from_file(self, policy_path):
        try:
            self.path = policy_path
            file = open(policy_path, 'r')
            raw = json.load(file)
            self.table = raw['q_table']
            self.time_running = raw['time_running'] + 1
            self.path = raw['path']
            self.goal_states = raw['goal_states']
            self.list_of_actions_with_no_impact = set(raw['actions_with_no_impact'])
            self.has_keys = raw['has_keys']
        except Exception as e:
            # create a new file
            self.time_running = 0
            self.has_keys =False
            file = open(policy_path, 'a')
            json.dump(self, file, cls=q_table_Encoder)
        file.close()
        return self.table

    def save_to_file(self, policy_path):
        self.path = policy_path
        file = open(policy_path, 'w')
        json.dump(self, file, cls=q_table_Encoder)
        file.close()
