from pathlib import Path
import json
import tempfile

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "event_log.jsonl"
    events = [{"type": "PipelineStarted"}, {"type": "PublicationDryRun"}]
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    loaded = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert loaded[-1]["type"] == "PublicationDryRun"
print("event_log_jsonl_ok")
