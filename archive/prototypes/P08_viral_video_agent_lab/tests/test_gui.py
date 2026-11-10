from pathlib import Path

from viral_lab.gui import normalize_config, run_artifacts


def test_normalize_config_applies_real_api_preset():
    config = normalize_config({"preset": "real_api", "max_trends": "9"})

    assert config["trend_source"] == "hn"
    assert config["media_provider"] == "template"
    assert config["video_renderer"] == "moviepy"
    assert config["max_trends"] == 3


def test_run_artifacts_finds_publish_package_files(tmp_path):
    run_dir = tmp_path / "run_demo"
    run_dir.mkdir()
    for name in ["video_trace_abc.mp4", "caption.txt", "run_report.json"]:
        (run_dir / name).write_text("x", encoding="utf-8")

    artifacts = run_artifacts(run_dir)

    assert artifacts["videos"] == ["video_trace_abc.mp4"]
    assert "caption.txt" in artifacts["package_files"]
    assert artifacts["report"] == "run_report.json"
