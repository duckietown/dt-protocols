#!/usr/bin/env python3
import argparse

import numpy as np

import duckietown_challenges as dc
from dt_protocols import CollisionCheckResult, protocol_collision_checking
from dt_protocols.checker import run_checker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dirname", type=str, required=True)

    parsed = parser.parse_args()

    dirname = parsed.dirname

    def scoring(gt: CollisionCheckResult, given: CollisionCheckResult):
        return 1 if gt.collision == given.collision else 0

    def finalize_scores(x):
        return {"performance": np.mean(x)}

    with dc.scoring_context() as _:
        run_checker(
            _, protocol_collision_checking, dirname=dirname, scoring=scoring, finalize_scores=finalize_scores
        )


if __name__ == "__main__":
    main()
