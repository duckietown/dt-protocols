#!/usr/bin/env python


import numpy as np

import duckietown_challenges as dc
from dt_protocols import protocol_collision_checking
from zuper_nodes_wrapper.wrapper_outside import ComponentInterface, MsgReceived


def get_time_series(N):
    t = np.linspace(0, 10, N)
    alpha = 0.1
    x = np.sin(alpha * t) + np.random.randn(N) * 0.1
    return x


def main(cie: dc.ChallengeInterfaceEvaluator):
    agent_ci = ComponentInterface(
        fnin="/fifos/predictor-in",
        fnout="/fifos/predictor-out",
        expect_protocol=protocol_collision_checking,
        nickname="predictor",
    )

    # check compatibility so that everything
    # fails gracefully in case of error
    # noinspection PyProtectedMember
    agent_ci._get_node_protocol()

    try:
        seed = 42
        agent_ci.write_topic_and_expect_zero("seed", seed)

        N = 100
        N_training = int(N / 2)

        values = get_time_series(200)

        values_training = values[:N_training]
        values_test = values[N_training:]
        for value in values_training:
            agent_ci.write_topic_and_expect_zero("observations", value)

        guess = []
        truth = []
        for value in values_test:
            msg_prediction: MsgReceived[float] = agent_ci.write_topic_and_expect(
                "get_prediction", None, expect="prediction"
            )

            guess.append(msg_prediction.data)

            truth.append(value)
            agent_ci.write_topic_and_expect_zero("observations", value)

        truth = np.array(truth)
        guess = np.array(guess)
        cie.info("truth: %s" % truth)
        cie.info("guess: %s" % guess)

        error_L1 = np.mean(np.abs(truth - guess))
        error_L2 = np.mean(np.power(truth - guess, 2))

        cie.set_score("error_L1", error_L1)
        cie.set_score("error_L2", error_L2)

        # cid = "QmUNeebf5AxDmhhEVaoz9dKWkS4n1djHsf765aZdW1ubgP"
        # cie.set_evaluation_ipfs_hash("logs", cid)
    except dc.InvalidSubmission:
        raise
    except BaseException as e:
        raise dc.InvalidEvaluator() from e

    finally:
        agent_ci.close()


if __name__ == "__main__":
    with dc.scoring_context() as _:
        main(_)
