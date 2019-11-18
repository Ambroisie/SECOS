#! /usr/bin/env python3

import logging
import sys
from dataclasses import dataclass
from typing import TextIO, Tuple, cast

import scipy.stats

from .abstract import AbstractEvaluator
from .common import evaluate


@dataclass
class WilcoxonEvaluator(AbstractEvaluator):
    class InputError(RuntimeError):
        """
        Error thrown when input files are not the same length
        """

        pass

    f1: str
    f1_col_split: int
    f1_col_gold: int
    f2: str
    f2_col_split: int
    f2_col_gold: int

    def evaluate(self, output: TextIO = sys.stdout) -> None:
        def printEval(scores: Tuple[float, float, float], a: float, c: float) -> None:
            k = scores
            print(scores, file=output)
            p = 1.0 * k[0] / (1.0 * k[0] + k[1])
            r = 1.0 * k[0] / (1.0 * k[0] + k[1] + k[2])
            f = 2 * p * r / (p + r)
            print(f"{p}\t{r}\t{f}", file=output)
            print(f"{a}\t{c}\t{c / a}", file=output)

        def computeEvalSc(k: Tuple[int, int, int]) -> Tuple[float, float, float]:
            p = 1.0 * k[0] / (1.0 * k[0] + k[1])
            r = 1.0 * k[0] / (1.0 * k[0] + k[1] + k[2])
            if k[0] == 0:
                f = 0.0
            else:
                f = 2 * p * r / (p + r)
            return (p, r, f)

        a1 = 0
        a2 = 0
        c1 = 0
        c2 = 0
        scores1 = (0.0, 0.0, 0.0)
        scores2 = (0.0, 0.0, 0.0)
        f1_lines = open(self.f1).readlines()
        f2_lines = open(self.f2).readlines()
        if len(f1_lines) != len(f2_lines):
            raise RuntimeError("Files do not have the same length")

        x1 = []
        x2 = []
        xd = []
        mcn = [[0, 0], [0, 0]]
        for i in range(0, len(f1_lines)):
            ls1 = f1_lines[i].strip().split("\t")
            ls2 = f2_lines[i].strip().split("\t")
            gold1 = ls1[self.f1_col_gold].lower()
            gold2 = ls2[self.f2_col_gold].lower()
            if gold1 != gold2:
                print(f"inequal: {gold1}\t{gold2}", file=output)
                print(f1_lines[i].strip(), file=output)
                print(f2_lines[i].strip(), file=output)
            cand1 = ls1[self.f1_col_split].lower()
            cand2 = ls2[self.f2_col_split].lower()
            sc1 = evaluate(gold1, cand1)
            sc2 = evaluate(gold2, cand2)
            e1 = computeEvalSc(sc1)
            e2 = computeEvalSc(sc2)
            logging.debug(f"{e1[2]}{e2[2]}{cand1}{cand2}{gold1}")
            x1.append(e1[2])
            x2.append(e2[2])
            xd.append(e2[2] - e1[2])
            scores1 = cast(
                Tuple[float, float, float], tuple(sum(x) for x in zip(scores1, sc1))
            )
            scores2 = cast(
                Tuple[float, float, float], tuple(sum(x) for x in zip(scores2, sc2))
            )
            flag1 = "0"
            flag2 = "0"
            i1 = 0
            i2 = 0
            if gold2 == cand2:
                flag2 = "1"
                c2 += 1
                i1 = 1
            if gold1 == cand1:
                flag1 = "1"
                c1 += 1
                i2 = 1
            mcn[i1][i2] += 1
            logging.debug(f"{flag1}\t{f1_lines[i].strip()}")
            logging.debug(f"{flag2}\t{f2_lines[i].strip()}")
            a1 += 1
            a2 += 1
        print(self.f1, file=output)
        printEval(scores1, a1, c1)
        print(self.f2, file=output)
        printEval(scores2, a2, c2)
        print("Wilcox", file=output)
        print(scipy.stats.wilcoxon(x1, y=x2, zero_method="wilcox"), file=output)
        print(scipy.stats.wilcoxon(x2, y=x1, zero_method="wilcox"), file=output)
        print("Wilcox2", file=output)
        print(scipy.stats.wilcoxon(xd, zero_method="wilcox"), file=output)
