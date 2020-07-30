"""
Name: Erel Shtossel
ID: 316297696
"""

import random
import threading
import my_utils
import breadcrumbs
import copy
from igraph import *


class learner(object):
    def __init__(self, q_table, last_state=None, last_action=None):
        self.table = q_table.table
        self.time_running = q_table.time_running
        self.meta_data = q_table
        self.last_state = last_state
        self.last_action = last_action
        self.last_valid_actions = []
        self.list_of_actions_with_no_impact = q_table.list_of_actions_with_no_impact
        self.save_format_for_graph = "graphml"

        self.track_finished_goals = list()
        self.num_of_finished_subgoals = 0
        self.points_of_interest = None

        self.time_from_last_save = 100
        self.save_q_table_func = lambda x: x.save_to_file(q_table.path)

        self.learning_rate = 0.8
        self.discount_factor = 0.8
        self.explore_level = 1 - q_table.time_running * 0.09

    def initialize(self, services):
        self.services = services
        self.meta_data.goal_states["start"] = my_utils.to_state(
            self.services.parser.copy_state(self.services.perception.get_state()))
        try:
            file_name = self.services.parser.domain_name + my_utils.to_state(
                self.services.parser.objects) + "." + self.save_format_for_graph
            self.states_graph = Graph.Read(file_name.replace('/', '#'), self.save_format_for_graph)
        except:
            self.states_graph = Graph(directed=True)
        if self.time_running > 0 and len(self.meta_data.goal_states) > 0:
            graph_actions = breadcrumbs.graph_actions(self.states_graph, copy.deepcopy(self.meta_data.goal_states))
            self.breadcrumbs, self.sub_goals_order = graph_actions.calculate_best_path()

            all_actions = list()
            all_goal_actions = list()
            for i in range(len(self.breadcrumbs) - 1):
                action = \
                    self.states_graph.es.find(self.states_graph.get_eid(self.breadcrumbs[i], self.breadcrumbs[i + 1]))[
                        "name"]
                all_actions.append(action)
                if self.breadcrumbs[i + 1] in self.sub_goals_order[0]:
                    all_goal_actions.append(action)

            # Extract a list of actions that we want to do before other actions based on knowledge from the state graph
            self.points_of_interest = dict()
            index_of_last_sub_goal = 0
            place_in_permutation = 0
            for sub_goals in all_goal_actions:
                index_of_sub_goal = all_actions.index(sub_goals)
                path_to_sub_goal = all_actions[index_of_last_sub_goal:index_of_sub_goal + 1]
                path_to_sub_goal.reverse()
                # Remove actions with no impact on the way:
                # i = 1
                # while i < len(path_to_sub_goal):
                #     # Not touching the first element because it is the sub-goal
                #     if path_to_sub_goal[i] in self.list_of_actions_with_no_impact:
                #         path_to_sub_goal.remove(path_to_sub_goal[i])
                #         continue
                #     i += 1
                # goal_words = path_to_sub_goal[0].strip(")").strip("(").split()[1:]
                # i = 1
                # while i in range(len(path_to_sub_goal)):
                #     if not any(x in path_to_sub_goal[i] for x in goal_words):
                #         path_to_sub_goal.remove(path_to_sub_goal[i])
                #         continue
                #     i += 1
                self.points_of_interest[self.sub_goals_order[2][place_in_permutation]] = path_to_sub_goal
                place_in_permutation += 1
                index_of_last_sub_goal = index_of_sub_goal

            self.way_to_groups_of_same_action_dict = dict()
            for task in self.sub_goals_order[2]:
                self.way_to_groups_of_same_action_dict[task] = self.way_to_groups_of_same_action(task)

            if self.breadcrumbs is not None:
                for i in range(len(self.breadcrumbs) - 1):
                    source = self.breadcrumbs[i]
                    target = self.breadcrumbs[i + 1]
                    edge_id = self.states_graph.get_eid(source, target)
                    action = self.states_graph.es.find(edge_id)["name"].strip(source).strip(target)
                    # Every run- the data from the graph is better
                    self.table[source][action] += 1.0 / (pow(2, 6 - self.time_running))

    def save_graph(self):
        file_name = self.services.parser.domain_name + my_utils.to_state(
            self.services.parser.objects) + "." + self.save_format_for_graph
        self.states_graph.save(file_name.replace('/', '#'), format=self.save_format_for_graph)

    def __del__(self):
        curr_state = my_utils.to_state(self.services.parser.copy_state(self.services.perception.get_state()))
        self.update_states_graph(curr_state)

        finished_goals = my_utils.done_subgoals(self.services.goal_tracking.completed_goals,
                                                self.services.perception.get_state())

        if len(self.services.goal_tracking.uncompleted_goals) == 0:
            # We won- find the last sub_goal
            try:
                self.meta_data.goal_states[curr_state] = self.track_finished_goals.index(False)
            except:
                0  # Only one goal
            self.update_table(1000)
        else:
            self.update_table(-1000)

        self.save_q_table_func(self.meta_data)
        self.save_graph()

    def reward_function(self, state, action, new_state):
        # walking is a waist of time
        reward = -1
        if self.time_running > 0 and self.breadcrumbs is not None:
            if self.states_graph.vs.find(state).index in self.breadcrumbs and self.states_graph.vs.find(
                    new_state).index in self.breadcrumbs:
                if self.breadcrumbs.index(self.states_graph.vs.find(state).index) + 1 == self.breadcrumbs.index(
                        self.states_graph.vs.find(new_state).index):
                    reward = 0
        if state == new_state:
            # the last action failed - maybe a better probability can be achieved with an other action
            reward -= 0.1
        # the final reward is given when the simulation ends- so it is in the goal check
        # the final reward is 1000
        return reward

    def update_table(self, reward=None, curr_state=None, curr_seen_best_option_value=None):
        # This function updates the q table
        if reward == None:
            reward = self.reward_function(self.last_state, self.last_action, curr_state)
        else:
            curr_seen_best_option_value = reward

        if not self.table[self.last_state].has_key(self.last_action):
            self.table[self.last_state][self.last_action] = 0
        self.table[self.last_state][self.last_action] = self.table[self.last_state][
                                                            self.last_action] + self.learning_rate * (
                                                                reward + self.discount_factor * curr_seen_best_option_value -
                                                                self.table[self.last_state][self.last_action])

    def explore(self, curr_state, curr_valid_actions):
        action_grades = dict()
        high_graded_action = None
        choose_from = list()
        for iter in curr_valid_actions:
            if (iter not in self.table[curr_state]):
                # This is a new option opened because of our actions
                self.table[curr_state][iter] = 0
            if (self.table[curr_state][iter]) == 0:
                # Go to a place never evaluated
                choose_from.append(iter)

        # Goal analyze
        goal_keywords = self.extract_goal_keywords(self.services.goal_tracking.uncompleted_goals)
        for action in curr_valid_actions:
            for keyword_tuple in goal_keywords:
                update_val = 1
                for keyword in keyword_tuple:
                    if action.find(keyword) != -1:
                        if action_grades.has_key(action):
                            action_grades[action] = update_val
                        else:
                            action_grades[action] = update_val
                            update_val += 1
        if (len(action_grades) > 1):
            high_graded_action = max(random.sample(action_grades.keys(), len(action_grades)), key=action_grades.get)

        if high_graded_action != None:
            if random.random() > math.pow(0.5, action_grades[high_graded_action]):
                return high_graded_action

        if len(curr_valid_actions) > 0:
            try:
                # Choose the least walked in vertex
                vertex = self.states_graph.vs.find(curr_state)
                neighbors = vertex.neighbors()
                y = min(random.sample(neighbors, len(neighbors)), key=lambda x: x["count"])
                for edge in vertex.out_edges():
                    if edge.source == vertex.index and edge.target == y.index:
                        return edge["name"].strip(vertex["name"]).strip(y["name"])
            except:
                0
            return random.choice(curr_valid_actions)

        if len(curr_valid_actions) == 0:
            # Dead end
            return None

    def extract_goal_keywords(self, uncompleted_goals):
        keywords = set()
        for sub_condition in uncompleted_goals:
            for part in sub_condition.parts:
                keywords.add(part.args)
        return keywords

    def next_action(self):
        # find current state
        raw_state_info = self.services.parser.copy_state(self.services.perception.get_state())
        curr_state = my_utils.to_state(raw_state_info)
        curr_valid_actions = self.services.valid_actions.get()

        self.register_new_state(curr_state, curr_valid_actions)
        # Dead end checking
        curr_seen_best_option = my_utils.key_max_value_from_actions(self.table[curr_state])
        if curr_seen_best_option == -1:
            # This is the end - no path from here
            self.update_table(reward=-1500)
            self.update_states_graph(curr_state)
            self.save_graph()
            return None

        list_of_opened_options = list(set(curr_valid_actions).difference(set(self.last_valid_actions)))
        if len(list_of_opened_options) == 0:
            # last action didn't change nothing
            self.list_of_actions_with_no_impact.add(self.last_action)

        if self.last_state != None:
            self.update_states_graph(curr_state)

            finished_goals = my_utils.done_subgoals(self.services.goal_tracking.uncompleted_goals,
                                                    raw_state_info)
            curr_subgoals_finished = my_utils.num_of_done_subgoals(finished_goals)

            if curr_subgoals_finished > self.num_of_finished_subgoals or len(
                    self.services.goal_tracking.uncompleted_goals) == 0:
                # We got a sub goal!
                if len(self.services.goal_tracking.uncompleted_goals) != 0:
                    self.meta_data.goal_states[curr_state] = my_utils.diff(self.track_finished_goals, finished_goals)
                else:
                    self.meta_data.goal_states[curr_state] = 0
                if len(finished_goals) != 0:
                    self.track_finished_goals = finished_goals
                if self.points_of_interest is not None and self.points_of_interest.has_key(
                        self.meta_data.goal_states[curr_state]):
                    del self.points_of_interest[self.meta_data.goal_states[curr_state]]

                self.update_table(1000)
                self.num_of_finished_subgoals = curr_subgoals_finished
                if self.services.goal_tracking.reached_all_goals():
                    # We got all goals!
                    self.save_graph()
                    return None
            elif curr_subgoals_finished < self.num_of_finished_subgoals:
                # We lost a sub goal
                self.update_table(-1100)

            self.track_finished_goals = finished_goals

            # observe and update the q table
            self.update_table(reward=None, curr_state=curr_state,
                              curr_seen_best_option_value=self.table[curr_state][curr_seen_best_option])

        try_action = self.choose_explore_or_exploit(curr_seen_best_option, curr_state, curr_valid_actions)

        # save this state as the last one done:
        self.last_state = curr_state
        self.last_action = try_action
        self.last_valid_actions = curr_valid_actions

        self.time_from_last_save -= 1
        if self.time_from_last_save == 0:
            threading.Thread(target=self.save_q_table_func(deepcopy(self.meta_data))).start()
            # threading.Thread(target=self.save_graph).start()
            self.save_graph()
            self.time_from_last_save = 5000

        # Keep the q_table as clean as possible
        for iter in curr_valid_actions:
            if self.table[curr_state][iter] == 0:
                del self.table[curr_state][iter]
        if len(self.table[curr_state]) == 0:
            self.table[curr_state][try_action] = 0

        return try_action

    def update_states_graph(self, curr_state):
        try:
            vertex = self.states_graph.vs.find(name=str(curr_state))
            vertex["count"] += 1
        except:
            vertex = self.states_graph.add_vertex(str(curr_state))
            vertex["count"] = 1
        try:
            vertex = self.states_graph.vs.find(name=str(self.last_state))
            vertex["count"] += 1
        except:
            vertex = self.states_graph.add_vertex(str(self.last_state))
            vertex["count"] = 1
        try:
            edge = self.states_graph.es.find(name=str(self.last_state) + self.last_action + str(curr_state))
        except:
            edge = self.states_graph.add_edge(str(self.last_state), str(curr_state))
            edge["name"] = self.last_action  # str(self.last_state) + self.last_action + str(curr_state)

    def exploit_graph(self, curr_valid_actions,curr_seen_best_option):
        task = [x for x in self.sub_goals_order[2] if x in self.points_of_interest.keys()][0]
        if not hasattr(self, 'last_task'):
            self.last_task = task
        if not hasattr(self, 'place_on_way') or self.last_task != task:
            if self.meta_data.has_keys == False:
                self.place_on_way = len(self.points_of_interest[task])
            else:
                self.place_on_way = 0
        # TODO: try it once- if it does not work- leave this system (we have keys in this problem)
        if self.meta_data.has_keys == False:
            i = 0
            for action_in_best_path in self.points_of_interest[task]:
                if action_in_best_path in curr_valid_actions:
                    if self.place_on_way != None and self.place_on_way >= i:
                        self.place_on_way = i
                        return action_in_best_path
                    else:
                        # Don't return to this system anymore
                        self.place_on_way = 0
                        self.meta_data.has_keys = True
                        return random.choice(curr_valid_actions)
                i += 1
        else:
            # TODO: if they are 2 actions of the same kind one after one - try not doing the second one

            way_as_groups = self.way_to_groups_of_same_action_dict[task]
            for group_of_actions in way_as_groups[self.place_on_way:]:
                group_of_possible_actions = set(curr_valid_actions).intersection(group_of_actions)
                if len(group_of_possible_actions) > 0:
                    self.place_on_way += 1
                    if curr_seen_best_option in group_of_possible_actions:
                        return curr_seen_best_option
                    return random.choice(list(group_of_possible_actions))
                else:
                    # We can't do what we wanted
                    return curr_seen_best_option

        return None

    def way_to_groups_of_same_action(self, task):
        # Can be calculated only once
        way_as_group = []

        for action in self.points_of_interest[task]:
            if len(way_as_group) > 0:
                last_node = way_as_group.pop()
            else:
                way_as_group.append([action])
                continue
            if last_node is not None and last_node[0].strip("(").split()[0] == action.strip("(").split()[0]:
                # This is the same kind of action
                last_node.append(action)
                way_as_group.append(last_node)
            else:
                way_as_group.append(last_node)
                way_as_group.append([action])
        way_as_group.reverse()
        return way_as_group

    def choose_explore_or_exploit(self, curr_seen_best_option, curr_state, curr_valid_actions):
        x = random.random()
        if x < self.explore_level:
            # time to explore:
            try_action = self.explore(curr_state, curr_valid_actions)
        else:
            # time to exploite:
            if self.breadcrumbs is not None:
                try_action = self.exploit_graph(curr_valid_actions,curr_seen_best_option)
            if try_action is None:
                try_action = curr_seen_best_option
        return try_action

    def register_new_state(self, curr_state, curr_valid_actions):
        if self.table.get(curr_state) is None:
            # this is a new state that we need to evaluate and add to the table
            self.table[curr_state] = dict()
            for iter in curr_valid_actions:
                self.table[curr_state][iter] = 0
        else:
            for iter in curr_valid_actions:
                if not self.table[curr_state].has_key(iter):
                    self.table[curr_state][iter] = 0
