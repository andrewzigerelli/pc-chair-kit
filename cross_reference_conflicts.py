import pickle
import sys

from tqdm import tqdm

from base import Institutions
from dblp_crawler import Cache
from pc_members import PCMember, Publication, Submission
from util import get_dict_json, iterate_csv

# load vars from disk istead
FAST = True


def print_conflict_list(l):
    s = ""
    for email, reasons in l.items():
        s += ("====> email: %s\n" % email)
        if reasons:
            s += str(reasons) + '\n'
    return s


def print_reports(sub_list, conflict_type, report_file, pid=None):
    csv_list = []
    for s in tqdm(sub_list):
        if pid:
            if s.pid != pid:
                continue
        csv_list += s.conflicts_csv(conflict_type)

    str_out = "valid, pid, email, reasons\n"
    str_out += "\n".join(csv_list)
    with open(report_file, 'w') as f:
        f.write(str_out)


def main():
    cache = Cache.load('data/.cache_queries')
    institutions_csv = sys.argv[1]
    submissions_json = sys.argv[2]
    hotcrp_pc_member_csv = sys.argv[3]
    pc_member_paper_db_csv = sys.argv[4]

    out_proper = sys.argv[5]
    out_paper_collabs_field = sys.argv[6]
    out_pc_collabs_field = sys.argv[7]
    out_dblp = sys.argv[8]
    out_fake = sys.argv[9]

    # Step 1: read all the inputs (institutions_csv, paper data from hotcrp,
    # pc info from hotcrp and paper db from dblp):
    print("Reading institutions csv...")
    try:
        if not FAST:
            raise Exception('NOT FAST')
        institutions = load_obj('institutions')
    except:
        institutions = Institutions(institutions_csv)
        save_obj(institutions, 'institutions')

    print("Reading submissions:")
    try:
        if not FAST:
            raise Exception('NOT FAST')
        i = load_obj('i')
        submissions = load_obj('submissions')
    except:
        submissions = []
    d = get_dict_json(submissions_json)
    j = 0
    for p in tqdm(d):
        if j < i:
            j += 1
            continue
        else:
            submissions.append(Submission.from_json(p, institutions))
            save_obj(submissions, 'submissions')
            j += 1
            save_obj(j, 'i')
        #submissions = [Submission.from_json(p, institutions) for p in tqdm(d)]

    print("Reading hotcrp pc members:")
    try:
        if not FAST:
            raise Exception('NOT FAST')
        hotcrp_pc_members = load_obj('hotcrp_pc_members')
    except:
        hotcrp_pc_members = [PCMember.from_hotcrp_csv(line, institutions)
                             for line in tqdm(iterate_csv(hotcrp_pc_member_csv,
                                                          encoding='utf-8'))]
        hotcrp_pc_members = {p.email: p for p in hotcrp_pc_members}
        save_obj(hotcrp_pc_members, 'hotcrp_pc_members')

    print("Reading pc papers:")
    try:
        if not FAST:
            raise Exception('NOT FAST')
        dblp_pc_members = load_obj('dblp_pc_members')
    except:
        dblp_pc_members = {k: p.copy_no_conflicts()
                           for k, p in hotcrp_pc_members.items()}
        for row in tqdm(iterate_csv(pc_member_paper_db_csv)):
            (email, id, firstname, lastname, keys, valid,
             pub_key, pub_title, pub_year, pub_authors) = row

            if valid == "x":
                pub = Publication.from_key2(pub_key, institutions, cache)
                try:
                    dblp_pc_members[email].add_publication(pub)
                except:
                    print("check: ", firstname, lastname, email, pub_title)
        save_obj(dblp_pc_members, 'dblp_pc_members')

    print("Cross referencing conflicts")
    for s in tqdm(submissions):
        if s.pid != 1267:
            continue
        # Step 2: list conflicts that are declared by authors properly
        # Step 3: list conflicts that are declared by authors
        #         in the collaborators field

        # for each pc, see if submission listed them in conflicts 
        # if it did, add it
        # i.e. only care about conflicts that paper listed that are actually
        # pc
        for k, v in hotcrp_pc_members.items():
            s.add_collaborator_conflict(v)

        # Step 4: list conflicts declared by pc members but undeclared
        # by paper authors
        # so for each pc member, check if the authors are on
        # the pc members conflict list
        for k, v in hotcrp_pc_members.items():
            s.add_conflicts_from_pc_member(v)
        #print(s)

        # Step 5: list conflicts not declared by anyone but caught by dblp
        for k, v in dblp_pc_members.items():
            s.add_conflicts_from_dblp(v)

        # Step 6:
        for k, v in dblp_pc_members.items():
            s.add_fake_conflicts(hotcrp_pc_members[k], v)

    print_reports(submissions, 'proper', out_proper)
    print_reports(submissions, 'collaborators_field', out_paper_collabs_field)
    print_reports(submissions, 'declared_by_pc_members', out_pc_collabs_field)
    print_reports(submissions, 'dblp', out_dblp)
    print_reports(submissions, 'fake_conflicts', out_fake)

#    print_reports(submissions, 'proper', out_proper, pid=12)
#    print_reports(submissions, 'collaborators_field', out_paper_collabs_field,
#                  pid=12)
#    print_reports(submissions, 'declared_by_pc_members', out_pc_collabs_field,
#                  pid=12)
#    print_reports(submissions, 'dblp', out_dblp, pid=12)
#    print_reports(submissions, 'fake_conflicts', out_fake, pid=12)


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


if __name__ == '__main__':
    #i = 0
    #save_obj(i, 'i')
    #exit()
    main()
