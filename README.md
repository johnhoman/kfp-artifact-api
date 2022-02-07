# KFP Artifact Server

A http translation layer from [ml-metadata] to a rest api so
that I can talk to it with a golang client from a controller


## Endpoints

### GET /api/v1alpha1/model/{run-id}

Gets the model uri for a run 



[ml-metadata]: https://github.com/google/ml-metadata
