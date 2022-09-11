# encrypticoin-ssi

Service-Server-Integration library written in Python for use with the Etalon Token-Integration-API.

The API is made to be as simple as possible, so integration from any environment would be cheap and easy. This repository demonstrates the integration procedure for both "simple" and "tracking" workflows using a tiny mocked service-server and service-client.

## Compatibility

The library is tested with CPython 3.8, 3.9 and 3.10. It should work with PyPy3 as well, but there is a dependency needed for running the tests that is not available for it.

## Usage

The main feature of the library is the `ServerIntegrationClient` class. It implements a lightweight wrapper to the integration REST API using `aiohttp`.

**NOTE: The codes in the `encrypticoin_ssi_tests` directory are purposefully kept minimalistic and simple to highlight the functional parts of the procedures. For a production environment, several changes must be made to provide the necessary security and data persistence.** 

The `encrypticoin_ssi_tests/simple` directory holds the example/test of the simple workflow:
- `service_server/main.py` implements the server-side integration and a mock API for testing
- `service_client.py` implements a mock client that communicates with the service-server
- `test_workflow.py` takes all of them and performs a basic test procedure

The `encrypticoin_ssi_tests/tracking` directory holds the example/test of the tracking workflow:
- `service_server/main.py` implements the server-side integration and a mock API for testing and the token-tracking collector procedure
- `service_client.py` implements a mock client that communicates with the service-server
- `test_workflow.py` takes all of them and performs a basic test procedure

## Server API

The live server-API documentation is available at https://etalon.cash/tia/docs

## Install

A source distribution package is available from PyPI named `encrypticoin-ssi`:

```
pip install encrypticoin-ssi
```
