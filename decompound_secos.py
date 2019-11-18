#! /usr/bin/env python3

# Decompounds from a file given as input

import logging
import sys

from decompound import Splitter

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


if len(sys.argv) < 11:
    eprint(
        f"python {sys.argv[0]} dt_candidates word_count_file "
        "min_word_count(50) file_compound word_index prefix_length(3) "
        "suffix_length(3) word_length(5) dash_word(3) upper(upper) epsilon"
    )
    eprint("-----------------------------------------------------")
    eprint("Parameter description:")
    eprint("-----------------------------------------------------")
    eprint(
        "dt_candidates:\t\tfile with words and their split candidates, "
        "generated from a distributional thesaurus (DT)"
    )
    eprint("word_count_file:\tfile with word counts used for filtering")
    eprint(
        "min_word_count:\t\tminimal word count used for split candidates "
        "(recommended paramater: 50)"
    )
    eprint(
        "file_compound:\t\tfile with words that should be decompounded "
        "(each compound needs to be in a single line)"
    )
    eprint("word_index:\t\tindex of the word in the tab separated file_compound")
    eprint(
        "prefix_length:\t\tlength of prefixes that are appended to the right-sided "
        "word (recommended parameter: 3)"
    )
    eprint(
        "suffix_length:\t\tlength of suffixes that are appended to the left-sided "
        "word (recommended parameter: 3)"
    )
    eprint(
        "word_length:\t\tminimal word length that is used from the split candidates "
        "(recommended parameter: 5)"
    )
    eprint(
        "dash_word:\t\theuristic to split words with dash, which has no big impact "
        "(recommended: 3)"
    )
    eprint(
        "upper:\t\t\tconsider uppercase letters (=upper) or not (=lower). Should be "
        "set for case-sensitive languages e.g. German"
    )
    eprint("epsilon:\t\tsmoothing factor (recommended parameter: 0.01")
    sys.exit(1)

decompounder = Splitter(
    min_word_count=int(sys.argv[3]),
    prefix_length=int(sys.argv[6]),
    suffix_length=int(sys.argv[7]),
    min_word_length=int(sys.argv[8]),
    # 1 -> remove, 2 -> split, 3 -> nothing
    dash_words=Splitter.DashBehaviour(int(sys.argv[9])),
    uppercase_first_letter=True if sys.argv[10] == "upper" else False,
    epsilon=float(sys.argv[11]),
)


file_knowledge = sys.argv[1]
file_wordcount = sys.argv[2]

decompounder.prepare_decompounding(file_wordcount, file_knowledge)


file_compound = sys.argv[4]
word_index_file_compound = int(sys.argv[5])

logging.info("decompound")
for l in open(file_compound):
    ls = l.strip().split("\t")
    w = ls[word_index_file_compound]
    wc = -1
    if w in decompounder.word_count:
        wc = decompounder.word_count[w]
    # NOTE: the following is just Decompounder.split_compound with debugging info
    c1 = decompounder.comp1.get(w, w)
    c2 = decompounder.comp2.get(w, w)
    c3 = decompounder.comp3.get(w, w)
    (u, ufeats) = decompounder._unknown_word_compounding(w)
    prefix = "W"
    cand = w
    feats = ""
    cands = [c1, c2, c3, u]
    cands_str = ["C1", "C2", "C3", "U"]
    idx = decompounder._get_first_dash(cands)
    if idx >= 0:
        cand = cands[idx]
        prefix = cands_str[idx]
    (idx, prob) = decompounder._get_highest_prob(cands)
    pcand = w
    pprefix = "W"
    if idx >= 0:
        pcand = cands[idx]
        pprefix = cands_str[idx]

    print(
        f"{pprefix}\t{pcand}\t{prefix}\t{cand}\t{c1}\t{c2}\t{c3}\t{u}\t{wc}\t"
        f"{l.strip()}"
    )
