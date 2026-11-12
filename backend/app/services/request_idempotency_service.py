import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.inventory import InventoryCreateRequest


class RequestIdempotencyService:
    """Coordinates client request keys within the caller's source transaction."""

    LOCK_NAMESPACE = 360362

    def __init__(self, db: Session):
        self.db = db

    @classmethod
    def _canonical_value(cls, value):
        if isinstance(value, Decimal):
            return format(value.normalize(), "f") if value else "0"
        if isinstance(value, datetime):
            if value.utcoffset() is not None:
                return value.astimezone(timezone.utc).isoformat()
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {key: cls._canonical_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._canonical_value(item) for item in value]
        return value

    @classmethod
    def payload_hash(cls, payload, organization_id: int) -> str:
        data = payload.model_dump(mode="python")
        # Omitted organization_id and an explicit matching ID mean the same request.
        if "organization_id" in data:
            data["organization_id"] = organization_id
        canonical = json.dumps(
            cls._canonical_value(data), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def find_existing(
        self, organization_id: int, operation: str, key: str | None, payload_hash: str
    ) -> InventoryCreateRequest | None:
        if key is None:
            return None
        key = key.strip()
        if not key or len(key) > 128:
            raise HTTPException(400, "Idempotency-Key must contain 1 to 128 characters")

        if self.db.get_bind().dialect.name == "postgresql":
            scoped_key = f"{organization_id}:{operation}:{key}"
            self.db.execute(
                text("SELECT pg_advisory_xact_lock(:namespace, hashtext(:request_key))"),
                {"namespace": self.LOCK_NAMESPACE, "request_key": scoped_key},
            )

        existing = self.db.get(
            InventoryCreateRequest,
            (organization_id, operation, key),
            with_for_update=True,
        )
        if existing is not None and existing.payload_hash != payload_hash:
            raise HTTPException(
                409,
                "Idempotency-Key was already used for a different request payload",
            )
        return existing

    def store(
        self,
        organization_id: int,
        operation: str,
        key: str | None,
        payload_hash: str,
        source_id: int,
    ) -> None:
        if key is None:
            return
        self.db.add(InventoryCreateRequest(
            organization_id=organization_id,
            operation=operation,
            idempotency_key=key.strip(),
            payload_hash=payload_hash,
            source_id=source_id,
        ))
        self.db.flush()
