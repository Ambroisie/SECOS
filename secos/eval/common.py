from typing import NamedTuple, Set


class EvalResult(NamedTuple):
    correct: int
    wrong: int
    unsplit: int


def get_idx(w: str) -> Set[int]:
    ws = w.split("-")
    i = 0
    idx = set()
    for s in ws:
        i += len(s)
        idx.add(i)
    return idx


def evaluate(w1: str, w2: str) -> EvalResult:
    cc = 0  # correct splits
    wfc = 0  # compound wrong split
    wnc = 0  # compound not split
    w1i = get_idx(w1)
    w2i = get_idx(w2)
    cc = len(w1i & w2i)
    wnc = len(w1i - w2i)
    wfc = len(w2i - w1i)
    return EvalResult(cc, wfc, wnc)
