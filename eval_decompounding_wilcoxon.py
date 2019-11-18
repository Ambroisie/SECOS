#! /usr/bin/env python3

# Use a testing dataset containing compound words to calculate precision, recall, F1
# This one also reports the significance of each method (i.e: comparing performance)

import sys

import scipy.stats

from secos.eval import WilcoxonEvaluator


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


if len(sys.argv) < 7:
    eprint(
        "this script performs an evaluation of two methods for compound "
        "splitting and also computes a wilcoxon test based on the F measure "
        "for each compound"
    )
    eprint(
        f"python {sys.argv[0]} compound_1_file compound_1_column_predicted "
        "compound_1_column_gold compound_2_file "
        "compound_2_column_predicted compound_2_column_gold"
    )
    sys.exit(1)
evaluator = WilcoxonEvaluator(
    f1=sys.argv[1],
    f1_col_split=int(sys.argv[2]),
    f1_col_gold=int(sys.argv[3]),
    f2=sys.argv[4],
    f2_col_split=int(sys.argv[5]),
    f2_col_gold=int(sys.argv[6]),
)
try:
    evaluator.evaluate()
except WilcoxonEvaluator.InputError as e:  # When files are not the same length
    print(e, file=sys.stderr)
