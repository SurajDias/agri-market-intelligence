"""Source adapters for agricultural market data.

The default adapter targets the official data.gov.in AGMARKNET resource. A
credential is required and is read only from the environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
import socket
import inspect
from typing import Any, Protocol
from urllib.parse import urlsplit

import requests


DEFAULT_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
DEFAULT_API_URL = "https://api.data.gov.in/resource"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_PAGE_SIZE = 1000
OFFICIAL_API_HOST = "api.data.gov.in"


class SourceAccessError(RuntimeError):
    """Raised when a configured source cannot be queried."""


@dataclass(frozen=True)
class PreflightResult:
    hostname: str
    dns_status: str
    https_status: str
    http_status: int | None = None
    detail: str | None = None

    @property
    def available(self) -> bool:
        return self.dns_status == "success" and self.https_status == "success"


@dataclass(frozen=True)
class ValidatedAcquisition:
    records: list[dict[str, Any]]
    raw_bytes: bytes
    source_url: str
    resource_id: str
    request_parameters: dict[str, Any]
    http_status: int
    content_type: str
    retrieved_at: datetime


class PriceSourceAdapter(Protocol):
    source_id: str

    def fetch_records(self, *, limit: int = 1000, offset: int = 0, filters: dict[str, str] | None = None) -> list[dict[str, Any]]:
        ...


@dataclass(frozen=True)
class DataGovInConfig:
    api_key: str
    resource_id: str = DEFAULT_RESOURCE_ID
    api_url: str = DEFAULT_API_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    price_unit: str | None = None

    @classmethod
    def from_environment(cls, *, require_api_key: bool = True) -> "DataGovInConfig":
        api_key = os.getenv("DATA_GOV_IN_API_KEY", "").strip()
        if require_api_key and not api_key:
            raise SourceAccessError(
                "DATA_GOV_IN_API_KEY is not configured; obtain an API key from data.gov.in"
            )
        timeout_raw = os.getenv("DATA_GOV_IN_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)).strip()
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise SourceAccessError("DATA_GOV_IN_TIMEOUT_SECONDS must be a positive number") from None
        if timeout_seconds <= 0:
            raise SourceAccessError("DATA_GOV_IN_TIMEOUT_SECONDS must be a positive number")
        return cls(
            api_key=api_key,
            resource_id=os.getenv("DATA_GOV_IN_RESOURCE_ID", DEFAULT_RESOURCE_ID).strip(),
            api_url=os.getenv("DATA_GOV_IN_API_URL", DEFAULT_API_URL).rstrip("/"),
            timeout_seconds=timeout_seconds,
            price_unit=os.getenv("DATA_GOV_IN_PRICE_UNIT", "").strip() or None,
        )


def validate_official_config(config: DataGovInConfig) -> None:
    """Reject endpoint overrides outside the documented official API host."""
    parsed = urlsplit(config.api_url)
    if parsed.scheme != "https" or parsed.hostname != OFFICIAL_API_HOST or parsed.path.rstrip("/") != "/resource":
        raise SourceAccessError("configured API URL is not the official data.gov.in resource endpoint")
    if config.resource_id != DEFAULT_RESOURCE_ID:
        raise SourceAccessError("configured resource ID does not match the official mandi resource")


def _network_failure_status(exc: Exception) -> str:
    if isinstance(exc, requests.exceptions.SSLError):
        return "tls_failure"
    if isinstance(exc, requests.exceptions.Timeout):
        return "timeout"
    message = str(exc).casefold()
    if any(token in message for token in ("name or service not known", "could not resolve", "nodename nor servname", "gaierror")):
        return "dns_failure"
    if "connection refused" in message or "failed to establish a new connection" in message:
        return "connection_refused"
    return "connection_failure"


def _new_no_retry_session() -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=0)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _get_without_redirects(session: Any, endpoint: str, *, params: dict[str, Any], timeout: float) -> Any:
    """Pass the redirect guard to requests and remain compatible with old test doubles."""
    parameters = inspect.signature(session.get).parameters
    if "allow_redirects" in parameters or any(parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()):
        return session.get(endpoint, params=params, timeout=timeout, allow_redirects=False)
    return session.get(endpoint, params=params, timeout=timeout)


def run_preflight(
    config: DataGovInConfig,
    *,
    session: requests.Session | None = None,
    resolver: Any = socket.getaddrinfo,
) -> PreflightResult:
    """Perform one DNS check and, only after success, one unauthenticated HTTPS check."""
    validate_official_config(config)
    hostname = urlsplit(config.api_url).hostname or ""
    try:
        resolver(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return PreflightResult(hostname, "dns_failure", "not_attempted", detail="DNS resolution failed")
    except OSError as exc:
        return PreflightResult(hostname, "dns_failure", "not_attempted", detail="DNS resolution failed")

    client = session or _new_no_retry_session()
    try:
        response = client.get(config.api_url, timeout=config.timeout_seconds, allow_redirects=False)
        if response.status_code >= 400:
            return PreflightResult(hostname, "success", "http_error", response.status_code, f"HTTP status {response.status_code}")
        return PreflightResult(hostname, "success", "success", response.status_code, None)
    except requests.RequestException as exc:
        return PreflightResult(hostname, "success", _network_failure_status(exc), detail=_network_failure_status(exc))


def _content_type(response: requests.Response) -> str:
    return response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()


def _validate_response_identity(payload: dict[str, Any], resource_id: str) -> None:
    for key in ("resource_id", "resourceid", "resourceId"):
        value = payload.get(key)
        if value not in (None, "") and str(value) != resource_id:
            raise SourceAccessError("data.gov.in response resource identity does not match the configured resource")


def _validated_records(payload: Any, resource_id: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise SourceAccessError("data.gov.in response was not a JSON object")
    _validate_response_identity(payload, resource_id)
    records = payload.get("records")
    if not isinstance(records, list):
        raise SourceAccessError("data.gov.in response did not contain a records array")
    malformed_count = sum(not isinstance(record, dict) for record in records)
    if malformed_count:
        raise SourceAccessError(f"data.gov.in response contained {malformed_count} non-object record(s)")
    return records


class DataGovInAgmarknetAdapter:
    """Adapter for the official daily AGMARKNET mandi-price resource."""

    source_id = "data_gov_in_agmarknet_daily_prices"
    source_name = "data.gov.in AGMARKNET daily mandi prices"
    source_url = "https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi"

    def __init__(self, config: DataGovInConfig | None = None, session: requests.Session | None = None):
        self.config = config or DataGovInConfig.from_environment()
        self.session = session or _new_no_retry_session()

    def fetch_records(
        self,
        *,
        limit: int = 1000,
        offset: int = 0,
        filters: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise SourceAccessError(f"limit must be between 1 and {MAX_PAGE_SIZE}")
        if offset < 0:
            raise SourceAccessError("offset must be zero or greater")
        params: dict[str, Any] = {
            "api-key": self.config.api_key,
            "format": "json",
            "limit": limit,
            "offset": offset,
        }
        for key, value in (filters or {}).items():
            params[f"filters[{key}]"] = value

        endpoint = f"{self.config.api_url}/{self.config.resource_id}"
        public_error: SourceAccessError | None = None
        try:
            response = _get_without_redirects(self.session, endpoint, params=params, timeout=self.config.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            public_error = SourceAccessError(f"data.gov.in request failed with HTTP status {status}")
        except requests.RequestException as exc:
            public_error = SourceAccessError(f"data.gov.in request failed ({type(exc).__name__})")
        except ValueError as exc:
            public_error = SourceAccessError("data.gov.in returned a non-JSON response")
        if public_error is not None:
            raise public_error

        records = payload.get("records") if isinstance(payload, dict) else None
        if not isinstance(records, list):
            raise SourceAccessError("data.gov.in response did not contain a records array")
        malformed_count = sum(not isinstance(record, dict) for record in records)
        if malformed_count:
            raise SourceAccessError(
                f"data.gov.in response contained {malformed_count} non-object record(s)"
            )
        return records

    def fetch_validated_response(
        self,
        *,
        limit: int = 5,
        offset: int = 0,
        filters: dict[str, str] | None = None,
    ) -> ValidatedAcquisition:
        """Fetch one bounded JSON response for the operator workflow.

        This method does not retry, follow redirects, write files, or access a
        database. The existing fetch_records behavior remains unchanged.
        """
        validate_official_config(self.config)
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise SourceAccessError(f"limit must be between 1 and {MAX_PAGE_SIZE}")
        if offset < 0:
            raise SourceAccessError("offset must be zero or greater")
        params: dict[str, Any] = {
            "api-key": self.config.api_key,
            "format": "json",
            "limit": limit,
            "offset": offset,
        }
        for key, value in (filters or {}).items():
            params[f"filters[{key}]"] = value
        safe_params = {key: value for key, value in params.items() if key != "api-key"}
        endpoint = f"{self.config.api_url}/{self.config.resource_id}"
        public_error: SourceAccessError | None = None
        try:
            response = self.session.get(endpoint, params=params, timeout=self.config.timeout_seconds, allow_redirects=False)
            response.raise_for_status()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            public_error = SourceAccessError(f"data.gov.in request failed with HTTP status {status}")
        except requests.RequestException as exc:
            public_error = SourceAccessError(f"data.gov.in request failed ({type(exc).__name__})")
        if public_error is not None:
            raise public_error

        content_type = _content_type(response)
        if content_type not in {"application/json", "application/json; charset=utf-8"} and not content_type.endswith("+json"):
            raise SourceAccessError("data.gov.in response was not JSON; possible HTML/error response")
        raw_bytes = response.content
        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise SourceAccessError("data.gov.in returned malformed JSON") from None
        records = _validated_records(payload, self.config.resource_id)
        return ValidatedAcquisition(
            records=records,
            raw_bytes=raw_bytes,
            source_url=endpoint,
            resource_id=self.config.resource_id,
            request_parameters=safe_params,
            http_status=response.status_code,
            content_type=content_type,
            retrieved_at=datetime.now(timezone.utc),
        )
