from __future__ import annotations

import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Callable

from viral_lab.contracts import Event

Handler = Callable[[Event], list[Event]]


class EventLogStore:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.event_log_path = run_dir / "event_log.jsonl"
        self.events: list[Event] = []

    def record(self, event: Event) -> None:
        self.events.append(event)
        with self.event_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def write_json(self, name: str, payload: object) -> Path:
        path = self.run_dir / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def count_by_type(self) -> dict[str, int]:
        return dict(Counter(event.type for event in self.events))


class EventBus:
    def __init__(self, store: EventLogStore) -> None:
        self.store = store
        self.handlers: dict[str, list[Handler]] = defaultdict(list)
        self.queue: deque[Event] = deque()

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self.handlers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        self.store.record(event)
        self.queue.append(event)

    def drain(self) -> None:
        while self.queue:
            event = self.queue.popleft()
            for handler in self.handlers.get(event.type, []):
                for next_event in handler(event):
                    self.publish(next_event)
