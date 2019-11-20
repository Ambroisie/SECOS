import logging
import sys
from dataclasses import dataclass
from typing import TextIO

from .abstract import AbstractEvaluator
from .common import EvalResult, evaluate


@dataclass
class Evaluator(AbstractEvaluator):
    col_split: int
    col_gold: int
    input: TextIO = sys.stdin

    def evaluate(self, output: TextIO = sys.stdout) -> None:
        a = 0
        c = 0
        scores = EvalResult(0, 0, 0)
        for l in self.input:
            ls = l.strip().split("\t")
            if len(ls) < self.col_gold or len(ls) < self.col_split:
                logging.debug(f"Line too short\n{l}")
            gold = ls[self.col_gold].lower()
            cand = ls[self.col_split].lower()
            scores = EvalResult(*(sum(x) for x in zip(scores, evaluate(gold, cand))))
            flag = "0"
            if gold == cand:
                flag = "1"
                c += 1
            logging.debug(f"{flag}\t{l.strip()}")
            a += 1
        p = scores.correct / (scores.correct + scores.wrong)
        r = (scores.correct ** 2) / sum(scores)
        f = 2 * p * r / (p + r)
        print("Precision\tRecall\tF1\n", file=output)
        print(f"{p}{r}{f}", file=output)
        print(f"{p:10.4f} & {r:10.4f}&{f:10.4f}", file=output)
        print("Considered\tCorrect\tPercentage of Correct ones", file=output)
        print(f"{a}\t{c}\t{c / a}", file=output)
