from enum import Enum
from functools import lru_cache
from http import HTTPStatus

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.logger import logger
from pydantic import BaseSettings, BaseModel, Field
from ml_metadata import errors
from ml_metadata.proto import MetadataStoreClientConfig
from ml_metadata.metadata_store import MetadataStore
from ml_metadata.metadata_store import ListOptions


class Settings(BaseSettings):
    metadata_host: str = Field(..., env="KFP_ARTIFACT_API_METADATA_HOST")
    metadata_port: int = Field(..., env="KFP_ARTIFACT_API_METADATA_PORT")


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    logger.info("metadata host: %s", settings.metadata_host)
    logger.info("metadata port: %d", settings.metadata_port)
    return settings


def metadata_store(settings: Settings = Depends(get_settings)) -> MetadataStore:
    config = MetadataStoreClientConfig(
        host=settings.metadata_host,
        port=settings.metadata_port,
    )
    return MetadataStore(config)


@lru_cache()
def get_model_type_id(store: MetadataStore = Depends(metadata_store)):
    model_type = store.get_artifact_type("system.Model")
    return model_type.id


app = FastAPI()


class V1Alpha1Model(BaseModel):
    uri: str


class HealthStatus(Enum):
    Ok = "Ok"
    Degraded = "Degraded"


class V1Alpha1HealthCheck(BaseModel):
    connect_ok: bool = True
    metadata_connect_ok: bool = True
    status: HealthStatus = HealthStatus.Ok


class Error(BaseModel):
    message: str


@app.get("/api/healthz", response_model=V1Alpha1HealthCheck)
def healthz(store: MetadataStore = Depends(metadata_store)):
    hc = V1Alpha1HealthCheck()
    try:
        store.get_executions(list_options=ListOptions(limit=1))
    except errors.UnavailableError:
        hc.metadata_connect_ok = False
        hc.status = HealthStatus.Degraded
    return hc


@app.get(
    "/api/v1alpha1/model/{run_id}",
    response_model=V1Alpha1Model,
    responses={
        404: {"model": Error},
    }
)
def get_model(
    run_id: str,
    store: MetadataStore = Depends(metadata_store),
    model_type_id: int = Depends(get_model_type_id),
):

    contexts = store.get_contexts(list_options=ListOptions(
        limit=1,
        filter_query=f"name = {run_id}"
    ))
    if len(contexts) < 1:
        return JSONResponse(status_code=HTTPStatus.NOT_FOUND, content={"message": "Context for run_id not found"})

    context = contexts[0]
    artifacts = store.get_artifacts_by_context(context.id)

    for artifact in artifacts:
        if artifact.type_id == model_type_id:
            return V1Alpha1Model(uri=artifact.uri)

    return JSONResponse(
        status_code=HTTPStatus.NOT_FOUND,
        content={"message": "No model artifact found for provided run id"},
    )
