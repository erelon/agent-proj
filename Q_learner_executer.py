"""
Name: Erel Shtossel
ID: 316297696
"""
import random

from my_utils import to_state, key_max_value_from_actions


class executer(object):
    def __init__(self, q_table):
        self.table = q_table.table

    def initialize(self, services):
        self.services = services

    def next_action(self):
        if self.services.goal_tracking.reached_all_goals():
            return None

        # find current state
        curr_state = to_state(self.services.perception.state)

        if self.table.get(curr_state) is None:
            # this is a new state that we have not seen or learned about
            actions = self.services.valid_actions.get()
            if (len(actions) == 0):
                # We lost
                return None
            else:
                return random.choice(self.services.valid_actions.get())

        return key_max_value_from_actions(self.table[curr_state],with_0=False)
