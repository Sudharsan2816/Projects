from backend.services import research_engine


def test_selected_document_report_does_not_mix_in_web_context(monkeypatch):
    monkeypatch.setattr(
        research_engine,
        "_has_documents",
        lambda session_id, source_filenames=None: True,
    )

    def fail_web_search(*args, **kwargs):
        raise AssertionError("Selected-document reports must not use web context")

    monkeypatch.setattr(research_engine, "build_web_context", fail_web_search)

    assert (
        research_engine._build_optional_web_context(
            "session",
            "Vertical farming",
            "summary",
            ["selected.pdf"],
        )
        == ""
    )


def test_full_report_passes_selected_sources_to_every_section(monkeypatch):
    selected_sources = ["first.pdf", "second.pdf"]
    calls = []
    monkeypatch.setattr(
        research_engine,
        "_has_documents",
        lambda session_id, source_filenames=None: True,
    )

    def record(name, result):
        def fake(session_id, topic, source_filenames=None):
            calls.append((name, source_filenames))
            return result

        return fake

    monkeypatch.setattr(
        research_engine,
        "generate_executive_summary",
        record("summary", "Summary"),
    )
    monkeypatch.setattr(
        research_engine,
        "extract_competitors",
        record("competitors", []),
    )
    monkeypatch.setattr(
        research_engine,
        "extract_pricing_insights",
        record("pricing", []),
    )
    monkeypatch.setattr(
        research_engine,
        "extract_market_trends",
        record("trends", []),
    )
    monkeypatch.setattr(
        research_engine,
        "generate_swot",
        record(
            "swot",
            {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": [],
            },
        ),
    )

    report = research_engine.generate_full_report(
        "session",
        "Vertical farming",
        source_filenames=selected_sources,
    )

    assert report["data_source"] == "selected_documents"
    assert calls == [
        ("summary", selected_sources),
        ("competitors", selected_sources),
        ("pricing", selected_sources),
        ("trends", selected_sources),
        ("swot", selected_sources),
    ]
