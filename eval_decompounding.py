#! /usr/bin/env python3

from typing import cast, Set, Tuple

import sys

if len(sys.argv) < 3:
    print("cat compound_file | python %s column_predicted column_gold_compound " % (sys.argv[0]))
    sys.exit(0)
col_split = int(sys.argv[1])
col_gold = int(sys.argv[2])
outp = False
if len(sys.argv) > 3:
    outp = True


def getIdx(w: str) -> Set[int]:
    ws = w.split("-")
    i = 0
    idx = set()
    for s in ws:
        i += len(s)
        idx.add(i)
    return idx


def evaluate(w1: str, w2: str) -> Tuple[int, int, int]:
    cc = 0  # correct splits
    wfc = 0  # compound wrong split
    wnc = 0  # compound not split
    w1i = getIdx(w1)
    w2i = getIdx(w2)
    cc = len(w1i & w2i)
    wnc = len(w1i - w2i)
    wfc = len(w2i - w1i)

    return (cc, wfc, wnc)


a = 0
c = 0
scores = (0, 0, 0)
for l in sys.stdin:
    ls = l.strip().split("\t")
    if len(ls) < col_gold or len(ls) < col_split:
        sys.stderr.write("Line too short\n" + l)
    gold = ls[col_gold].lower()
    cand = ls[col_split].lower()
    scores = cast(Tuple[int, int, int], tuple(sum(x) for x in zip(scores, evaluate(gold, cand))))
    flag = "0"
    if gold == cand:
        flag = "1"
        c += 1
    if outp :
        print(flag + "\t" + l.strip())
    a += 1
k = scores
p = 1.0 * k[0] / (1.0 * k[0] + k[1])
r = 1.0 * k[0] * k[0] / (1.0 * k[0] + k[1] + k[2])
f = 2 * p * r / (p + r)
sys.stderr.write("Precision\tRecall\tF1\n")
sys.stderr.write("%f\t%f\t%f\n" % (p, r, f))
sys.stderr.write("%10.4f & %10.4f&%10.4f\n" % (p, r, f))
sys.stderr.write("Considered\tCorrect\tPercentage of Correct ones\n")
sys.stderr.write("%f\t%f\t%f\n" % (a, c, 1.0 * c / a))
