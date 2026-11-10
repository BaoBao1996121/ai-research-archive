import json
from pathlib import Path

from viral_lab.main import run_pipeline


def load_events(run_dir: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (run_dir / "event_log.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_mock_pipeline_emits_dry_run_publication(tmp_path):
    result = run_pipeline(provider="mock", output_dir=tmp_path, max_trends=4)

    events = load_events(result.run_dir)
    event_types = [event["type"] for event in events]

    assert "PipelineStarted" in event_types
    assert "PublicationDryRun" in event_types
    assert "RiskRejected" in event_types
    assert (result.run_dir / "run_report.json").exists()


def test_a2a_envelope_fields_are_present(tmp_path):
    result = run_pipeline(provider="mock", output_dir=tmp_path, max_trends=1)
    events = load_events(result.run_dir)

    first = events[0]["message"]
    for field in [
        "message_id",
        "trace_id",
        "conversation_id",
        "sender",
        "receiver",
        "performative",
        "payload",
    ]:
        assert field in first


def test_template_moviepy_demo_writes_mp4(tmp_path):
    trend_file = Path(__file__).parents[1] / "config" / "trends.sample.json"

    result = run_pipeline(
        provider="mock",
        trend_source="file",
        trend_file=trend_file,
        media_provider="template",
        video_renderer="moviepy",
        output_dir=tmp_path,
        max_trends=1,
    )

    videos = list(result.run_dir.glob("video_*.mp4"))
    assert videos, "expected template demo to produce an MP4"
    assert videos[0].stat().st_size > 1000
