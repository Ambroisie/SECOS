#! /usr/bin/env python3

# Decompounds from stdin instead of reading a file directly

import logging
import sys

from decompound import Decompounder

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


if len(sys.argv) < 9:
    eprint(
        f"python {sys.argv[0]} dt_candidates word_count_file min_word_count(50) "
        "word_index prefix_length(3) suffix_length(3) word_length(5) dash_word(3) "
        "upper(upper) epsilon"
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
        "prefix_length:\t\tlength of prefixes that are appended to the right-sided "
        "word (recommended parameter: 3)"
    )
    eprint(
        "suffix_length:\t\tlength of suffixes that are appended to the left-sided "
        "word (recommended parameter: 3)"
    )
    eprint(
        "word_length:\t\tminimal word length that is used from the split "
        "candidates (recommended parameter: 5)"
    )
    eprint(
        "dash_word:\t\theuristic to split words with dash, which has no big impact "
        "(recommended: 3)"
    )
    eprint(
        "upper:\t\t\tconsider uppercase letters (=upper) or not (=lower). "
        "Should be set for case-sensitive languages e.g. German"
    )
    eprint("epsilon:\t\tsmoothing factor (recommended parameter: 0.01")
    sys.exit(1)


decompounder = Decompounder(
    min_word_count=int(sys.argv[3]),
    prefix_length=int(sys.argv[4]),
    suffix_length=int(sys.argv[5]),
    min_word_length=int(sys.argv[6]),
    # 1 -> remove, 2 -> split, 3 -> nothing
    dash_words=Decompounder.DashBehaviour(int(sys.argv[7])),
    uppercase_first_letter=True if sys.argv[8] == "upper" else False,
    epsilon=float(sys.argv[9]),
)


file_knowledge = sys.argv[1]
file_wordcount = sys.argv[2]

decompounder.prepare_decompounding(file_wordcount, file_knowledge)

# NOTE: Different from decompound_secos.py
# FIXME: gotta do this
for l in sys.stdin:
    text = ""
    for w in l.strip().split():
        wc = -1
        if w in decompounder.word_count:
            wc = decompounder.word_count[w]
        c1 = decompounder.comp1.get(w, w)
        c2 = decompounder.comp2.get(w, w)
        c3 = decompounder.comp3.get(w, w)
        [u, ufeats] = decompounder._unknown_word_compounding(w)
        cand = w
        cands = [c1, c2, c3, u]
        idx = decompounder._get_first_dash(cands)
        if idx >= 0:
            cand = cands[idx]
        [idx, prob] = decompounder._get_highest_prob(cands)
        pcand = w
        if idx >= 0:
            pcand = cands[idx]
        text += " " + pcand.replace("-", " ")
    print(text.strip())
