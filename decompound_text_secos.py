#! /usr/bin/env python3

# Decompounds from stdin instead of reading a file directly

import gzip
import sys
from typing import IO, Dict, Iterable, List, Optional, Set, Tuple

i = 0


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
file_knowledge = sys.argv[1]
file_wordcount = sys.argv[2]
min_word_count = int(sys.argv[3])


prefix_length = int(sys.argv[4])
suffix_length = int(sys.argv[5])
min_word_length = int(sys.argv[6])
epsilon = float(sys.argv[9])
# 1 -> remove, 2 -> split, 3 -> nothing
dash_words = int(sys.argv[7])
uppercaseFirstLetter = False
if sys.argv[8] == "upper":
    uppercaseFirstLetter = True


debug = not True


def nopen(f: str) -> IO[str]:
    if f.endswith(".gz"):
        return gzip.open(f)
    return open(f, encoding="utf-8")


words: Set[str] = set()
total_word_count = 0
word_count: Dict[str, int] = {}
for l in nopen(file_wordcount):
    ls = l.strip().split("\t")
    if len(ls) < 2:
        continue  # Differences between python2 and python3 strip method made it crash
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
        if (
            len(w) >= min_word_length
            and w.lower() != wc.lower()
            and not w.isupper()
            and w.lower() in wc.lower()
        ):
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
    nw = w
    nl = ""
    for l in nw.split("-"):
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
            sum *= (word_count[c] + epsilon) / (
                total_word_count + epsilon * len(word_count)
            )
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
            eprint(f"NONE: {w}")
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
            eprint(f"Result: {w}\t{ws}\t{ws_merged}")


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
eprint("read knowledge")


for l in nopen(file_knowledge):
    ls = l.rstrip("\n").split("\t")
    w = ls[0]
    if not removeWord(w):
        processCompound(comp1, w, ls[1])
        processCompound(comp2, w, ls[2])
        processCompound(comp3, w, ls[3])
eprint("extract single words")
singlewords: Set[str] = set()
for c in comp1:
    if "-" in comp1[c]:
        singlewords |= set(comp1[c].split("-"))
eprint("decompound")


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
        eprint(f"unknown1: {res}")
    if res is None:
        res = w
    else:
        res = appendSuffixAndPrefix(res)
    if debug:
        eprint(f"unknown2: {res}")
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


# NOTE: Different from decompound_secos.py
for l in sys.stdin:
    text = ""
    for w in l.strip().split():
        wc = -1
        if w in word_count:
            wc = word_count[w]
        c1 = comp1.get(w, w)
        c2 = comp2.get(w, w)
        c3 = comp3.get(w, w)
        [u, ufeats] = unknownWordCompounding(w)
        cand = w
        cands = [c1, c2, c3, u]
        idx = getFirstDash(cands)
        if idx >= 0:
            cand = cands[idx]
        [idx, prob] = getHighestProb(cands)
        pcand = w
        if idx >= 0:
            pcand = cands[idx]
        text += " " + pcand.replace("-", " ")
    print(text.strip())
