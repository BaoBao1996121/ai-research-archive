from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from viral_lab.agents import make_event
from viral_lab.contracts import Event, Performative


@dataclass
class TopicSaga:
    trend: dict[str, Any]
    comic_payload: dict[str, Any] | None = None
    caption_payload: dict[str, Any] | None = None
    voice_payload: dict[str, Any] | None = None
    video_requested: bool = False
    rejected: bool = False


class SagaOrchestrator:
    name = "saga_orchestrator"

    def __init__(self) -> None:
        self.sagas: dict[str, TopicSaga] = {}

    def handle_rejected(self, event: Event) -> list[Event]:
        saga = self._saga(event)
        saga.rejected = True
        return []

    def handle_comic(self, event: Event) -> list[Event]:
        self._saga(event).comic_payload = event.data
        return self._maybe_bundle(event)

    def handle_caption(self, event: Event) -> list[Event]:
        self._saga(event).caption_payload = event.data
        return self._maybe_bundle(event)

    def handle_voice(self, event: Event) -> list[Event]:
        self._saga(event).voice_payload = event.data
        return self._maybe_bundle(event)

    def _saga(self, event: Event) -> TopicSaga:
        return self.sagas.setdefault(event.message.trace_id, TopicSaga(trend=event.data["trend"]))

    def _maybe_bundle(self, event: Event) -> list[Event]:
        saga = self._saga(event)
        if saga.rejected or saga.video_requested:
            return []
        if not (saga.comic_payload and saga.caption_payload and saga.voice_payload):
            return []

        saga.video_requested = True
        bundle = {
            "comic": saga.comic_payload,
            "caption": saga.caption_payload["caption"],
            "voiceover": saga.voice_payload["voiceover"],
        }
        payload = {"trend": saga.trend, "bundle": bundle}
        return [
            make_event(
                "AssetBundleReady",
                self.name,
                "video_composer_agent",
                Performative.INFORM,
                payload,
                event,
            )
        ]
