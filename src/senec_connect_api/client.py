"""Client for the SENEC.Connect cloud API."""

from typing import Any, NotRequired, TypedDict, cast

from aiohttp import ClientError, ClientSession

API_URL = (
    "https://apim-eds-gwc-prod.azure-api.net/senec-connect"
    "/v1/systems/device-data/general"
)


class BatteryData(TypedDict, total=False):
    """Battery data returned by SENEC.Connect."""

    state: int
    state_of_charge: int
    power: float
    voltage: float
    current: float


class BessNameplateData(TypedDict, total=False):
    """Battery system nameplate data returned by SENEC.Connect."""

    manufacturer: str
    model: str
    serial_number: str
    design_capacity: int
    active_charge_power: int
    active_discharge_power: int


class MeterData(TypedDict, total=False):
    """Meter data returned by SENEC.Connect."""

    grid_power: float
    consumption: float
    production: float


class GeneralDeviceData(TypedDict):
    """General system data returned by SENEC.Connect."""

    battery: NotRequired[BatteryData]
    bessNameplate: NotRequired[BessNameplateData]
    meter: NotRequired[MeterData]


class SenecError(Exception):
    """Base exception for SENEC.Connect API errors."""


class SenecAuthError(SenecError):
    """Raised when SENEC.Connect rejects the subscription key."""


class SenecConnectionError(SenecError):
    """Raised when the SENEC.Connect API cannot be reached."""


class SenecApiError(SenecError):
    """Raised when SENEC.Connect returns an error or invalid data."""


class SenecClient:
    """Make authenticated requests to the SENEC.Connect API."""

    def __init__(self, api_key: str, session: ClientSession) -> None:
        """Initialize the client with an API subscription key and shared session."""
        self._api_key = api_key
        self._session = session

    async def async_get_device_data(self) -> list[GeneralDeviceData]:
        """Return general data for all systems associated with the subscription."""
        try:
            response = await self._session.get(
                API_URL,
                headers={"Ocp-Apim-Subscription-Key": self._api_key},
            )
        except (ClientError, TimeoutError) as err:
            raise SenecConnectionError from err

        async with response:
            if response.status in (401, 403):
                raise SenecAuthError
            if response.status >= 400:
                raise SenecApiError(f"SENEC.Connect API error: {response.status}")

            try:
                data: Any = await response.json()
            except (ClientError, ValueError) as err:
                raise SenecApiError("Invalid response from SENEC.Connect API") from err

        if not isinstance(data, list) or not data:
            raise SenecApiError("No SENEC systems returned")

        serial_numbers: set[str] = set()
        for system in data:
            if not isinstance(system, dict) or not isinstance(
                nameplate := system.get("bessNameplate"), dict
            ):
                raise SenecApiError("Missing SENEC system identity")
            serial = nameplate.get("serial_number")
            if (
                not isinstance(serial, str)
                or not serial.strip()
                or serial in serial_numbers
            ):
                raise SenecApiError("Invalid or duplicate SENEC serial number")
            serial_numbers.add(serial)

        return cast(list[GeneralDeviceData], data)
