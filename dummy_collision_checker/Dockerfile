ARG DOCKER_REGISTRY
ARG ARCH=amd64
ARG MAJOR=daffy
ARG BASE_TAG=${MAJOR}-${ARCH}
FROM ${DOCKER_REGISTRY}/duckietown/aido-base-python3:${BASE_TAG}

ARG PIP_INDEX_URL="https://pypi.org/simple/"
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

COPY requirements.* ./
RUN cat requirements.* > .requirements.txt
RUN python3 -m pip install  -r .requirements.txt


COPY . .

RUN node-launch --help
RUN python3 -m pip list

ENTRYPOINT ["node-launch", "--node", "dummy_collision_checker.DummyCollisionChecker", "--protocol", "dt_protocols.protocol_collision_checking"]
