from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class Performative(StrEnum):
    INFORM = "inform"
    REQUEST = "request"
    PROPOSE = "propose"
    APPROVE = "approve"
    REJECT = "reject"
    DELEGATE = "delegate"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class A2AMessage:
    sender: str
    receiver: str
    performative: Performative
    payload: dict[str, Any]
    trace_id: str
    conversation_id: str
    message_id: str = field(default_factory=lambda: new_id("msg"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "trace_id": self.trace_id,
            "conversation_id": self.conversation_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "performative": self.performative.value,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class Event:
    type: str
    message: A2AMessage
    data: dict[str, Any]
    timestamp: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "timestamp": self.timestamp,
            "message": self.message.to_dict(),
            "data": self.data,
        }
