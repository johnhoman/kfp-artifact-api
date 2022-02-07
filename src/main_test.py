import uuid

from ml_metadata import metadata_store
from ml_metadata.proto import metadata_store_pb2, ArtifactType, Artifact, Attribution, ContextType, Context
from fastapi import Depends
from fastapi.testclient import TestClient

from src import main


client = TestClient(main.app)


def override_settings():
    return main.Settings(metadata_host="", metadata_port=12345)


run_id = str(uuid.uuid4())
model_uri = "minio://pipelines-bucket/12345/model"


def override_metadata_store(settings: main.Settings = Depends(override_settings)):

    connection_config = metadata_store_pb2.ConnectionConfig()
    connection_config.fake_database.SetInParent() # Sets an empty fake database proto.
    store = metadata_store.MetadataStore(connection_config)

    context_type = ContextType()
    context_type.name = "system.PipelineRun"
    context_type_id = store.put_context_type(context_type)

    context = Context()
    context.type_id = context_type_id
    context.name = run_id
    [context_id] = store.put_contexts([context])

    artifact_type = ArtifactType()
    artifact_type.name = "system.Model"
    artifact_type_id = store.put_artifact_type(artifact_type)

    artifact = Artifact()
    artifact.type_id = artifact_type_id
    artifact.uri = model_uri
    [artifact_id] = store.put_artifacts([artifact])

    attribution = Attribution()
    attribution.artifact_id = artifact_id
    attribution.context_id = context_id
    store.put_attributions_and_associations([attribution], [])

    return store


main.app.dependency_overrides[main.metadata_store] = override_metadata_store
main.app.dependency_overrides[main.get_settings] = override_settings


def test_healthz():
    response = client.get("/api/healthz")
    assert response.status_code == 200


def test_get_model():
    response = client.get(f"/api/v1alpha1/model/{run_id}")
    assert response.status_code == 200
    assert response.json().get("uri") == model_uri


def test_get_model_returns_404_when_not_found():
    response = client.get(f"/api/v1alpha1/model/{uuid.uuid4()}")
    assert response.status_code == 404
    assert "not found" in response.json().get("message", "").lower()

