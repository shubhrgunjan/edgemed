from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Login(Strict):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


class CreateMemory(Strict):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=12000)
    subject: str = Field(default="SYN-001", pattern=r"^SYN-[0-9]{3,6}$")
    category: Literal["OBSERVATION", "ALLERGY", "MEDICATION", "VITAL_SIGN", "NOTE"] = "OBSERVATION"
    privacy: Literal["SENSITIVE", "HIGHLY_SENSITIVE"] = "SENSITIVE"
    importance: float = Field(default=0.5, ge=0, le=1)


class Revision(Strict):
    parent: UUID
    content: str = Field(min_length=1, max_length=12000)


class Resolve(Strict):
    parents: list[UUID] = Field(min_length=2, max_length=10)
    chosen: UUID


class Search(Strict):
    query: str = Field(min_length=1, max_length=1000)
    mode: Literal["hybrid", "semantic"] = "hybrid"
    limit: int = Field(default=10, ge=1, le=30)
    subject: str | None = Field(default=None, pattern=r"^SYN-[0-9]{3,6}$")


class FixtureRevision(Strict):
    parent: UUID
    variant: Literal[0, 1, 2]


class TransportState(Strict):
    enabled: bool


class Export(Strict):
    schema_version: Literal[1] = 1
    policy_version: Literal["synthetic-reference-v1"] = "synthetic-reference-v1"
    operation_id: UUID
    memory_id: UUID
    revision_id: UUID
    parents: list[UUID] = Field(default_factory=list, max_length=10)
    device_id: str = Field(pattern=r"^edge-[ab]$")
    facility: Literal["lex-demo"] = "lex-demo"
    fixture: Literal["reference-hydration", "reference-handoff"]
    variant: Literal[0, 1, 2] = 0
    deleted: bool = False


class SignedOperation(Strict):
    payload: Export
    signature: str = Field(max_length=128)


class PullRequest(Strict):
    device_id: str = Field(pattern=r"^edge-[ab]$")
    cursor: int = Field(ge=0)
    nonce: UUID
    signature: str = Field(max_length=128)


class Receipt(Strict):
    operation_id: UUID
    accepted: Literal[True]
    duplicate: bool
    indexed: bool


class Change(Strict):
    seq: int = Field(ge=1)
    payload: Export


class PullPage(Strict):
    from_cursor: int = Field(ge=0)
    nonce: UUID
    changes: list[Change] = Field(max_length=100)
