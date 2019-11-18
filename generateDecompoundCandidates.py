#! /usr/bin/env python3

# Training new decompounding models using a distributional thesaurus from JoBimText

import logging
import sys

from secos import Trainer

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)

trainer = Trainer(
    pattern=sys.argv[1] if len(sys.argv) > 1 else ".*",
    split_dash=True if len(sys.argv) > 2 else False,
)

trainer.train()
