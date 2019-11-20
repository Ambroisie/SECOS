import gzip
import logging
from dataclasses import dataclass, field
from enum import IntEnum
from typing import IO, Dict, Iterable, List, Optional, Set, Tuple


def nopen(f: str) -> IO[str]:
    if f.endswith(".gz"):
        return gzip.open(f)
    return open(f, encoding="utf-8")


def contained_in(c: str, cands: Iterable[str]) -> bool:
    for cj in cands:
        if c.lower() in cj.lower() and c.lower() != cj.lower():
            return True
    return False


def get_max_idx(ls: Iterable[float]) -> Tuple[int, float]:
    """
    Return the index and value of the maximum in the given iterable,
    returns (-1, 0.0) on empty iterables
    """
    return max(enumerate(ls), key=lambda x: x[1], default=(-1, 0.0))


@dataclass
class Splitter:
    class DashBehaviour(IntEnum):
        """
        Which heuristic should the decompounder use to split dashed-words.
        """

        REMOVE = 1
        SPLIT = 2
        IGNORE = 3

    epsilon: float = 0.01
    min_word_length: int = 5
    min_word_count: int = 50
    prefix_length: int = 3
    suffix_length: int = 3
    dash_words: DashBehaviour = DashBehaviour.IGNORE
    uppercase_first_letter: bool = False
    single_words: Set[str] = field(default_factory=set, init=False)
    # count suffixes and prefixes
    fillers: Dict[str, int] = field(default_factory=dict, init=False)
    total_word_count: int = field(default=0, init=False)
    word_count: Dict[str, int] = field(default_factory=dict, init=False)
    comp1: Dict[str, str] = field(default_factory=dict, init=False)
    comp2: Dict[str, str] = field(default_factory=dict, init=False)
    comp3: Dict[str, str] = field(default_factory=dict, init=False)

    def _remove_word(self, w: str) -> bool:
        if len(w.replace("-", "")) == 0:
            return True
        if self.min_word_count <= 0:
            return False
        return self.word_count.get(w, 0) < self.min_word_count

    def _remove_short_and_equal(self, wc: str, ws: Iterable[str]) -> List[str]:
        nws = set()
        for w in ws:
            if (
                len(w) >= self.min_word_length
                and w.lower() != wc.lower()
                and not w.isupper()
                and w.lower() in wc.lower()
            ):
                nws.add(w)
        return list(nws)

    def _add_up(self, w: str) -> None:
        if w in self.fillers:
            self.fillers[w] += 1
        else:
            self.fillers[w] = 1

    def _append_suffix(self, w: str) -> str:
        nl = ""
        # first append on the left side
        for l in w.split("-"):
            if len(l) > self.suffix_length:
                nl += "-"
            else:
                self._add_up(l)
            nl += l
        nl = nl.strip("-")
        return nl

    def _append_prefix(self, w: str) -> str:
        # append to the right
        nl = ""
        for l in w.split("-"):
            nl += l
            if len(l) > self.prefix_length:
                nl += "-"
        if nl.endswith("-"):
            nl = nl[:-1]
        return nl

    def _get_word_counts(self, comp: str) -> float:
        tot = 1.0
        split = comp.split("-")
        for c in split:
            if self.uppercase_first_letter:
                c = c[0].upper() + c[1:]
            tot *= (self.word_count.get(c, 0) + self.epsilon) / (
                self.total_word_count + self.epsilon * len(self.word_count)
            )
        return pow(tot, 1.0 / len(split))

    def _append_suffix_and_prefix(self, w: str) -> str:
        sp = self._append_suffix(self._append_prefix(w))
        ps = self._append_prefix(self._append_suffix(w))
        spc = self._get_word_counts(sp)
        psc = self._get_word_counts(ps)
        if spc > psc:
            return sp
        return ps

    def _generate_compound(self, w: str, ws: Iterable[str]) -> Optional[str]:
        # remove too short words
        nws = self._remove_short_and_equal(w, ws)
        if len(nws) == 0:
            logging.debug(f"NONE: {w}")
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

    def _add_compound(self, comp: Dict[str, str], w: str, ws: Optional[str]) -> None:
        if ws is not None:
            ws_merged = self._append_suffix_and_prefix(ws)
            comp[w] = ws_merged
            logging.debug(f"Result: {w}\t{ws}\t{ws_merged}")

    def _process_compound(self, comp: Dict[str, str], w: str, wns: str) -> None:
        wns_split = wns.split(" ")
        if "-" in w and self.dash_words == self.DashBehaviour.REMOVE:
            return
        if self.dash_words == self.DashBehaviour.SPLIT:
            ws = w.split("-")
            for wi in ws:
                res = self._generate_compound(wi, wns_split)
                self._add_compound(comp, wi, res)
        else:
            res = self._generate_compound(w, wns_split)
            self._add_compound(comp, w, res)

    def _unknown_word_compounding(self, w: str) -> Tuple[str, Set[str]]:
        cands = set()
        for s in self.single_words:
            if s.lower() in w.lower() and not s.lower() == w.lower():
                cands.add(s)
        cands_new = set()
        for ci in cands:
            if not contained_in(ci, cands):
                cands_new.add(ci)
        res = self._generate_compound(w, cands_new)
        logging.debug(f"unknown1: {res}")
        if res is None:
            res = w
        else:
            res = self._append_suffix_and_prefix(res)
        logging.debug(f"unknown2: {res}")
        return (res, cands_new)

    def _get_highest_prob(self, compounds: Iterable[str]) -> Tuple[int, float]:
        probs = []
        for c in compounds:
            p = self._get_word_counts(c)
            probs.append(p)
        return get_max_idx(probs)

    def read_word_count(self, name: str) -> None:
        """
        Read the word counts from a file formatted in two tab-separated columns:
        the words in the first column, their count in the second.

        The file can be opened with gzip if it ends in '.gz'.
        """
        for i, l in enumerate(nopen(name)):
            try:
                ls = l.strip().split("\t")
                if len(ls) < 2:
                    logging.info(f"{name}:{i}: split error")
                    continue  # Don't crash on error-prone split
                wc = int(ls[1])
                self.word_count[ls[0]] = wc
                self.total_word_count += wc
            except UnicodeEncodeError as e:
                logging.info(f"{name}:{i}: ", e)

    def read_knowledge(self, name: str) -> None:
        """
        Read a list of words and its splitting candidates generated from a
        distributional thesaurus in a tab separated columns, the words in the first
        column, their splitting candidates in the following ones.

        The file can be opened with gzip if it ends in '.gz'.
        """
        for i, l in enumerate(nopen(name)):
            try:
                ls = l.rstrip("\n").split("\t")
                if len(ls) < 4:
                    logging.info(f"{name}:{i}: split error")
                    continue  # Don't crash on error-prone split
                w = ls[0]
                if not self._remove_word(w):
                    self._process_compound(self.comp1, w, ls[1])
                    self._process_compound(self.comp2, w, ls[2])
                    self._process_compound(self.comp3, w, ls[3])
            except UnicodeEncodeError as e:
                logging.info(f"{name}:{i}: ", e)

    def extract_single_words(self) -> None:
        """
        Extract single words from the first set of candidate splits extracted from the
        knowledge file.
        """
        for c in self.comp1:
            if "-" in self.comp1[c]:
                self.single_words |= set(self.comp1[c].split("-"))

    def prepare_decompounding(self, file_count: str, file_knowledge: str) -> None:
        """
        Calls read_word_count(file_count), read_knowledge(file_knowledge), and
        extract_single_words in that order to prepare for compound splitting.
        """
        logging.info("reading word count")
        self.read_word_count(file_count)
        logging.info("reading knowledge")
        self.read_knowledge(file_knowledge)
        logging.info("extracting single words")
        self.extract_single_words()

    def split_compound(self, w: str) -> Optional[str]:
        """
        Return the best split candidate for a given compound, or None
        if no good candidate was found.
        """
        c1 = self.comp1.get(w, w)
        c2 = self.comp2.get(w, w)
        c3 = self.comp3.get(w, w)
        (u, __) = self._unknown_word_compounding(w)
        cands = [c1, c2, c3, u]
        (idx, prob) = self._get_highest_prob(cands)
        if idx >= 0:
            return cands[idx]
        return None
