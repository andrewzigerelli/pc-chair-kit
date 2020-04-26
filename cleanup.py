import argparse
import csv
import pickle
import re
from string import ascii_letters


def translate(name, trans_dict, legal_chars):
    new_name = ''
    print(name)
    for char in name:
        if char not in legal_chars:
            try:
                new_name += trans_dict[char]
            except:
                print('Need to known translation of %s\n' % char)
                print("What should it be? Enter it:\n")
                choice = input()
                trans_dict[char] = choice.strip()
                save_obj(trans_dict, 'translation_dict')
                raise Exception('Run script again')
        else:
            new_name += char
    return new_name


def fix_backwards(name):
    return 'FIX ME' + name


def cleanup(filename):
    try:
        trans_dict = load_obj('translation_dict')
    except:
        print('You need translation_dict.pkl in the cleanup.py directory.')
        # add some defaults
        trans_dict = {"'": ""}
    asciis = ascii_letters + ' .-'

    # DEFINE SPECIAL CHARS HERE
    legal_chars = asciis

    to_check = {}
    check_pc_names = {}
    check_collab_names = {}

    # DEFINE REGEX HERE
    susp_1 = re.compile(".*,.*")
    fan_yao = re.compile("(^[^0-9][A-Za-z ]*)(,)([A-Za-z ]*)\([^)]*\)")

    def isascii(s): return len(s) == len(s.encode())
    with open(filename, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for pc in reader:
            pc_name = pc['first'] + pc['last']
            if set(pc_name).difference(legal_chars):
                check_pc_names[pc['']] = pc_name
            isBad = False
            non_ascii = False
            bad_collabs = []
            non_ascii_list = []
            collaborators = pc['collaborators'].split('\n')
            i = 0
            # hardcoded fixes
            # Fan Yao fix
            #if pc[''] == '76':
            #    new_collaborators = []
            #    for collab in collaborators:
            #        res = fan_yao.match(collab)
            #        name = res.group(1).strip().rstrip()
            #        institute = res.group(2).strip().lstrip()
            #        new_collaborators.append(name + " (" + institute + ")")
            #    collaborators = new_collaborators

            for collab in collaborators:
                # remove university
                left_paren_loc = collab.find('(')
                if left_paren_loc > -1:
                    collab = collab[:left_paren_loc].strip()

                # check for backwards name
                if susp_1.match(collab):
                    isBad = True
                    bad_collabs.append(collab)
                    fixed = fix_backwards(collab)
                    collaborators[i] = fixed
                    print('backwards name\n')
                    print("changed: %-80s\n     to: %-80s\n" % (collab, fixed))
                if set(collab).difference(legal_chars):
                    non_ascii = True
                    non_ascii_list.append(collab)
                    fixed = translate(collab, trans_dict, legal_chars)
                    print('bad char in name\n')
                    print("changed: %-80s\n     to: %-80s\n" % (collab, fixed))
                # do next guy
                i = i + 1

            if isBad:
                to_check[pc['']] = bad_collabs
            if non_ascii:
                check_collab_names[pc['']] = non_ascii_list

    print("bad collab format")
    for key, value in to_check.items():
        print(key)
        print(value)
    print('='*80)

    print("check pc names")
    for key, value in check_pc_names.items():
        print(key)
        print(value)
    print('='*80)

    print("check collab names")
    for key, value in check_collab_names.items():
        print(key)
        print(value)


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Cleanup ttt file from HOTCRP')
    parser.add_argument('filename',  type=str,
                        help='csv file of names and dblp links')
    args = parser.parse_args()
    cleanup(filename=args.filename)
