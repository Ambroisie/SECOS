from typing import TextIO


class AbstractEvaluator:
    def evaluate(self, output: TextIO) -> None:
        raise NotImplementedError("Use a concrete evaluator")
