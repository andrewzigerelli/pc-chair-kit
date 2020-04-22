import argparse
import csv
import pickle
import re
from string import ascii_letters

from fuzzywuzzy import fuzz, process


def remove_commas(inst):
    return re.sub(r',', ';', inst)


def check_institutes(inst_file, ttt_file):
    # get known insts
    inst_list, inst_lines, inst2line = get_insts(inst_file)
    unknown_insts = set()
    # get already unknown insts
    # try:
    #    already_unknown = load_obj('already_unknown')
    # except:
    #    already_unknown = []
    # overwrite insts_lines
    # try:
    #    inst_lines = load_obj('inst_lines')
    # except:
    #    pass
    with open(ttt_file, encoding='mac_roman') as csvfile:
        reader = csv.DictReader(csvfile)
        for pc in reader:
            collaborators = pc['collaborators'].split('\n')
            for collab in collaborators:
                # get inst
                left_paren_loc = collab.find('(')
                right_paren_loc = collab.find(')')
                if left_paren_loc == -1 or right_paren_loc == -1:
                    # print("id: %s, collaborator %s, check institution" %
                    #      (pc['id'], collab))
                    continue
                inst = collab[left_paren_loc +
                              1:right_paren_loc].strip().lstrip()
                inst = remove_commas(inst)
                if inst not in inst_list:
                    unknown_insts.add(inst)
    # for u in unknown_insts:
    #    print(u)
    # exit()
    to_add = {}
    for u in sorted(unknown_insts):
        # if u in already_unknown:
        #    continue
        res = process.extract(u, inst_lines, limit=2,
                              scorer=fuzz.token_set_ratio)
        for r in res:
            guess = r[0]
            percent = r[1]
            guess_line_no = inst2line[guess]
            # print(r[1])
            quest = "Should %s be added to: %s\n" % (
                u, inst_lines[guess_line_no])
            # if query_yes_no(quest, default="yes"):
            if r[1] >= 85:
                already_there = inst_lines[guess_line_no]
                new = already_there + ',' + u
                # replace it
                inst_lines[guess_line_no] = new
                inst2line[new] = guess_line_no
                print("replacing: %-100s\n     with: %-100s\n" %
                      (already_there, new))
                #save_obj(inst_lines, 'inst_lines')
                break
            else:
                # let's just try to add it
                print("added: %-100s\n" % u)
                #save_obj(inst_lines, 'inst_lines')
                new_line_no = len(inst_lines)
                inst_lines.append(u)
                inst2line[u] = new_line_no
                break
        # already_unknown.append(u)
        #save_obj(already_unknown, 'already_unknown')
    with open(inst_file, 'w') as f:
       for line in inst_lines:
           f.write(line + '\n')


def get_insts(inst_file):
    inst_lines = []
    inst_list = []
    line_hash = {}
    line_no = 0
    with open(inst_file) as f:
        inst_lines = f.readlines()
        inst_lines = [i.strip() for i in inst_lines]
        for line in inst_lines:
            insts = line.split(',')
            inst_list.extend(insts)
            line_hash[line] = line_no
            line_no += 1
    return inst_list, inst_lines, line_hash


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' "
                  "(or 'y' or 'n').\n")


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='check institutions csv to see if it\'s complete')
    parser.add_argument('inst_file',  type=str,
                        help='csv file of prior institutions file')
    parser.add_argument('ttt_file',  type=str,
                        help='csv file of ttt file')

    args = parser.parse_args()
    check_institutes(args.inst_file, args.ttt_file)
