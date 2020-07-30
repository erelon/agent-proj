"""
Name: Erel Shtossel
ID: 316297696
"""
import atexit
import sys
from igraph import Graph

import breadcrumbs

from pddlsim.local_simulator import LocalSimulator

import Q_learner_executer
import learner
import graph_executor
import q_table


def main():
    domain_path ="doms and probs/satellite_domain_multi.pddl"#"doms and probs/rover_domain (2).pddl"# #  #  #sys.argv[2]
    problem_path ="doms and probs/satellite_problem_multi.pddl"#"doms and probs/rover_problem (2).pddl" #  # # sys.argv[3]

    # Find the problem and the world in the problem name
    file = open(problem_path, 'r')
    policy_name = file.readline().replace("(define (problem ", "")
    while policy_name == "\n":
        policy_name = file.readline().replace("(define (problem ", "")
    policy_name = policy_name[0:policy_name.find(")")] + "_Q_Table"
    file.close()

    file = open(domain_path)
    is_deterministic = file.read().find("probabilistic") == -1
    file.close()

    file = open(problem_path)
    is_transparent = file.read().find("reveal") == -1
    file.close()

    # if (is_deterministic == False):
    # load\create the Qtable
    q = q_table.q_table()
    q.build_from_file(policy_name)
    # if sys.argv[1] == "-E":
    # execute mode
    #
    # if is_deterministic == False:
    #print LocalSimulator().run(domain_path, problem_path, Q_learner_executer.executer(q))
    # else:
    #print LocalSimulator().run(domain_path, problem_path, graph_executor.executer(q,Graph.Read("roverMqsdkJedCB9zj3HW+RaxCJQcsI6i4w3XNYU8vDEdkFo=.graphml", "graphml")))

    # elif sys.argv[1] == "-L":
    # atexit.register(q.save_to_file, policy_path=policy_name)
    # learn mode
    print LocalSimulator().run(domain_path, problem_path, learner.learner(q))
    # save the Qtable

    #q.save_to_file(policy_name)


if __name__ == '__main__':
    main()
