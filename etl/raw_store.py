"""Persist raw source payloads for reproducibility and provenance."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
from typing import Any


class RawStoreError(OSError):
    """Raised when a raw artifact cannot be published safely."""


_SENSITIVE_METADATA_KEY = re.compile(r"(?:api[-_]?key|token|authorization|password|credential|secret|cookie)", re.IGNORECASE)
_SENSITIVE_METADATA_VALUE = re.compile(r"(?:api[-_]?key|authorization|password|credential|secret|cookie)\s*[:=]", re.IGNORECASE)


def _validate_metadata_safety(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if _SENSITIVE_METADATA_KEY.search(str(key)):
                raise ValueError("raw metadata contains a prohibited sensitive field")
            _validate_metadata_safety(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _validate_metadata_safety(child)
    elif isinstance(value, str) and _SENSITIVE_METADATA_VALUE.search(value):
        raise ValueError("raw metadata contains a prohibited sensitive value")


def _write_temp_bytes(directory: Path, prefix: str, payload: bytes) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=directory)
    path = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        path.unlink(missing_ok=True)
        raise
    return path


def _publish_without_overwrite(source: Path, destination: Path) -> None:
    try:
        os.link(source, destination)
    except FileExistsError:
        raise
    except OSError as exc:
        raise RawStoreError("raw artifact publication failed") from exc
    source.unlink()


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _release_owned_lock(lock_path: Path, owner_token: str) -> None:
    """Release only a lock whose token still belongs to this writer."""
    try:
        if lock_path.read_text(encoding="ascii") == owner_token:
            lock_path.unlink()
    except (FileNotFoundError, PermissionError, UnicodeError):
        return


def write_raw_response(
    response_bytes: bytes,
    *,
    source_id: str,
    output_dir: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    """Write original response bytes and a separate provenance sidecar.

    The response body is never parsed or rewritten. Exclusive file creation
    prevents overwriting an existing artifact.
    """
    directory = Path(output_dir or os.getenv("RAW_DATA_DIR", "data/raw"))
    directory.mkdir(parents=True, exist_ok=True)
    _validate_metadata_safety(metadata or {})
    timestamp = datetime.now(timezone.utc)
    digest = hashlib.sha256(response_bytes).hexdigest()
    base = f"{source_id}_{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
    index = 0
    while True:
        suffix = "" if index == 0 else f"_{index}"
        body_path = directory / f"{base}{suffix}.json"
        metadata_path = directory / f"{base}{suffix}.metadata.json"
        lock_path = directory / f".{base}{suffix}.lock"
        owner_token = uuid.uuid4().hex
        try:
            with lock_path.open("x", encoding="ascii") as lock_handle:
                lock_handle.write(owner_token)
                lock_handle.flush()
                os.fsync(lock_handle.fileno())
        except FileExistsError:
            index += 1
            continue
        if body_path.exists() or metadata_path.exists():
            _release_owned_lock(lock_path, owner_token)
            index += 1
            continue
        body_temp: Path | None = None
        metadata_temp: Path | None = None
        try:
            body_temp = _write_temp_bytes(directory, f".{body_path.name}.", response_bytes)
            saved_metadata = dict(metadata or {})
            saved_metadata.setdefault("retrieval_timestamp", timestamp.isoformat())
            saved_metadata["downloaded_bytes"] = len(response_bytes)
            saved_metadata["sha256"] = digest
            saved_metadata["artifact_filename"] = body_path.name
            saved_metadata["publication_status"] = "complete"
            metadata_temp = _write_temp_bytes(
                directory,
                f".{metadata_path.name}.",
                json.dumps(saved_metadata, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
            )
            _publish_without_overwrite(body_temp, body_path)
            body_temp = None
            _fsync_directory(directory)
            _publish_without_overwrite(metadata_temp, metadata_path)
            metadata_temp = None
            _fsync_directory(directory)
            return body_path, metadata_path
        except FileExistsError as exc:
            raise RawStoreError("raw artifact destination already exists; no file was overwritten") from exc
        finally:
            if body_temp is not None:
                body_temp.unlink(missing_ok=True)
            if metadata_temp is not None:
                metadata_temp.unlink(missing_ok=True)
            _release_owned_lock(lock_path, owner_token)


def write_raw_snapshot(
    records: list[dict[str, Any]],
    *,
    source_id: str,
    output_dir: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Path:
    directory = Path(output_dir or os.getenv("RAW_DATA_DIR", "data/raw"))
    directory.mkdir(parents=True, exist_ok=True)
    _validate_metadata_safety(metadata or {})
    timestamp = datetime.now(timezone.utc)
    payload = {
        "source": source_id,
        "fetched_at": timestamp.isoformat(),
        "source_metadata": metadata or {},
        "records": records,
    }
    payload_bytes = json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    base = f"{source_id}_{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
    index = 0
    while True:
        suffix = "" if index == 0 else f"_{index}"
        destination = directory / f"{base}{suffix}.json"
        lock_path = directory / f".{base}{suffix}.lock"
        owner_token = uuid.uuid4().hex
        try:
            with lock_path.open("x", encoding="ascii") as lock_handle:
                lock_handle.write(owner_token)
                lock_handle.flush()
                os.fsync(lock_handle.fileno())
        except FileExistsError:
            index += 1
            continue
        if destination.exists():
            _release_owned_lock(lock_path, owner_token)
            index += 1
            continue
        temporary: Path | None = None
        try:
            temporary = _write_temp_bytes(directory, f".{destination.name}.", payload_bytes)
            _publish_without_overwrite(temporary, destination)
            temporary = None
            _fsync_directory(directory)
            return destination
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            _release_owned_lock(lock_path, owner_token)
