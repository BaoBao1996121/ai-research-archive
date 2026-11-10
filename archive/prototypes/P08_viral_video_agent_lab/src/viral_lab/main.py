from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from viral_lab.adapters import (
    DryRunPublisher,
    MockCreativeProvider,
    build_media_factory,
    build_trend_source,
    build_video_renderer,
)
from viral_lab.agents import (
    ApprovalAgent,
    CopywriterAgent,
    CreativeDirectorAgent,
    DrawingAgent,
    PublisherAgent,
    RiskAndRightsAgent,
    StoryboardAgent,
    TrendScoutAgent,
    VideoComposerAgent,
    VoiceoverAgent,
)
from viral_lab.contracts import A2AMessage, Event, Performative, new_id
from viral_lab.events import EventBus, EventLogStore
from viral_lab.orchestrator import SagaOrchestrator


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    run_dir: Path
    report_path: Path
    event_log_path: Path


def run_pipeline(
    provider: str = "mock",
    trend_source: str = "mock",
    trend_file: str | Path | None = None,
    media_provider: str = "dry_run",
    video_renderer: str = "manifest",
    output_dir: str | Path = "output",
    max_trends: int = 4,
) -> PipelineResult:
    if provider != "mock":
        raise ValueError("This restored demo supports provider='mock'. Live providers are intentionally disabled.")

    run_id = new_id("run")
    root = Path(output_dir)
    run_dir = root / run_id
    store = EventLogStore(run_dir)
    bus = EventBus(store)

    source = build_trend_source(trend_source, Path(trend_file) if trend_file else None)
    trends = source.fetch(max_trends)
    creative = MockCreativeProvider()
    media = build_media_factory(media_provider)
    renderer = build_video_renderer(video_renderer)
    saga = SagaOrchestrator()

    bus.subscribe("PipelineStarted", TrendScoutAgent(trends).handle)
    bus.subscribe("TrendDetected", RiskAndRightsAgent().handle)
    bus.subscribe("RiskRejected", saga.handle_rejected)
    bus.subscribe("RiskChecked", CreativeDirectorAgent(creative).handle)
    bus.subscribe("ContentPlanCreated", StoryboardAgent(creative).handle)
    bus.subscribe("CaptionRequested", CopywriterAgent(creative).handle)
    bus.subscribe("StoryboardReady", DrawingAgent(media, store).handle)
    bus.subscribe("StoryboardReady", VoiceoverAgent(media, store).handle)
    bus.subscribe("ComicRendered", saga.handle_comic)
    bus.subscribe("CaptionReady", saga.handle_caption)
    bus.subscribe("VoiceoverReady", saga.handle_voice)
    bus.subscribe("AssetBundleReady", VideoComposerAgent(renderer, store).handle)
    bus.subscribe("VideoRendered", ApprovalAgent().handle)
    bus.subscribe("ApprovalGranted", PublisherAgent(DryRunPublisher(), store).handle)

    start = Event(
        "PipelineStarted",
        A2AMessage(
            sender="cli",
            receiver="trend_scout_agent",
            performative=Performative.REQUEST,
            payload={"max_trends": max_trends, "trend_source": trend_source},
            trace_id=run_id,
            conversation_id=run_id,
        ),
        {"max_trends": max_trends, "trend_source": trend_source},
    )
    bus.publish(start)
    bus.drain()

    report_path = _write_report(store, run_id, provider, trend_source, media_provider, video_renderer)
    return PipelineResult(run_id=run_id, run_dir=run_dir, report_path=report_path, event_log_path=store.event_log_path)


def _write_report(
    store: EventLogStore,
    run_id: str,
    provider: str,
    trend_source: str,
    media_provider: str,
    video_renderer: str,
) -> Path:
    publications = [event.data["publication"] for event in store.events if event.type == "PublicationDryRun"]
    videos = [event.data["video"] for event in store.events if event.type == "VideoRendered"]
    rejected = [event.data for event in store.events if event.type == "RiskRejected"]
    report = {
        "run_id": run_id,
        "mode": {
            "provider": provider,
            "trend_source": trend_source,
            "media_provider": media_provider,
            "video_renderer": video_renderer,
        },
        "event_counts": store.count_by_type(),
        "videos": videos,
        "publications": publications,
        "rejected_topics": rejected,
        "takeaway": "Offline demo: event-driven multi-agent pipeline with A2A envelopes, saga join, HITL gate, and dry-run publishing.",
    }
    return store.write_json("run_report.json", report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the P08 viral video agent lab demo.")
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--trend-source", default="mock", choices=["mock", "file", "hn", "hackernews"])
    parser.add_argument("--trend-file")
    parser.add_argument("--media-provider", default="dry_run", choices=["dry_run", "template"])
    parser.add_argument("--video-renderer", default="manifest", choices=["manifest", "moviepy"])
    parser.add_argument("--max-trends", type=int, default=4)
    parser.add_argument("--output-dir", default="output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_pipeline(
        provider=args.provider,
        trend_source=args.trend_source,
        trend_file=args.trend_file,
        media_provider=args.media_provider,
        video_renderer=args.video_renderer,
        output_dir=args.output_dir,
        max_trends=args.max_trends,
    )
    print(json.dumps({"run_id": result.run_id, "run_dir": str(result.run_dir), "report": str(result.report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
