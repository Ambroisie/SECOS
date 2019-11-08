#! /usr/bin/env python3

from typing import Set, Dict, IO, Iterable, List, Optional, Tuple

import gzip
import sys

i = 0

if len(sys.argv) < 11:
    sys.stderr.write("python " + sys.argv[0] + " dt_candidates word_count_file min_word_count(50) file_compound word_index prefix_length(3) suffix_length(3) word_length(5) dash_word(3) upper(upper) epsilon\n")
    sys.stderr.write("-----------------------------------------------------\n")
    sys.stderr.write("Parameter description:\n")
    sys.stderr.write("-----------------------------------------------------\n")
    sys.stderr.write("dt_candidates:\t\tfile with words and their split candidates, generated from a distributional thesaurus (DT)\n")
    sys.stderr.write("word_count_file:\tfile with word counts used for filtering\n")
    sys.stderr.write("min_word_count:\t\tminimal word count used for split candidates (recommended paramater: 50)\n")
    sys.stderr.write("file_compound:\t\tfile with words that should be decompounded (each compound needs to be in a single line)\n")
    sys.stderr.write("word_index:\t\tindex of the word in the tab separated file_compound\n")
    sys.stderr.write("prefix_length:\t\tlength of prefixes that are appended to the right-sided word (recommended parameter: 3)\n")
    sys.stderr.write("suffix_length:\t\tlength of suffixes that are appended to the left-sided word (recommended parameter: 3)\n")
    sys.stderr.write("word_length:\t\tminimal word length that is used from the split candidates (recommended parameter: 5)\n")
    sys.stderr.write("dash_word:\t\theuristic to split words with dash, which has no big impact (recommended: 3)\n")
    sys.stderr.write("upper:\t\t\tconsider uppercase letters (=upper) or not (=lower). Should be set for case-sensitive languages e.g. German\n")
    sys.stderr.write("epsilon:\t\tsmoothing factor (recommended parameter: 0.01\n")
    sys.exit(0)
file_knowledge = sys.argv[1]
file_wordcount = sys.argv[2]
min_word_count = int(sys.argv[3])
file_compound = sys.argv[4]
word_index_file_compound = int(sys.argv[5])


prefix_length = int(sys.argv[6])
suffix_length = int(sys.argv[7])
min_word_length = int(sys.argv[8])
epsilon = float(sys.argv[11])
# 1 -> remove, 2 -> split, 3 -> nothing
dash_words = int(sys.argv[9])
uppercaseFirstLetter = False
if sys.argv[10] == "upper":
    uppercaseFirstLetter = True


debug = True


def nopen(f: str) -> IO[str]:
    if f.endswith(".gz"):
        return gzip.open(f)
    return open(f, encoding="utf-8")


words: Set[str] = set()
total_word_count = 0
word_count: Dict[str, int] = {}
for l in nopen(file_wordcount):
    ls = l.strip().split("\t")
    wc = int(ls[1])
    word_count[ls[0]] = wc
    total_word_count += wc


def removeWord(w: str) -> bool:
    if len(w.replace("-", "")) == 0:
        return True
    if min_word_count <= 0:
        return False
    if w in word_count:
        if word_count[w] >= min_word_count:
            return False
    return True


def removeShortAndEqual(wc: str, ws: Iterable[str]) -> List[str]:
    nws = set()
    for w in ws:
        if len(w) >= min_word_length and w.lower() != wc.lower() and not w.isupper() and w.lower() in wc.lower():
            nws.add(w)
    return list(nws)


# count suffixes and prefixes
fillers: Dict[str, int] = {}


def addUp(w: str) -> None:
    if w in fillers:
        fillers[w] += 1
    else:
        fillers[w] = 1


def appendSuffix(w: str) -> str:
    nl = ""
    # first append on the left side
    for l in w.split("-"):
        if len(l) > suffix_length:
            nl += "-"
        else:
            addUp(l)
        nl += l
    nl = nl.strip("-")
    return nl


def appendPrefix(w: str) -> str:
    # append to the right
    nl = ""
    for l in w.split("-"):
        nl += l
        if len(l) > prefix_length:
            nl += "-"
    if nl.endswith("-"):
        nl = nl[:-1]
    return nl


def getWordCounts(comp: str) -> float:
    sum = 1.0
    for c in comp.split("-"):
        if uppercaseFirstLetter:
            c = c[0].upper() + c[1:]
        if c in word_count:
            sum *= (word_count[c] + epsilon) / (total_word_count + epsilon * len(word_count))
        else:
            sum *= epsilon / (total_word_count + epsilon * len(word_count))
    return pow(1.0 * sum, 1.0 / len(comp.split("-")))


def appendSuffixAndPrefix(w: str) -> str:
    sp = appendSuffix(appendPrefix(w))
    ps = appendPrefix(appendSuffix(w))
    spc = getWordCounts(sp)
    psc = getWordCounts(ps)
    if spc > psc:
        return sp
    return ps


def generateCompound(w: str, ws: Iterable[str]) -> Optional[str]:
    # remove too short words
    nws = removeShortAndEqual(w, ws)
    if len(nws) == 0:
        if debug:
            sys.stderr.write("NONE: " + w + "\n")
        return None
    nws_sorted = sorted(nws, key=lambda x: len(x), reverse=True)
    # get split points
    splits = set()
    for n in nws_sorted:
        if not n.lower() in w.lower():
            continue
        idx = w.lower().index(n.lower())
        splits.add(idx)
        splits.add(idx + len(n))
    splits_sorted = sorted(list(splits))
    wc = ""
    prev = 0
    for i in splits_sorted:
        if i == 0:
            continue
        wc += w[prev:i] + "-"
        prev = i
    wc += w[prev:]
    if wc.endswith("-"):
        wc = wc[:-1]
    return wc


def addCompound(comp: Dict[str, str], w: str, ws: str) -> None:
    if ws is not None:
        ws_merged = appendSuffixAndPrefix(ws)
        comp[w] = ws_merged
        if debug:
            sys.stderr.write("Result: " + w + "\t" + ws + "\t" + ws_merged + "\n")


def processCompound(comp: Dict[str, str], w: str, wns: str) -> None:
    wns_split = wns.split(" ")
    if "-" in w and dash_words == 1:
        return
    if dash_words == 2:
        ws = w.split("-")
        for wi in ws:
            res = generateCompound(wi, wns_split)
            if res is not None:
                addCompound(comp, wi, res)
        return
    res = generateCompound(w, wns_split)
    if res is not None:
        addCompound(comp, w, res)


comp1: Dict[str, str] = {}
comp2: Dict[str, str] = {}
comp3: Dict[str, str] = {}
sys.stderr.write("read knowledge\n")


for l in nopen(file_knowledge):
    ls = l.rstrip("\n").split("\t")
    w = ls[0]
    if not removeWord(w):
        processCompound(comp1, w, ls[1])
        processCompound(comp2, w, ls[2])
        processCompound(comp3, w, ls[3])
sys.stderr.write("extract single words\n")
singlewords: Set[str] = set()
for c in comp1:
    if "-" in comp1[c]:
        singlewords |= set(comp1[c].split("-"))
sys.stderr.write("decompound\n")


def containedIn(c: str, cands: Iterable[str]) -> bool:
    for cj in cands:
        if c.lower() in cj.lower() and c.lower() != cj.lower():
            return True
    return False


def unknownWordCompounding(w: str) -> Tuple[str, Set[str]]:
    cands = set()
    for s in singlewords:
        if s.lower() in w.lower() and not s.lower() == w.lower():
            cands.add(s)
    cands_new = set()
    for ci in cands:
        if not containedIn(ci, cands):
            cands_new.add(ci)
    res = generateCompound(w, cands_new)
    if debug:
        sys.stderr.write("unknown1: " + res + "\n")
    if res is None:
        res = w
    else:
        res = appendSuffixAndPrefix(res)
    if debug:
        sys.stderr.write("unknown2: " + res + "\n")
    return (res, cands_new)


def getFirstDash(compounds: Iterable[str]) -> int:
    i = 0
    for c in compounds:
        if "-" in c:
            return i
        i += 1
    return -1


def getMaxIdx(ls: Iterable[float]) -> Tuple[int, float]:
    idx = -1
    val = 0.0
    i = 0
    # NOTE: use enumerate
    for l in ls:
        if l > val:
            val = l
            idx = i
        i += 1
    return (idx, val)


def getHighestProb(compounds: Iterable[str]) -> Tuple[int, float]:
    probs = []
    for c in compounds:
        p = getWordCounts(c)
        probs.append(p)
    return getMaxIdx(probs)


for l in nopen(file_compound):
    ls = l.strip().split("\t")
    w = ls[word_index_file_compound]
    wc = -1
    if w in word_count:
        wc = word_count[w]
    c1 = comp1.get(w, w)
    c2 = comp2.get(w, w)
    c3 = comp3.get(w, w)
    (u, ufeats) = unknownWordCompounding(w)
    prefix = "W"
    cand = w
    feats = ""
    cands = [c1, c2, c3, u]
    cands_str = ["C1", "C2", "C3", "U"]
    idx = getFirstDash(cands)
    if idx >= 0:
        cand = cands[idx]
        prefix = cands_str[idx]
    (idx, prob) = getHighestProb(cands)
    pcand = w
    pprefix = "W"
    if idx >= 0:
        pcand = cands[idx]
        pprefix = cands_str[idx]

    print("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s" % (pprefix, pcand, prefix, cand, c1, c2, c3, u, wc, l.strip()))
