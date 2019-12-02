from typing import TextIO


class AbstractEvaluator:
    """
    The abstract interface for an Evaluator.
    """

    def evaluate(self, output: TextIO) -> None:
        """
        Abstract method to evaluate the performance of SECOS on a given corpus.
        """
        raise NotImplementedError("Use a concrete evaluator")
