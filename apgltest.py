import time
from itertools import permutations

from igraph import *
import breadcrumbs
import q_table
import copy

if __name__ == '__main__':
    p1 = permutations([3,4])
    p2 = permutations([1,2])
    all_permu = list()
    for a1 in permutations([1,2]):
        for a2 in permutations([3,4,5]):
            all_permu.append(list(a1) + list(a2))


    for a in all_permu:
        print a

    # domain_path = "doms and probs/freecell_domain (1).pddl"  # #  # sys.argv[2]
    # problem_path = "doms and probs/freecell_problem (1).pddl"  # # # sys.argv[3]
    #
    # file = open(problem_path, 'r')
    # policy_name = file.readline().replace("(define (problem ", "")
    # while policy_name == "\n":
    #     policy_name = file.readline().replace("(define (problem ", "")
    # policy_name = policy_name[0:policy_name.find(")")] + "_Q_Table"
    # file.close()
    #
    # q = q_table.q_table()
    # q.build_from_file(policy_name)
    #
    # g = breadcrumbs.transetive_close(deepcopy(q.goal_states), Graph.Read("states_graph", "graphml"))
    # breadcrumbs.find_best_way2(deepcopy(q.goal_states), g, Graph.Read("states_graph", "graphml"))
