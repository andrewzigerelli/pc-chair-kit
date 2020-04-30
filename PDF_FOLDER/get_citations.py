import argparse
import os
import pickle
import re
import csv
import urllib
import unidecode
from time import sleep

import requests
import xmltodict
from fuzzywuzzy import fuzz

from natsort import natsorted


def iterate_csv(filename, encoding=""):
    if not encoding:
        encoding = 'latin-1'
        encoding = 'utf-8'
    with open(filename, newline='', encoding=encoding) as csvfile:
        csv_it = csv.reader(csvfile)
        next(csv_it, None)
        for r in csv_it:
            yield [unidecode.unidecode(i) for i in r]


def log(logstr):
    with open('log.txt', 'a') as f:
        f.write(logstr + '\n')


def check_hits(hits, authors):
    extracted_authors = []
    try:
        hits = hits['hit']
    except:
        # no hits
        pass
    try:
        hit_authors_dict_list = hits['info']['authors']['author']
        for info in hit_authors_dict_list:
            extracted_authors.append(info['#text'])
    except:
        for hit in hits:
            try:
                hit_authors_dict_list = hit['info']['authors']['author']
                for info in hit_authors_dict_list:
                    try:
                        extracted_authors.append(info['#text'])
                    except:
                        extracted_authors.append(
                            hit_authors_dict_list['#text'])
            except:
                continue
    # let's actually match
    matched_authors = []
    for ext in extracted_authors:
        for author in authors:
            author_name = author[0] + " " + author[1]
            result = fuzz.token_sort_ratio(ext, author_name)
            if result > RATIO_MATCH:
                matched_authors.append(author)
    return matched_authors


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


ref_string = re.compile(".*REFERENCES|References|EFERENCES")
quotes = re.compile(r'.*“|"|”')
full_title = re.compile(r'("|”)([^“"]+)("|”)')
cache2 = load_obj('cache2')
RATIO_MATCH = 85


def search_dblp(title):
    url = 'http://dblp.org/search/publ/api'
    payload = {'q': title}
    num_retries = 2
    while num_retries > 0:
        try:
            if title in cache2:
                resource = cache2[title]
            else:
                resource = requests.get(url, params=payload).text
                cache2[title] = resource
                save_obj(cache2, 'cache2')
            return xmltodict.parse(resource)
        except:
            if num_retries > 0:
                print("Block from dblp, sleeping for 10s")
                sleep(10)
                num_retries -= 1
            else:
                return {}

    # woops we failed
    return {}


def get_references(filename, pc_info):
    matches = []
    isTitle = False
    startTitle = False
    endTitle = False
    title = ""
    authors = []
    with open(filename, 'r') as f:
        txt = f.readlines()
        i = 0
        found_references = False  # just for log
        found_title = False # just for log
        for line in txt:
            found = ref_string.match(line)
            found_references = bool(found_references) or found
            if found:
                refs = txt[i:]
                # now see if match
                for r in refs:
                    tokens = r.split(',')
                    new_tokens = []
                    # necessary cleanup
                    for t in tokens:
                        if full_title.match(t):
                            found_title = True
                            full_try = full_title.sub(r"\g<2>", t)
                            title = full_try
                            resp = search_dblp(title)
                            hits = resp['result']['hits']
                            matches.extend(check_hits(hits, authors))
                            # clear title and authors
                            authors = []
                            title = ''
                        try_title = quotes.match(t)
                        if try_title:
                            if isTitle:
                                title = title + t[:try_title.end()-1].strip()
                                found_title = True
                                isTitle = False
                                resp = search_dblp(title)
                                hits = resp['result']['hits']
                                matches.extend(check_hits(hits, authors))
                                # clear title and authors
                                authors = []
                                title = ''
                            else:
                                isTitle = True
                                title = title + \
                                    t[try_title.end():].strip() + " "
                                # always adding space seems to work"
                                continue
                        if isTitle:  # no match, but started, so append
                            title = title + t
                        loc = t.find(']')
                        if loc != -1 and not isTitle:
                            t = t[loc+1:]
                        loc = t.find(' and')
                        if loc != -1 and not isTitle:
                            t = t[loc+4:]
                        new_tokens.append(t)

                    tokens = [t.strip().lstrip().lower() for t in new_tokens]
                    for pc, pc_val in pc_info.items():
                        for t in tokens:
                            search_str = pc_val[0][0].lower(
                            ) + ". " + pc_val[1].lower()
                            result = fuzz.token_sort_ratio(t, search_str)
                            if result > RATIO_MATCH:
                                authors.append(pc_val)
            i += 1
        if not found_references:
            log("Didn't find references in %s" % filename)
        if not found_title:
            log("Didn't find any titles in %s" % filename)

    # write info
    match_dict = {}
    for match in matches:
        match_num = match_dict.get(match, 0)
        match_num += 1
        match_dict[match] = match_num
    # new_filename
    paper_loc = filename.find('paper')
    new_filename = filename[paper_loc:]
    new_filename = new_filename[:-4]
    new_filename = new_filename + ".csv"
    with open(new_filename, 'w') as new_f:
        new_f.write("pc_key,refs\n")
        for match, n in sorted(match_dict.items()):
            new_f.write("%s,%s\n" % (match[2], n))


def get_pc_info(pc_csv):
    pc = {}
    for row in iterate_csv(pc_csv):
        a, first, last, email, a, tpc_or_erc, *nothing = row
        key = first + last
        pc[key] = (first, last, email)
    return pc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--pc_info',
        help='pc_info csv from hotcrp')
    parser.add_argument("--id_min", type=int,
                        default=0,
                        help="min id for author id loop")
    parser.add_argument("--id_max", type=int,
                        default=1000,
                        help="max id for author id loop")
    args = parser.parse_args()

    # get pc_info
    pc_csv = args.pc_info
    pcs = get_pc_info(pc_csv)
    # get min, max for paper loop
    id_min = args.id_min
    id_max = args.id_max

    # get txt submissions
    files_ = os.listdir('.')
    txts = [f for f in files_ if f[:5] == 'micro' and f[-4:] == '.txt']
    txts = natsorted(txts)
    for txt in txts:
        paper_loc = txt.find('paper')
        pd_loc = txt.find('.')
        paper_num = int(txt[paper_loc+5:pd_loc])
        if paper_num >= id_min and paper_num <= id_max:
            get_references(txt, pcs)
            print("done with %s" % txt)
