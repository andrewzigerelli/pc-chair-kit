import argparse
import csv
import pickle
import re
from string import ascii_letters


def cleanup(filename):
    print(ascii_letters)
    exit()
    asciis = ascii_letters + ' .-'
    ### DEFINE SPECIAL CHARS HERE
    special_chars = asciis
    to_check = {}
    check_pc_names = {}
    check_collab_names = {}
    susp_1 = re.compile(".*,.*")


    def isascii(s): return len(s) == len(s.encode())
    with open(filename, encoding='mac_roman') as csvfile:
        reader = csv.DictReader(csvfile)
        for pc in reader:
            pc_name = pc['first'] + pc['last']
            if set(pc_name).difference(special_chars):
                check_pc_names[pc['']] = pc_name
            isBad = False
            non_ascii = False
            bad_collabs = []
            non_ascii_list = []
            collaborators = pc['collaborators'].split('\n')
            for collab in collaborators:
                # remove university
                left_paren_loc = collab.find('(')
                if left_paren_loc > -1:
                    collab = collab[:left_paren_loc].strip()
                if susp_1.match(collab):
                    isBad = True
                    bad_collabs.append(collab)
                if set(collab).difference(special_chars):
                    non_ascii = True
                    non_ascii_list.append(collab)
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Cleanup ttt file from HOTCRP')
    parser.add_argument('filename',  type=str,
                        help='csv file of names and dblp links')
    args = parser.parse_args()
    cleanup(filename=args.filename)
