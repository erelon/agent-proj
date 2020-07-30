"""
Name: Erel Shtossel
ID: 316297696
"""
import collections
import hashlib
import base64
import json
import operator
import pickle


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def asciify_dict(dic):
    if isinstance(dic, str):
        return (dic.encode("ascii"))
    if isinstance(dic, unicode):
        return (dic.encode("ascii"))
    elif isinstance(dic, dict):
        for key in dic:
            dic[key] = asciify_dict(dic[key])
        return (dic)
    elif isinstance(dic, list):
        new_l = []
        for e in sorted(dic):
            new_l.append(asciify_dict(e))
        return (new_l)
    elif isinstance(dic, set):
        return set(asciify_dict(list(dic)))
    elif isinstance(dic, tuple):
        new_l =[]
        for e in dic:
            new_l.append(asciify_dict(e))
        return (tuple(new_l))
    else:
        return (dic)


def to_state(curr_state):
    asciify_dict(curr_state)
    return make_hash_sha256(make_hashable(curr_state))


def key_max_value_from_actions(option_dict,with_0=True):
    if len(option_dict) == 0:
        # A dead end - no actions from here
        return -1
    if with_0==True:
        return max(option_dict.keys(), key=(lambda k: option_dict[k]))
    else:
        max_val = None
        result = None
        for k, v in option_dict.items():
            if v and (max_val is None or v > max_val):
                max_val = v
                result = k
        return result


def num_of_done_subgoals(list_of_uncompleted_goal):
    return list_of_uncompleted_goal.count(True)


def done_subgoals(list_of_uncompleted_goals, raw_state_info):
    total_uncompleted_goals = list()
    for goal in list_of_uncompleted_goals:
        total_uncompleted_goals.extend([part.test(raw_state_info) for part in goal.parts])
    return total_uncompleted_goals


def diff(list1, list2):
    for i in range(len(list1)):
        if list1[i] != list2[i]:
            return i


def make_hash_sha256(o):
    hasher = hashlib.sha256()
    hasher.update(repr(make_hashable(o)).encode())
    return base64.b64encode(hasher.digest()).decode()


def make_hashable(o):
    if isinstance(o, (tuple, list)):
        return tuple((make_hashable(e) for e in o))

    if isinstance(o, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in o.items()))

    if isinstance(o, (set, frozenset)):
        return tuple(sorted(make_hashable(e) for e in o))

    return o


def RGBtoHex(vals, rgbtype=1):
    """Converts RGB values in a variety of formats to Hex values.

       @param  vals     An RGB/RGBA tuple
       @param  rgbtype  Valid valus are:
                            1 - Inputs are in the range 0 to 1
                          256 - Inputs are in the range 0 to 255

       @return A hex string in the form '#RRGGBB' or '#RRGGBBAA'
  """

    if len(vals) != 3 and len(vals) != 4:
        raise Exception("RGB or RGBA inputs to RGBtoHex must have three or four elements!")
    if rgbtype != 1 and rgbtype != 256:
        raise Exception("rgbtype must be 1 or 256!")

    # Convert from 0-1 RGB/RGBA to 0-255 RGB/RGBA
    if rgbtype == 1:
        vals = [255 * x for x in vals]

    # Ensure values are rounded integers, convert to hex, and concatenate
    return '#' + ''.join(['{:02X}'.format(int(round(x))) for x in vals])
