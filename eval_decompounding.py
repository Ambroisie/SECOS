#! /usr/bin/env python3

# Use a testing dataset containing compound words to calculate precision, recall, F1

import sys
from typing import Set, Tuple, cast

from secos.eval import Evaluator


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


if len(sys.argv) < 3:
    eprint(
        f"cat compound_file | python {sys.argv[0]} "
        "column_predicted column_gold_compound"
    )
    sys.exit(1)
evaluator = Evaluator(col_split=int(sys.argv[1]), col_gold=int(sys.argv[2]))
evaluator.evaluate()
