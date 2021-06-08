AIDO_REGISTRY ?= docker.io
PIP_INDEX_URL ?= https://pypi.org/simple

repo=aidonode-dummy_image_source2
# repo=$(shell basename -s .git `git config --get remote.origin.url`)
branch=$(shell git rev-parse --abbrev-ref HEAD)
tag=$(AIDO_REGISTRY)/duckietown/$(repo):$(branch)

build_options=\
 	--build-arg AIDO_REGISTRY=$(AIDO_REGISTRY)\
 	--build-arg PIP_INDEX_URL=$(PIP_INDEX_URL)

update-reqs:
	pur --index-url $(PIP_INDEX_URL) -r requirements.txt -f -m '*' -o requirements.resolved
	dt-update-reqs requirements.resolved

build: update-reqs
	docker build --pull -t $(tag) $(build_options) .

build-no-cache: update-reqs
	docker build --pull -t $(tag)  $(build_options)  --no-cache .

push: build
	dts build_utils push $(tag)

test-data1-direct:
	./dummy_image_filter.py < test_data/in1.json > test_data/out1.json

test-data1-docker:
	docker run -i $(tag) < test_data/in1.json > test_data/out1.json


test-data1-direct-more:
	cat  test_data/in1.json | \
		./dummy_image_filter.py --name node1  | \
		./dummy_image_filter.py --name node2  \
		> test_data/out1.json

%.cbor: %.jsonl
	json2cbor < $< > $@

test: test_data/in1.cbor
	node-launch \
		--protocol dt_protocols.protocol_collision_checking \
		--node 	dummy_collision_checker.DummyCollisionChecker < test_data/in1.cbor
