from __future__ import annotations

from typing import Any

from viral_lab.adapters import DryRunPublisher, MediaFactory, MockCreativeProvider, VideoRenderer
from viral_lab.contracts import A2AMessage, Event, Performative, new_id
from viral_lab.events import EventLogStore


def make_event(
    event_type: str,
    sender: str,
    receiver: str,
    performative: Performative,
    payload: dict[str, Any],
    parent: Event,
    data: dict[str, Any] | None = None,
) -> Event:
    message = A2AMessage(
        sender=sender,
        receiver=receiver,
        performative=performative,
        payload=payload,
        trace_id=parent.message.trace_id,
        conversation_id=parent.message.conversation_id,
    )
    return Event(type=event_type, message=message, data=data or payload)


class TrendScoutAgent:
    name = "trend_scout_agent"

    def __init__(self, trends: list[dict[str, Any]]) -> None:
        self.trends = trends

    def handle(self, event: Event) -> list[Event]:
        out = []
        for trend in self.trends:
            message = A2AMessage(
                sender=self.name,
                receiver="risk_and_rights_agent",
                performative=Performative.INFORM,
                payload={"trend": trend},
                trace_id=new_id("trace"),
                conversation_id=event.message.conversation_id,
            )
            out.append(Event("TrendDetected", message, {"trend": trend}))
        return out


class RiskAndRightsAgent:
    name = "risk_and_rights_agent"
    blocked_terms = {"privacy", "private", "leak", "medical", "finance", "doxx"}

    def handle(self, event: Event) -> list[Event]:
        trend = event.data["trend"]
        text = f"{trend.get('title', '')} {trend.get('angle', '')} {trend.get('risk', '')}".lower()
        if any(term in text for term in self.blocked_terms):
            payload = {"trend": trend, "decision": "reject", "reason": "privacy_or_sensitive_topic"}
            return [make_event("RiskRejected", self.name, "orchestrator", Performative.REJECT, payload, event)]

        payload = {
            "trend": trend,
            "decision": "allow",
            "constraints": ["original commentary only", "human review before publishing"],
        }
        return [make_event("RiskChecked", self.name, "creative_director_agent", Performative.APPROVE, payload, event)]


class CreativeDirectorAgent:
    name = "creative_director_agent"

    def __init__(self, creative: MockCreativeProvider) -> None:
        self.creative = creative

    def handle(self, event: Event) -> list[Event]:
        trend = event.data["trend"]
        plan = self.creative.content_plan(trend)
        plan_payload = {"trend": trend, "plan": plan}
        caption_payload = {"trend": trend, "plan": plan}
        return [
            make_event("ContentPlanCreated", self.name, "storyboard_agent", Performative.PROPOSE, plan_payload, event),
            make_event("CaptionRequested", self.name, "copywriter_agent", Performative.REQUEST, caption_payload, event),
        ]


class StoryboardAgent:
    name = "storyboard_agent"

    def __init__(self, creative: MockCreativeProvider) -> None:
        self.creative = creative

    def handle(self, event: Event) -> list[Event]:
        trend = event.data["trend"]
        plan = event.data["plan"]
        storyboard = self.creative.storyboard(trend, plan)
        payload = {"trend": trend, "plan": plan, "storyboard": storyboard}
        return [make_event("StoryboardReady", self.name, "drawing_and_voiceover_agents", Performative.INFORM, payload, event)]


class DrawingAgent:
    name = "drawing_agent"

    def __init__(self, media: MediaFactory, store: EventLogStore) -> None:
        self.media = media
        self.store = store

    def handle(self, event: Event) -> list[Event]:
        assets = [
            self.media.render_panel(panel["visual_prompt"], panel, event.message.trace_id, self.store)
            for panel in event.data["storyboard"]["panels"]
        ]
        payload = {"trend": event.data["trend"], "assets": assets}
        return [make_event("ComicRendered", self.name, "orchestrator", Performative.INFORM, payload, event)]


class VoiceoverAgent:
    name = "voiceover_agent"

    def __init__(self, media: MediaFactory, store: EventLogStore) -> None:
        self.media = media
        self.store = store

    def handle(self, event: Event) -> list[Event]:
        script = event.data["storyboard"]["voiceover_script"]
        voiceover = self.media.render_voiceover(script, event.message.trace_id, self.store)
        payload = {"trend": event.data["trend"], "voiceover": voiceover}
        return [make_event("VoiceoverReady", self.name, "orchestrator", Performative.INFORM, payload, event)]


class CopywriterAgent:
    name = "copywriter_agent"

    def __init__(self, creative: MockCreativeProvider) -> None:
        self.creative = creative

    def handle(self, event: Event) -> list[Event]:
        payload = {
            "trend": event.data["trend"],
            "caption": self.creative.caption_package(event.data["trend"], event.data["plan"]),
        }
        return [make_event("CaptionReady", self.name, "orchestrator", Performative.INFORM, payload, event)]


class VideoComposerAgent:
    name = "video_composer_agent"

    def __init__(self, renderer: VideoRenderer, store: EventLogStore) -> None:
        self.renderer = renderer
        self.store = store

    def handle(self, event: Event) -> list[Event]:
        video = self.renderer.render(event.data["bundle"], event.message.trace_id, self.store)
        payload = {"trend": event.data["trend"], "video": video, "caption": event.data["bundle"]["caption"]}
        return [make_event("VideoRendered", self.name, "approval_agent", Performative.INFORM, payload, event)]


class ApprovalAgent:
    name = "approval_agent"
    checklist = [
        "Original commentary, no copied source video",
        "No private individual or sensitive personal data",
        "Manual human review required before real publishing",
        "Dry-run only in this demo",
    ]

    def handle(self, event: Event) -> list[Event]:
        requested_payload = {**event.data, "checklist": self.checklist}
        granted_payload = {**requested_payload, "approval": "auto_granted_for_demo_dry_run"}
        return [
            make_event("ApprovalRequested", self.name, "human_reviewer", Performative.REQUEST, requested_payload, event),
            make_event("ApprovalGranted", "human_reviewer", "publisher_agent", Performative.APPROVE, granted_payload, event),
        ]


class PublisherAgent:
    name = "publisher_agent"

    def __init__(self, publisher: DryRunPublisher, store: EventLogStore) -> None:
        self.publisher = publisher
        self.store = store

    def handle(self, event: Event) -> list[Event]:
        publication = self.publisher.publish(event.data["video"], event.data["caption"], event.data["checklist"], self.store)
        payload = {"trend": event.data["trend"], "publication": publication}
        return [make_event("PublicationDryRun", self.name, "run_report", Performative.INFORM, payload, event)]
