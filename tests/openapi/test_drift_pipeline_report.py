from scripts.openapi_drift.drift_pipeline_report import build_pipeline_report, pr_body_markdown, summary_markdown


def test_pipeline_report_accepts_openapi_refresh_artifacts() -> None:
    report = build_pipeline_report(
        tracked_paths=[
            "openapi/astrox.openapi.yaml",
            "openapi/archive/2026-06-04.openapi.yaml",
        ],
        previous_openapi_version="1.0.0",
        current_openapi_version="1.0.1",
    )

    assert report["pr_required"] is True
    assert report["refresh_valid"] is True
    assert report["unexpected_paths"] == []
    assert report["changed_categories"] == {
        "openapi_baseline": True,
        "openapi_archive": True,
    }
    assert "OpenAPI description: yes" in summary_markdown(report)
    assert "dated OpenAPI archive copy: yes" in pr_body_markdown(report)


def test_pipeline_report_rejects_legacy_fixture_changes() -> None:
    report = build_pipeline_report(
        tracked_paths=["openapi/fixtures/STATUS.md"],
        previous_openapi_version="1.0.0",
        current_openapi_version="1.0.0",
    )

    assert report["pr_required"] is False
    assert report["refresh_valid"] is False
    assert report["unexpected_paths"] == ["openapi/fixtures/STATUS.md"]
