IMG ?= jackhoman/kfp-artifact-api:latest

KFP_ARTIFACT_API_METADATA_HOST ?= $(shell minikube ip)
KFP_ARTIFACT_API_METADATA_PORT ?= 30888

docker-build:
	docker build -t $(IMG) -f Dockerfile .

docker-push:
	docker push $(IMG)

run:
	KFP_ARTIFACT_API_METADATA_HOST=$(KFP_ARTIFACT_API_METADATA_HOST) \
	KFP_ARTIFACT_API_METADATA_PORT=$(KFP_ARTIFACT_API_METADATA_PORT) \
	    uvicorn main:app --host=0.0.0.0 --port=9999

console:
	KFP_ARTIFACT_API_METADATA_HOST=$(KFP_ARTIFACT_API_METADATA_HOST) \
	KFP_ARTIFACT_API_METADATA_PORT=$(KFP_ARTIFACT_API_METADATA_PORT) \
        python -i main.py

generate: oapi-codegen
	rm -rf /tmp/kfp-artifact-api
	mkdir /tmp/kfp-artifact-api
	rm -rf $(shell pwd)/client-go/generated
	mkdir $(shell pwd)/client-go/generated
	python -c "import src.main, json; print(json.dumps(src.main.app.openapi(), indent=4))" > /tmp/kfp-artifact-api/openapi-spec.json
	$(OAPI_CODEGEN) -generate client,types \
        -o $(shell pwd)/client-go/generated/api.go \
        -package generated \
        /tmp/kfp-artifact-api/openapi-spec.json


OAPI_CODEGEN = $(shell pwd)/bin/oapi-codegen

.PHONY: swagger
oapi-codegen:
	$(call go-get-tool,$(OAPI_CODEGEN),github.com/deepmap/oapi-codegen/cmd/oapi-codegen@latest)

# go-get-tool will 'go get' any package $2 and install it to $1.
PROJECT_DIR := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))
define go-get-tool
@[ -f $(1) ] || { \
set -e ;\
TMP_DIR=$$(mktemp -d) ;\
cd $$TMP_DIR ;\
go mod init tmp ;\
echo "Downloading $(2)" ;\
GOBIN=$(PROJECT_DIR)/bin go get $(2) ;\
rm -rf $$TMP_DIR ;\
}
endef
