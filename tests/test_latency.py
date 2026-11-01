from packages.evaluation.latency import summarize_latency


def test_new_instances_are_not_counted_as_warm():
    result = summarize_latency(
        {
            "checked_at": "2026-11-01T00:00:00Z",
            "idle": {"after_instance": "a"},
            "warm": {
                "samples": [
                    {"instance_id": "a", "ms": 100, "process_uptime_seconds": 10},
                    {"instance_id": "b", "ms": 900, "process_uptime_seconds": 0.2},
                    {"instance_id": "b", "ms": 120, "process_uptime_seconds": 1},
                ]
            },
        }
    )
    assert result["sequence_count"] == 3
    assert result["reused_instance_count"] == 2
    assert result["reused_instance_p50_ms"] == 100
    assert result["reused_instance_p99_ms"] == 120
    assert result["additional_first_observations"][0]["instance_id"] == "b"


def test_no_reused_process_is_unmeasured():
    result = summarize_latency(
        {
            "checked_at": "2026-11-01T00:00:00Z",
            "idle": {"after_instance": "a"},
            "warm": {"samples": [{"instance_id": "b", "ms": 900, "process_uptime_seconds": 0.2}]},
        }
    )
    assert result["reused_instance_count"] == 0
    assert result["reused_instance_p50_ms"] is None
    assert result["reused_instance_p99_ms"] is None
