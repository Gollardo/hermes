from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, SecretStr

from app.core.validation import Money
from app.modules.accounts.contracts import AccountType
from app.modules.categories.contracts import CategoryType
from app.modules.funds.backup import FundEventType
from app.modules.operations.contracts import OperationType
from app.modules.scheduling.backup import OccurrenceStatus, RecurrenceFrequency


class BackupModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SettingsRecord(BackupModel):
    base_currency: str
    timezone: str
    base_currency_locked_at: AwareDatetime | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AccountRecord(BackupModel):
    id: UUID
    type: AccountType
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    archived_at: AwareDatetime | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CategoryRecord(BackupModel):
    id: UUID
    type: CategoryType
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    parent_id: UUID | None
    archived_at: AwareDatetime | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class OperationRecord(BackupModel):
    id: UUID
    type: OperationType
    description: str | None = Field(max_length=2000)
    reason: str | None = Field(max_length=2000)
    category_id: UUID | None
    occurred_on: date
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int = Field(ge=1)


class AccountMovementRecord(BackupModel):
    id: UUID
    operation_id: UUID
    account_id: UUID
    amount: Money


class FundRecord(BackupModel):
    id: UUID
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(max_length=2000)
    allocation_percentage: Money
    archived_at: AwareDatetime | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int = Field(ge=1)


class FundEventRecord(BackupModel):
    id: UUID
    type: FundEventType
    occurred_on: date
    description: str | None = Field(max_length=2000)
    created_at: AwareDatetime


class FundMovementRecord(BackupModel):
    id: UUID
    fund_id: UUID
    account_id: UUID
    operation_id: UUID | None
    event_id: UUID | None
    amount: Money


class RecurringRuleRecord(BackupModel):
    id: UUID
    type: OperationType
    frequency: RecurrenceFrequency
    start_on: date
    end_on: date | None
    amount: Money
    description: str | None = Field(max_length=2000)
    account_id: UUID
    destination_account_id: UUID | None
    category_id: UUID | None
    active: bool
    version: int = Field(ge=1)
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ExpectedOccurrenceRecord(BackupModel):
    id: UUID
    rule_id: UUID
    scheduled_on: date
    due_on: date
    status: OccurrenceStatus
    manually_modified: bool
    type: OperationType
    amount: Money
    description: str | None = Field(max_length=2000)
    account_id: UUID
    destination_account_id: UUID | None
    category_id: UUID | None
    actual_operation_id: UUID | None
    version: int = Field(ge=1)
    created_at: AwareDatetime
    updated_at: AwareDatetime


class BackupData(BackupModel):
    settings: SettingsRecord
    accounts: list[AccountRecord]
    categories: list[CategoryRecord]
    operations: list[OperationRecord]
    account_movements: list[AccountMovementRecord]
    funds: list[FundRecord]
    fund_events: list[FundEventRecord]
    fund_movements: list[FundMovementRecord]
    recurring_rules: list[RecurringRuleRecord]
    expected_occurrences: list[ExpectedOccurrenceRecord]


class BackupIntegrity(BackupModel):
    algorithm: Literal["sha256"] = "sha256"
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class BackupDocument(BackupModel):
    format: Literal["hermes-json-backup"]
    schema_version: Literal[1]
    app_version: str
    exported_at: AwareDatetime
    data: BackupData
    integrity: BackupIntegrity


class BackupCounts(BackupModel):
    accounts: int
    categories: int
    operations: int
    account_movements: int
    funds: int
    fund_events: int
    fund_movements: int
    recurring_rules: int
    expected_occurrences: int


class BackupPreviewResponse(BackupModel):
    format: str
    schema_version: int
    app_version: str
    exported_at: AwareDatetime
    counts: BackupCounts
    base_currency: str
    timezone: str
    integrity_verified: bool


class RestoreRequest(BackupModel):
    backup: BackupDocument
    confirmation: str = Field(max_length=64)
    master_password: SecretStr = Field(max_length=1024)


class RestoreResponse(BackupModel):
    restored: bool
    counts: BackupCounts
