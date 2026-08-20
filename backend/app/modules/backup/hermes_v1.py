import base64
import binascii
import json
import secrets
from datetime import UTC
from typing import Any

from argon2.low_level import ARGON2_VERSION, Type, hash_secret_raw
from nacl.exceptions import CryptoError
from nacl.secret import Aead
from pydantic import ValidationError

from app.modules.backup.errors import (
    BackupAuthenticationFailed,
    BackupTooLarge,
    InvalidBackupPayload,
    InvalidHermesFile,
    InvalidKdfParameters,
    UnsupportedHermesVersion,
)
from app.modules.backup.schemas import (
    BackupDocument,
    HermesBackup,
    HermesKdf,
    HermesKeyEncryption,
    HermesPayload,
    HermesPayloadEncryption,
)

HERMES_FORMAT = "hermes"
HERMES_VERSION = 1
AEAD_ALGORITHM = "xchacha20-poly1305-ietf"

ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65_536
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16

MIN_TIME_COST = 3
MAX_TIME_COST = 6
MIN_MEMORY_COST = 65_536
MAX_MEMORY_COST = 262_144
MIN_PARALLELISM = 1
MAX_PARALLELISM = 8
MIN_SALT_LEN = 16
MAX_SALT_LEN = 64

DEK_LEN = Aead.KEY_SIZE
NONCE_LEN = Aead.NONCE_SIZE
TAG_LEN = Aead.MACBYTES
MAX_PLAINTEXT_BACKUP_BYTES = 50 * 1024 * 1024
MAX_PAYLOAD_CIPHERTEXT_BYTES = MAX_PLAINTEXT_BACKUP_BYTES + TAG_LEN


def parse_backup_envelope(raw: dict[str, Any]) -> BackupDocument | HermesBackup:
    format_name = raw.get("format")
    if format_name == "hermes-json-backup":
        return BackupDocument.model_validate(raw)
    try:
        if format_name == HERMES_FORMAT:
            version = raw.get("version")
            if not isinstance(version, int) or isinstance(version, bool):
                raise InvalidHermesFile("Hermes backup version must be an integer")
            if version != HERMES_VERSION:
                raise UnsupportedHermesVersion("Unsupported Hermes backup version")
            return HermesBackup.model_validate(raw)
    except ValidationError as error:
        raise InvalidHermesFile("Hermes backup structure is invalid") from error
    raise InvalidHermesFile("Unknown backup format")


class HermesV1Writer:
    def write(self, master_password: str, document: BackupDocument) -> HermesBackup:
        payload = HermesPayload(
            schema_version=document.schema_version,
            app_version=document.app_version,
            exported_at=document.exported_at,
            data=document.data,
        )
        plaintext = payload.model_dump_json(exclude_unset=True).encode("utf-8")
        if len(plaintext) > MAX_PLAINTEXT_BACKUP_BYTES:
            raise BackupTooLarge("Backup payload exceeds the 50 MiB limit")

        salt = secrets.token_bytes(ARGON2_SALT_LEN)
        kdf = HermesKdf(
            algorithm="argon2id",
            argon2_version=ARGON2_VERSION,
            salt=_encode(salt),
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
        )
        created_at = document.exported_at
        kek = bytearray(_derive_kek(master_password, salt, kdf))
        dek = bytearray(secrets.token_bytes(DEK_LEN))
        key_nonce = secrets.token_bytes(NONCE_LEN)
        payload_nonce = secrets.token_bytes(NONCE_LEN)
        while payload_nonce == key_nonce:
            payload_nonce = secrets.token_bytes(NONCE_LEN)
        try:
            encrypted_dek = (
                Aead(bytes(kek))
                .encrypt(bytes(dek), _key_aad(created_at, kdf), key_nonce)
                .ciphertext
            )
            ciphertext = (
                Aead(bytes(dek))
                .encrypt(plaintext, _payload_aad(created_at), payload_nonce)
                .ciphertext
            )
            return HermesBackup(
                format=HERMES_FORMAT,
                version=HERMES_VERSION,
                created_at=created_at,
                kdf=kdf,
                key_encryption=HermesKeyEncryption(
                    algorithm=AEAD_ALGORITHM,
                    nonce=_encode(key_nonce),
                    encrypted_data_key=_encode(encrypted_dek),
                ),
                payload_encryption=HermesPayloadEncryption(
                    algorithm=AEAD_ALGORITHM,
                    nonce=_encode(payload_nonce),
                    ciphertext=_encode(ciphertext),
                ),
            )
        finally:
            _wipe(kek)
            _wipe(dek)


class HermesV1Reader:
    def read(self, master_password: str, document: HermesBackup) -> HermesPayload:
        if document.version != HERMES_VERSION:
            raise UnsupportedHermesVersion("Unsupported Hermes backup version")
        salt = _decode(document.kdf.salt, "KDF salt")
        key_nonce = _decode(document.key_encryption.nonce, "key nonce")
        encrypted_dek = _decode(document.key_encryption.encrypted_data_key, "encrypted data key")
        payload_nonce = _decode(document.payload_encryption.nonce, "payload nonce")
        ciphertext = _decode(document.payload_encryption.ciphertext, "payload ciphertext")
        _validate_parameters(
            document.kdf, salt, key_nonce, encrypted_dek, payload_nonce, ciphertext
        )

        kek = bytearray(_derive_kek(master_password, salt, document.kdf))
        dek = bytearray()
        try:
            try:
                dek.extend(
                    Aead(bytes(kek)).decrypt(
                        encrypted_dek,
                        _key_aad(document.created_at, document.kdf),
                        key_nonce,
                    )
                )
                plaintext = Aead(bytes(dek)).decrypt(
                    ciphertext, _payload_aad(document.created_at), payload_nonce
                )
            except (CryptoError, ValueError) as error:
                raise BackupAuthenticationFailed(
                    "Incorrect password or corrupted backup."
                ) from error
            if len(plaintext) > MAX_PLAINTEXT_BACKUP_BYTES:
                raise BackupTooLarge("Backup payload exceeds the 50 MiB limit")
            try:
                payload = HermesPayload.model_validate_json(plaintext)
            except (ValidationError, ValueError, UnicodeDecodeError) as error:
                raise InvalidBackupPayload("Backup payload is invalid") from error
            if payload.exported_at != document.created_at:
                raise InvalidBackupPayload("Backup timestamps do not match")
            return payload
        finally:
            _wipe(kek)
            _wipe(dek)


def _derive_kek(master_password: str, salt: bytes, kdf: HermesKdf) -> bytes:
    return hash_secret_raw(
        secret=master_password.encode("utf-8"),
        salt=salt,
        time_cost=kdf.time_cost,
        memory_cost=kdf.memory_cost,
        parallelism=kdf.parallelism,
        hash_len=kdf.hash_len,
        type=Type.ID,
        version=kdf.argon2_version,
    )


def _validate_parameters(
    kdf: HermesKdf,
    salt: bytes,
    key_nonce: bytes,
    encrypted_dek: bytes,
    payload_nonce: bytes,
    ciphertext: bytes,
) -> None:
    if not (
        kdf.algorithm == "argon2id"
        and kdf.argon2_version == ARGON2_VERSION
        and MIN_TIME_COST <= kdf.time_cost <= MAX_TIME_COST
        and MIN_MEMORY_COST <= kdf.memory_cost <= MAX_MEMORY_COST
        and MIN_PARALLELISM <= kdf.parallelism <= MAX_PARALLELISM
        and kdf.hash_len == ARGON2_HASH_LEN
        and MIN_SALT_LEN <= len(salt) <= MAX_SALT_LEN
    ):
        raise InvalidKdfParameters("Hermes backup KDF parameters are outside safe limits")
    if len(key_nonce) != NONCE_LEN or len(payload_nonce) != NONCE_LEN:
        raise InvalidHermesFile("Hermes backup nonce length is invalid")
    if len(encrypted_dek) != DEK_LEN + TAG_LEN:
        raise InvalidHermesFile("Encrypted data key length is invalid")
    if not TAG_LEN <= len(ciphertext) <= MAX_PAYLOAD_CIPHERTEXT_BYTES:
        raise InvalidHermesFile("Payload ciphertext length is invalid")


def _key_aad(created_at: Any, kdf: HermesKdf) -> bytes:
    return _canonical(
        {
            "format": HERMES_FORMAT,
            "version": HERMES_VERSION,
            "created_at": created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "purpose": "key_encryption",
            "algorithm": AEAD_ALGORITHM,
            "kdf": kdf.model_dump(mode="json"),
        }
    )


def _payload_aad(created_at: Any) -> bytes:
    return _canonical(
        {
            "format": HERMES_FORMAT,
            "version": HERMES_VERSION,
            "created_at": created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "purpose": "payload_encryption",
            "algorithm": AEAD_ALGORITHM,
        }
    )


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _decode(value: str, label: str) -> bytes:
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise InvalidHermesFile(f"{label} is not valid base64") from error
    if _encode(decoded) != value:
        raise InvalidHermesFile(f"{label} is not canonical base64")
    return decoded


def _wipe(value: bytearray) -> None:
    for index in range(len(value)):
        value[index] = 0
