"""
Stage 2 Extension Harness — Manifest Validation & Storage.

Every extension MUST ship a validated manifest before it can be registered.
The manifest pins the extension to an exact baseline and declares the
state-schema / hook-contract versions it implements.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from .errors import ManifestValidationError
from .protocol import (
    VALID_EXTENSION_STATUSES,
    VALID_RANDOMNESS_POLICIES,
)

# Classic semver: MAJOR.MINOR.PATCH with optional pre-release suffix.
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

# Exactly 64 lowercase hex characters.
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def _validate_semver(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _SEMVER_RE.match(value):
        raise ManifestValidationError(
            f"{field_name!r} must be a semver string (e.g. '0.1.0'), got {value!r}"
        )


def _validate_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _SHA256_HEX_RE.match(value):
        raise ManifestValidationError(
            f"{field_name!r} must be a 64-character lowercase hex string, got {value!r}"
        )


def _validate_positive_int(value: int, field_name: str) -> None:
    if not isinstance(value, int) or value < 1:
        raise ManifestValidationError(
            f"{field_name!r} must be a positive integer, got {value!r}"
        )


class ExtensionManifest:
    """
    Validated, immutable extension manifest.

    Create directly or via ``from_dict()``; either path runs the same
    validation suite and raises ``ManifestValidationError`` on failure.
    """

    __slots__ = (
        "extension_id",
        "extension_name",
        "extension_version",
        "status",
        "base_system",
        "required_base_source_sha256",
        "required_base_package_manifest_sha256",
        "author",
        "purpose",
        "claim_boundary",
        "state_schema_version",
        "hook_contract_version",
        "randomness_policy",
        "created_timestamp",
    )

    def __init__(
        self,
        extension_id: str,
        extension_name: str,
        extension_version: str,
        status: str,
        base_system: str,
        required_base_source_sha256: str,
        required_base_package_manifest_sha256: str,
        author: str,
        purpose: str,
        claim_boundary: str,
        state_schema_version: int,
        hook_contract_version: int,
        randomness_policy: str,
        created_timestamp: Optional[str] = None,
    ) -> None:
        # ── Validate ──────────────────────────────────────────────
        if not isinstance(extension_id, str) or not extension_id.strip():
            raise ManifestValidationError("extension_id must be a non-empty string")
        if not isinstance(extension_name, str) or not extension_name.strip():
            raise ManifestValidationError("extension_name must be a non-empty string")
        _validate_semver(extension_version, "extension_version")

        if status not in VALID_EXTENSION_STATUSES:
            raise ManifestValidationError(
                f"status must be one of {sorted(VALID_EXTENSION_STATUSES)}, got {status!r}"
            )

        if not isinstance(base_system, str):
            raise ManifestValidationError("base_system must be a string")

        _validate_sha256(required_base_source_sha256, "required_base_source_sha256")
        _validate_sha256(
            required_base_package_manifest_sha256,
            "required_base_package_manifest_sha256",
        )

        if not isinstance(author, str):
            raise ManifestValidationError("author must be a string")
        if not isinstance(purpose, str):
            raise ManifestValidationError("purpose must be a string")
        if not isinstance(claim_boundary, str):
            raise ManifestValidationError("claim_boundary must be a string")

        _validate_positive_int(state_schema_version, "state_schema_version")
        _validate_positive_int(hook_contract_version, "hook_contract_version")

        if randomness_policy not in VALID_RANDOMNESS_POLICIES:
            raise ManifestValidationError(
                f"randomness_policy must be one of {sorted(VALID_RANDOMNESS_POLICIES)}, "
                f"got {randomness_policy!r}"
            )

        if created_timestamp is not None and not isinstance(created_timestamp, str):
            raise ManifestValidationError("created_timestamp must be a string or None")

        # ── Store ─────────────────────────────────────────────────
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.extension_version = extension_version
        self.status = status
        self.base_system = base_system
        self.required_base_source_sha256 = required_base_source_sha256
        self.required_base_package_manifest_sha256 = required_base_package_manifest_sha256
        self.author = author
        self.purpose = purpose
        self.claim_boundary = claim_boundary
        self.state_schema_version = state_schema_version
        self.hook_contract_version = hook_contract_version
        self.randomness_policy = randomness_policy
        self.created_timestamp = created_timestamp

    # ── Factory ───────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "ExtensionManifest":
        """
        Construct a validated manifest from a raw dictionary.

        Required keys:
            extension_id, extension_name, extension_version, status,
            base_system, required_base_source_sha256,
            required_base_package_manifest_sha256, author, purpose,
            claim_boundary, state_schema_version, hook_contract_version,
            randomness_policy

        Raises ManifestValidationError if any key is missing, has the
        wrong type, or violates validation rules.
        """
        if not isinstance(data, dict):
            raise ManifestValidationError("data must be a dict")

        required_keys = {
            "extension_id",
            "extension_name",
            "extension_version",
            "status",
            "base_system",
            "required_base_source_sha256",
            "required_base_package_manifest_sha256",
            "author",
            "purpose",
            "claim_boundary",
            "state_schema_version",
            "hook_contract_version",
            "randomness_policy",
        }
        missing = required_keys - data.keys()
        if missing:
            raise ManifestValidationError(
                f"Missing required keys: {sorted(missing)}"
            )

        return cls(
            extension_id=data["extension_id"],
            extension_name=data["extension_name"],
            extension_version=data["extension_version"],
            status=data["status"],
            base_system=data["base_system"],
            required_base_source_sha256=data["required_base_source_sha256"],
            required_base_package_manifest_sha256=data["required_base_package_manifest_sha256"],
            author=data["author"],
            purpose=data["purpose"],
            claim_boundary=data["claim_boundary"],
            state_schema_version=data["state_schema_version"],
            hook_contract_version=data["hook_contract_version"],
            randomness_policy=data["randomness_policy"],
            created_timestamp=data.get("created_timestamp"),
        )

    # ── Serialisation ─────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Return the manifest as a dictionary (suitable for JSON)."""
        result: dict[str, Any] = {
            "extension_id": self.extension_id,
            "extension_name": self.extension_name,
            "extension_version": self.extension_version,
            "status": self.status,
            "base_system": self.base_system,
            "required_base_source_sha256": self.required_base_source_sha256,
            "required_base_package_manifest_sha256": self.required_base_package_manifest_sha256,
            "author": self.author,
            "purpose": self.purpose,
            "claim_boundary": self.claim_boundary,
            "state_schema_version": self.state_schema_version,
            "hook_contract_version": self.hook_contract_version,
            "randomness_policy": self.randomness_policy,
        }
        if self.created_timestamp is not None:
            result["created_timestamp"] = self.created_timestamp
        return result

    def __repr__(self) -> str:
        return (
            f"ExtensionManifest(id={self.extension_id!r}, "
            f"version={self.extension_version!r}, status={self.status!r})"
        )
