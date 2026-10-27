# senec-connect-api

An asynchronous Python client for SENEC.Connect. The client uses a caller-provided `aiohttp.ClientSession` and returns the API's general system data without translating it into application-specific concepts.

## Usage

```python
import asyncio

from aiohttp import ClientSession
from senec_connect_api import SenecClient


async def main() -> None:
    async with ClientSession() as session:
        client = SenecClient("your-subscription-key", session)
        systems = await client.async_get_device_data()
        print(systems)


asyncio.run(main())
```

The caller owns the session lifecycle. `SenecAuthError` identifies rejected credentials, `SenecConnectionError` indicates a network failure, and `SenecApiError` indicates an API or response-data error.

## Development

```bash
python -m pip install -e '.[test]'
pytest
ruff check .
ruff format --check .
```

Releases are tagged with the same version published to PyPI. To publish:

1. Configure a PyPI pending publisher for project `senec-connect-api`, GitHub owner `MiHechtel`, repository `senec-connect-api`, workflow `publish.yaml`, and environment `pypi`.
2. Create the GitHub `pypi` environment.
3. Publish a GitHub release using a `v`-prefixed tag matching the version in `pyproject.toml` (for example, `v0.1.0`).

The release workflow builds the wheel and source distribution, then publishes them through PyPI Trusted Publishing. It needs no PyPI API token.
