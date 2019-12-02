# Training new decompounding models using a distributional thesaurus from JoBimText

import logging
import re
import sys
from dataclasses import InitVar, dataclass, field
from typing import Dict, Iterable, List, Pattern, TextIO


def add_to_set(d: Dict[str, int], s: Iterable[str]) -> None:
    """
    Increment the values mapped in d to each string in s,
    creating the mapping if it doesn't exist.
    """
    for w in s:
        if w in d:
            d[w] += 1
        else:
            d[w] = 1


@dataclass
class Trainer:
    """
    Train the SECOS model from a distributional thesaurus.
    """

    input: TextIO = sys.stdin
    split_dash: bool = False
    dt: Dict[str, List[str]] = field(default_factory=dict, init=False)
    pattern: InitVar[str] = field(default=".*")
    accept: Pattern[str] = field(init=False)

    def __post_init__(self, pattern: str) -> None:
        """
        This hook is run at the end of __init__, with variables marked as
        `InitVar` given as arguments.
        """
        self.accept = re.compile(pattern)

    def _get_overlap(self, w: str, ls: List[str]) -> List[str]:
        """
        Return the list of words in ls that are subsets of w, taking into account if
        words should be split on dashes.
        """
        wl = w.lower()
        ret = []
        for l in ls:
            if l.lower() in wl:
                ret.append(l)
            if self.split_dash and "-" in l:
                lm = l.split("-")
                for m in lm:
                    if m in wl:
                        ret.append(l)
        return ret

    def _read_input(self) -> None:
        """
        Read the distributional thesaurus.
        """
        for l in self.input:
            ls = l.strip().split("\t")
            w1 = ls[0]
            w2 = ls[1]
            if not (self.accept.match(w1) and self.accept.match(w2)):
                logging.info(f"Not accepted: {w1}\t{w2}")
                continue
            if w1 in self.dt:
                self.dt[w1].append(w2)
            else:
                self.dt[w1] = [w2]

    def train(self, output: TextIO = sys.stdout) -> None:
        """
        Train on the input given at construction, outuput training data to output file
        given in argument.
        """
        self._read_input()

        for w1 in self.dt:
            sims = self.dt[w1]
            word_overlap = self._get_overlap(w1, sims)
            sims_overlap: Dict[str, int] = {}
            for w2 in sims:
                if w2 in self.dt:
                    overlap = self._get_overlap(w1, self.dt[w2])
                    add_to_set(sims_overlap, overlap)
            out1 = ""
            out2 = ""
            out3 = " ".join(word_overlap)
            for w2 in sims_overlap:
                out1 += " " + w2
                out2 += " " + w2 + ":" + str(sims_overlap[w2])
            out3 = out3 + out1
            out1 = out1.strip()
            print(
                f"{w1}\t{' '.join(word_overlap)}\t{out1}\t{out3}\t{out2}", file=output
            )
