ARG AIDO_REGISTRY
FROM ${AIDO_REGISTRY}/duckietown/aido-base-python3:daffy-amd64

ARG PIP_INDEX_URL
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

RUN python -m pip install -U "pip>=20.2"
COPY requirements.* ./
RUN cat requirements.* > .requirements.txt
RUN  python -m pip install  -r .requirements.txt


COPY . .

RUN node-launch --help
RUN python -m pip list

ENTRYPOINT ["node-launch", "--node", "dummy_collision_checker.DummyCollisionChecker", "--protocol", "dt_protocols.protocol_collision_checking"]
