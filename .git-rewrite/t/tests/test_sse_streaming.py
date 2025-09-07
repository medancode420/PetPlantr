import pytest

@pytest.mark.sprint_c
def test_sse_event_format_and_sequence():
    def make_sse(events):
        # Minimal SSE framing helper for scaffolding
        lines = []
        for ev in events:
            if "event" in ev:
                lines.append(f"event: {ev['event']}")
            if "id" in ev:
                lines.append(f"id: {ev['id']}")
            data = ev.get("data", "")
            for line in str(data).splitlines() or [""]:
                lines.append(f"data: {line}")
            lines.append("")
        return "\n".join(lines)

    s = make_sse([
        {"event": "start", "id": "1", "data": {"status": "ok"}},
        {"event": "progress", "id": "2", "data": {"pct": 50}},
        {"event": "done", "id": "3", "data": {"ok": True}},
    ])

    # Validate framing and order
    assert "event: start" in s
    assert "event: progress" in s
    assert "event: done" in s
    assert s.index("event: start") < s.index("event: progress") < s.index("event: done")
