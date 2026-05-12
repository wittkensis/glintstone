"""Object storage abstraction with two backends: LocalFilesystem and R2.

Selected via the ``STORAGE_BACKEND`` env var (``local`` or ``r2``). The R2
backend talks to Cloudflare R2 via the S3-compatible API using boto3 — the
account ID, access keys, and bucket come from the env.

R2 secret handling: Cloudflare exposes two related strings for an R2 API
token — the raw ``cfat_…`` token value (what the dashboard / AI assistant
shows) and the actual S3 Secret Access Key, which is the SHA-256 hash of
that value in hex. We accept either: if a value starts with ``cfat_``, we
derive the real secret from it. See
https://developers.cloudflare.com/r2/api/tokens/

All backends expose the same minimal surface so the ingestion connector and
the API can stay backend-agnostic. Anything that needs richer behavior
(presigned URLs, versioning) goes here, not in the call sites.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from core.config import Settings, get_settings


def _resolve_r2_secret(value: str) -> str:
    """Return the S3 Secret Access Key, deriving it from a raw token value if needed."""
    if value.startswith("cfat_"):
        return hashlib.sha256(value.encode()).hexdigest()
    return value


@dataclass(frozen=True)
class PutResult:
    """Returned by ``Storage.put`` so callers can persist the object key and hash."""

    key: str
    sha256: str
    byte_size: int


class Storage(Protocol):
    """Minimal object storage interface."""

    def put(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: Optional[str] = None,
    ) -> PutResult: ...

    def exists(self, key: str) -> bool: ...

    def public_url(self, key: str) -> str: ...


# ---------------------------------------------------------------------------
# Local filesystem backend
# ---------------------------------------------------------------------------


class LocalFilesystemStorage:
    """Writes objects under a root directory. Used for tests and offline dev."""

    def __init__(self, root: Path, public_base_url: str = "/static/storage") -> None:
        self.root = root
        self.public_base = public_base_url.rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def put(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: Optional[str] = None,
    ) -> PutResult:
        del content_type, cache_control  # filesystem ignores headers
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return PutResult(key=key, sha256=_sha256(data), byte_size=len(data))

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()

    def public_url(self, key: str) -> str:
        return f"{self.public_base}/{key}"


# ---------------------------------------------------------------------------
# Cloudflare R2 backend (S3-compatible)
# ---------------------------------------------------------------------------


class R2Storage:
    """Uploads to Cloudflare R2 via the S3-compatible endpoint.

    Requires R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY in env.
    Bucket comes from R2_BUCKET. Public URLs use R2_PUBLIC_BASE_URL if set,
    otherwise fall back to the bucket's auto-assigned pub-<bucket>.r2.dev URL
    (which only works if the bucket has public access enabled in Cloudflare).
    """

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        s3_endpoint: str,
        public_base_url: Optional[str] = None,
    ) -> None:
        # boto3 is heavy — import lazily so test/dev environments without R2
        # don't pay the import cost.
        import boto3
        from botocore.config import Config

        self.bucket = bucket
        self.public_base = (
            public_base_url.rstrip("/")
            if public_base_url
            else f"https://pub-{bucket}.r2.dev"
        )
        # boto3 ≥1.36 enables default request/response checksum algorithms
        # that R2 doesn't support, breaking the sigv4 signature. Force them
        # to "when_required" (the pre-1.36 behavior). See
        # https://developers.cloudflare.com/r2/examples/aws/boto3/
        config = Config(
            signature_version="s3v4",
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        )
        self._client = boto3.client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=_resolve_r2_secret(secret_access_key),
            region_name="auto",
            config=config,
        )

    def put(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: Optional[str] = None,
    ) -> PutResult:
        extra: dict[str, str] = {"ContentType": content_type}
        if cache_control:
            extra["CacheControl"] = cache_control
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        return PutResult(key=key, sha256=_sha256(data), byte_size=len(data))

    def exists(self, key: str) -> bool:
        # head_object raises on 404; the S3 client surfaces that as a
        # ClientError we have to catch by error code.
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
                return False
            raise

    def public_url(self, key: str) -> str:
        return f"{self.public_base}/{key}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_storage(settings: Optional[Settings] = None) -> Storage:
    """Construct the configured storage backend.

    Resolution: read ``STORAGE_BACKEND`` from settings. If ``r2``, validate
    that all required credentials are present and instantiate R2Storage.
    If ``local``, instantiate LocalFilesystemStorage rooted at
    ``./var/storage`` (gitignored).
    """
    s = settings or get_settings()
    backend = s.storage_backend.lower().strip()
    if backend == "r2":
        # Prefer the explicit S3 endpoint (CLOUDFLARE_S3_ENDPOINT_URL) when
        # provided; otherwise build it from account_id. Account IDs are 32
        # hex chars — any other length is treated as malformed.
        s3_endpoint = s.r2_s3_endpoint
        if not s3_endpoint:
            account_id = (s.r2_account_id or "").strip()
            if len(account_id) != 32 or not all(
                c in "0123456789abcdefABCDEF" for c in account_id
            ):
                raise RuntimeError(
                    "STORAGE_BACKEND=r2 requires either R2_S3_ENDPOINT / "
                    "CLOUDFLARE_S3_ENDPOINT_URL, or a valid 32-hex-char "
                    "R2_ACCOUNT_ID / CLOUDFLARE_ACCOUNT_ID."
                )
            s3_endpoint = f"https://{account_id}.r2.cloudflarestorage.com"

        missing = [
            name
            for name, val in {
                "R2_ACCESS_KEY_ID / CLOUDFLARE_ACCESS_KEY_ID": s.r2_access_key_id,
                "R2_SECRET_ACCESS_KEY / CLOUDFLARE_SECRET_ACCESS_KEY": s.r2_secret_access_key,
            }.items()
            if not val
        ]
        if missing:
            raise RuntimeError(
                f"STORAGE_BACKEND=r2 but missing required env vars: {', '.join(missing)}"
            )
        return R2Storage(
            access_key_id=s.r2_access_key_id,
            secret_access_key=s.r2_secret_access_key,
            bucket=s.r2_bucket,
            s3_endpoint=s3_endpoint,
            public_base_url=s.r2_public_base_url,
        )
    if backend == "local":
        return LocalFilesystemStorage(root=Path("var/storage"))
    raise ValueError(f"unknown STORAGE_BACKEND: {backend!r}")


# ---------------------------------------------------------------------------
# Key helpers — centralized so connector + API stay in sync
# ---------------------------------------------------------------------------


def artifact_image_key(
    p_number: str,
    image_type: str,
    suffix: str,
    *,
    extension: str = "jpg",
    thumbnail: bool = False,
) -> str:
    """Object key for an artifact image. Keys are stable and human-debuggable.

    Layout: ``tablets/<P>/<type>-<suffix>.<ext>``, e.g.::

        tablets/P000001/photo-88909.jpg
        tablets/P000001/photo-88909-thumb.webp
    """
    base = f"tablets/{p_number}/{image_type}-{suffix}"
    if thumbnail:
        return f"{base}-thumb.webp"
    return f"{base}.{extension.lstrip('.')}"


def _sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()
