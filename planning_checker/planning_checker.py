#!/usr/bin/env python
from typing import List

import numpy as np

import duckietown_challenges as dc
from aido_schemas import FriendlyPose
from dt_protocols import (Circle, CollisionCheckQuery, logger, MapDefinition, Primitive,
                          protocol_collision_checking)
from zuper_nodes_wrapper.wrapper_outside import ComponentInterface


def get_time_series(N):
    t = np.linspace(0, 10, N)
    alpha = 0.1
    x = np.sin(alpha * t) + np.random.randn(N) * 0.1
    return x


def main(cie: dc.ChallengeInterfaceEvaluator):
    agent_ci = ComponentInterface(
        fnin="/fifos/checker-in",
        fnout="/fifos/checker-out",
        expect_protocol=protocol_collision_checking,
        nickname="checker",
    )

    # check compatibility so that everything
    # fails gracefully in case of error
    # noinspection PyProtectedMember
    agent_ci._get_node_protocol()

    environment: List[Primitive] = [
        Circle(x=1, y=2, radius=1)
    ]
    body = Circle(x=1, y=2, radius=1)
    map_definition = MapDefinition(environment, body)

    try:
        pose = FriendlyPose(0.0, 0.0, 90.0)
        query = CollisionCheckQuery(pose=pose)
        agent_ci.write_topic_and_expect_zero("set_map", map_definition)
        response = agent_ci.write_topic_and_expect("query", query, expect="response")
        logger.info(response=response)
        performance = 0.1
        cie.set_score("performance", performance)
    except dc.InvalidSubmission:
        raise
    except BaseException as e:
        raise dc.InvalidEvaluator() from e

    finally:
        agent_ci.close()


if __name__ == "__main__":
    with dc.scoring_context() as _:
        main(_)
