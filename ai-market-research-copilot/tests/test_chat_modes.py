from backend.services import chat_engine


def test_scope_gate_accepts_market_research_questions():
    assert chat_engine.is_market_research_question(
        "How should I calculate TAM, SAM, and SOM for this industry?"
    )
    assert chat_engine.is_market_research_question(
        "What pricing strategy should a new competitor use?"
    )


def test_scope_gate_rejects_unrelated_questions():
    assert not chat_engine.is_market_research_question("What is the capital of France?")
    assert not chat_engine.is_market_research_question("Write a poem about pricing")


def test_document_scope_accepts_natural_summary_requests():
    assert chat_engine.is_document_question("Important points to note")
    assert chat_engine.is_document_question("What are the key takeaways?")
    assert chat_engine.is_document_question("Summarize the uploaded document")


def test_relevant_question_uses_labeled_general_knowledge_when_docs_do_not_match(
    monkeypatch,
):
    monkeypatch.setattr(chat_engine, "retrieve_results", lambda **kwargs: [])
    monkeypatch.setattr(
        chat_engine,
        "generate",
        lambda prompt, system, **kwargs: "Use top-down and bottom-up market sizing.",
    )

    answer, sources, mode = chat_engine.chat(
        "session",
        "How do I estimate the market size for a new product?",
    )

    assert "top-down" in answer
    assert sources == []
    assert mode == "general_market_knowledge"


def test_unrelated_question_is_marked_not_in_report_after_retrieval(monkeypatch):
    call_order = []

    def fake_retrieve(**kwargs):
        call_order.append("retrieve")
        return []

    def fake_has_indexed_documents(session_id):
        call_order.append("check_index")
        assert call_order == ["retrieve", "check_index"]
        return True

    monkeypatch.setattr(chat_engine, "retrieve_results", fake_retrieve)
    monkeypatch.setattr(
        chat_engine, "has_indexed_documents", fake_has_indexed_documents
    )

    def fail_generate(*args, **kwargs):
        raise AssertionError("The model must not answer a question unsupported by the report")

    monkeypatch.setattr(chat_engine, "generate", fail_generate)

    answer, sources, mode = chat_engine.chat(
        "session",
        "What is the capital of France?",
    )

    assert "checked the uploaded report first" in answer
    assert sources == []
    assert mode == "report_irrelevant"


def test_unrelated_question_without_a_report_remains_scope_guarded(monkeypatch):
    monkeypatch.setattr(chat_engine, "retrieve_results", lambda **kwargs: [])
    monkeypatch.setattr(
        chat_engine, "has_indexed_documents", lambda session_id: False
    )

    answer, sources, mode = chat_engine.chat(
        "session",
        "What is the capital of France?",
    )

    assert "outside this copilot's market-research scope" in answer
    assert sources == []
    assert mode == "out_of_scope"


def test_relevant_document_context_remains_grounded_and_cited(monkeypatch):
    results = [
        (
            {
                "source": "market.pdf",
                "text": "The addressable market is USD 4 billion.",
                "chunk_index": 2,
            },
            0.82,
        )
    ]
    monkeypatch.setattr(chat_engine, "retrieve_results", lambda **kwargs: results)
    monkeypatch.setattr(
        chat_engine,
        "answer_from_results",
        lambda query, selected, system, **kwargs: (
            "The document reports a USD 4 billion market.",
            [{"filename": "market.pdf", "chunk_index": 2}],
        ),
    )

    answer, sources, mode = chat_engine.chat("session", "What is the market size?")

    assert "USD 4 billion" in answer
    assert sources[0]["filename"] == "market.pdf"
    assert mode == "documents"


def test_retrieved_but_unsupported_context_is_marked_not_in_report(monkeypatch):
    results = [
        (
            {
                "source": "market.pdf",
                "text": "The report covers vertical-farming appliances.",
                "chunk_index": 2,
            },
            0.62,
        )
    ]
    monkeypatch.setattr(chat_engine, "retrieve_results", lambda **kwargs: results)
    monkeypatch.setattr(
        chat_engine,
        "answer_from_results",
        lambda query, selected, system, **kwargs: (
            "Not covered in the uploaded documents. The report discusses a different market.",
            [{"filename": "market.pdf", "chunk_index": 2}],
        ),
    )

    answer, sources, mode = chat_engine.chat(
        "session", "What is the market size of electric aircraft?"
    )

    assert answer.startswith("Not covered in the uploaded documents")
    assert sources == []
    assert mode == "report_irrelevant"


def test_generic_summary_request_uses_document_context_without_score_cutoff(monkeypatch):
    captured = {}
    results = [
        (
            {
                "source": "market.pdf",
                "text": "Demand is growing and price sensitivity remains high.",
                "chunk_index": 0,
            },
            0.21,
        )
    ]

    def fake_retrieve(**kwargs):
        captured.update(kwargs)
        return results

    monkeypatch.setattr(chat_engine, "retrieve_results", fake_retrieve)
    monkeypatch.setattr(
        chat_engine,
        "answer_from_results",
        lambda query, selected, system, **kwargs: (
            "The important points are demand growth and price sensitivity.",
            [{"filename": "market.pdf", "chunk_index": 0}],
        ),
    )

    answer, sources, mode = chat_engine.chat("session", "Important points to note")

    assert "demand growth" in answer
    assert sources[0]["filename"] == "market.pdf"
    assert mode == "documents"
    assert captured["minimum_score"] is None
    assert "most important findings" in captured["query"]


def test_generic_summary_request_without_documents_is_not_scope_guarded(monkeypatch):
    monkeypatch.setattr(chat_engine, "retrieve_results", lambda **kwargs: [])

    answer, sources, mode = chat_engine.chat("session", "Important points to note")

    assert "Not covered in the uploaded documents" in answer
    assert sources == []
    assert mode == "documents"


def test_history_aware_rewrite_supplies_a_standalone_retrieval_query(monkeypatch):
    captured = {}
    results = [
        (
            {
                "source": "report.pdf",
                "text": "SproutNest was founded by Aravind Menon.",
                "chunk_index": 0,
            },
            0.5,
        )
    ]

    def fake_retrieve(**kwargs):
        captured.update(kwargs)
        return results

    monkeypatch.setattr(chat_engine, "retrieve_results", fake_retrieve)
    monkeypatch.setattr(
        chat_engine,
        "generate_with_provider",
        lambda provider, prompt, system, **kwargs: "Who founded SproutNest?",
    )
    monkeypatch.setattr(
        chat_engine,
        "answer_from_results",
        lambda query, selected, system, **kwargs: (
            "SproutNest was founded by Aravind Menon.",
            [{"filename": "report.pdf", "chunk_index": 0}],
        ),
    )
    history = [
        {"role": "user", "content": "Give me a broad summary of every market trend."},
        {"role": "assistant", "content": "A long previous response that must not be embedded."},
    ]

    answer, sources, mode = chat_engine.chat(
        "session",
        "Who founded SproutNest?",
        history=history,
    )

    assert "Aravind Menon" in answer
    assert sources[0]["filename"] == "report.pdf"
    assert mode == "documents"
    assert captured["query"] == "Who founded SproutNest?"
    assert captured["use_lexical_fallback"] is True


def test_document_answer_prompt_receives_only_current_turn(monkeypatch):
    captured = {}
    results = [
        (
            {
                "source": "report.pdf",
                "text": "The report contains no information about Tesla.",
                "chunk_index": 0,
            },
            0.5,
        )
    ]
    monkeypatch.setattr(chat_engine, "retrieve_results", lambda **kwargs: results)
    monkeypatch.setattr(
        chat_engine,
        "generate_with_provider",
        lambda provider, prompt, system, **kwargs: "What is Tesla's 2026 market share?",
    )
    monkeypatch.setattr(
        chat_engine,
        "correct_document_entity_typos",
        lambda session_id, query: query,
    )

    def fake_answer(query, selected, system, **kwargs):
        captured["query"] = query
        captured.update(kwargs)
        return "Not covered in the uploaded documents.", []

    monkeypatch.setattr(chat_engine, "answer_from_results", fake_answer)
    history = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "That is not in the report."},
    ]

    answer, sources, mode = chat_engine.chat(
        "session",
        "What is Tesla's 2026 market share?",
        history=history,
    )

    assert answer == "Not covered in the uploaded documents."
    assert sources == []
    assert mode == "report_irrelevant"
    assert captured["query"] == "What is Tesla's 2026 market share?"
    assert "France" not in captured["query"]
    assert captured["max_output_tokens"] == chat_engine.settings.CHAT_MAX_OUTPUT_TOKENS


def test_pronoun_follow_up_is_rewritten_with_report_backed_entity(monkeypatch):
    captured = {}
    results = [
        (
            {
                "source": "report.pdf",
                "text": "KrishiKube's weakness is its under-developed app.",
                "chunk_index": 0,
            },
            0.8,
        )
    ]
    monkeypatch.setattr(
        chat_engine,
        "correct_document_entity_typos",
        lambda session_id, query: query,
    )
    monkeypatch.setattr(
        chat_engine,
        "find_document_entity_mention",
        lambda session_id, text: "KrishiKube" if "KrishiKube" in text else None,
    )

    def fake_retrieve(**kwargs):
        captured["retrieval_query"] = kwargs["query"]
        return results

    def fake_answer(query, selected, system, **kwargs):
        captured["answer_query"] = query
        return "Its weakness is an under-developed app.", [
            {"filename": "report.pdf", "chunk_index": 0}
        ]

    monkeypatch.setattr(chat_engine, "retrieve_results", fake_retrieve)
    monkeypatch.setattr(chat_engine, "answer_from_results", fake_answer)
    monkeypatch.setattr(
        chat_engine,
        "generate_with_provider",
        lambda provider, prompt, system, **kwargs: "What are KrishiKube's weaknesses?",
    )

    answer, sources, mode = chat_engine.chat(
        "session",
        "What are its weaknesses?",
        history=[{"role": "user", "content": "Tell me about KrishiKube"}],
    )

    assert "under-developed app" in answer
    assert sources
    assert mode == "documents"
    assert captured["retrieval_query"] == "What are KrishiKube's weaknesses?"
    assert captured["answer_query"] == "What are KrishiKube's weaknesses?"
    assert "Tell me about" not in captured["retrieval_query"]


def test_clarification_turn_is_rewritten_before_stream_retrieval(monkeypatch):
    captured = {}
    results = [
        (
            {
                "source": "pricing.pdf",
                "text": "Nimbus starts at $19 while Corvex starts at $29.",
                "chunk_index": 3,
            },
            0.91,
        )
    ]

    def fake_rewrite(provider, prompt, system, **kwargs):
        captured["provider"] = provider
        captured["rewrite_prompt"] = prompt
        captured["rewrite_system"] = system
        captured["rewrite_max_tokens"] = kwargs["max_output_tokens"]
        return "Compare entry pricing of Nimbus vs Corvex"

    def fake_retrieve(**kwargs):
        captured["retrieval_query"] = kwargs["query"]
        return results

    def fake_info(message, *args, **kwargs):
        if message == "history_aware_query_rewrite":
            captured["rewrite_log"] = kwargs["extra"]

    monkeypatch.setattr(chat_engine, "generate_with_provider", fake_rewrite)
    monkeypatch.setattr(chat_engine, "retrieve_results", fake_retrieve)
    monkeypatch.setattr(chat_engine.logger, "info", fake_info)
    monkeypatch.setattr(
        chat_engine,
        "generate_stream",
        lambda prompt, system, **kwargs: iter(["Nimbus is cheaper than Corvex."]),
    )

    history = [
        {"role": "user", "content": "Compare entry pricing A vs B"},
        {"role": "assistant", "content": "Which companies do A and B represent?"},
    ]
    events = list(
        chat_engine.chat_stream(
            "session",
            "A is Nimbus B is Corvex",
            history=history,
        )
    )

    assert captured["provider"] == "gemini"
    assert "Compare entry pricing A vs B" in captured["rewrite_prompt"]
    assert "A is Nimbus B is Corvex" in captured["rewrite_prompt"]
    assert captured["retrieval_query"] == "Compare entry pricing of Nimbus vs Corvex"
    assert captured["rewrite_max_tokens"] == 120
    assert captured["rewrite_log"]["original_message"] == "A is Nimbus B is Corvex"
    assert captured["rewrite_log"]["rewritten_query"] == (
        "Compare entry pricing of Nimbus vs Corvex"
    )
    assert events[-1][2] == "documents"


def test_first_turn_does_not_call_query_rewriter(monkeypatch):
    captured = {}

    def fail_rewrite(*args, **kwargs):
        raise AssertionError("Turn one must not call the history-aware query rewriter")

    def fake_retrieve(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(chat_engine, "generate_with_provider", fail_rewrite)
    monkeypatch.setattr(chat_engine, "retrieve_results", fake_retrieve)
    monkeypatch.setattr(chat_engine, "has_indexed_documents", lambda session_id: True)

    chat_engine.chat("session", "Compare entry pricing of Nimbus vs Corvex")

    assert captured["query"] == "Compare entry pricing of Nimbus vs Corvex"


def test_empty_report_retrieval_returns_verified_report_miss(monkeypatch):
    monkeypatch.setattr(chat_engine, "retrieve_results", lambda **kwargs: [])
    monkeypatch.setattr(chat_engine, "has_indexed_documents", lambda session_id: True)

    def fail_generate(*args, **kwargs):
        raise AssertionError("A missing document fact must not call general knowledge")

    monkeypatch.setattr(chat_engine, "generate", fail_generate)

    answer, sources, mode = chat_engine.chat(
        "session",
        "What is SproutNest's net profit margin?",
    )

    assert "does not contain information relevant to this question" in answer
    assert sources == []
    assert mode == "report_irrelevant"


def test_stream_reports_general_answer_mode(monkeypatch):
    monkeypatch.setattr(chat_engine, "retrieve_results", lambda **kwargs: [])
    monkeypatch.setattr(
        chat_engine, "has_indexed_documents", lambda session_id: False
    )
    monkeypatch.setattr(
        chat_engine,
        "generate_stream",
        lambda prompt, system, **kwargs: iter(["Use ", "TAM/SAM/SOM."]),
    )

    events = list(
        chat_engine.chat_stream(
            "session",
            "Which market sizing framework should I use?",
        )
    )

    assert events[-1] == (None, [], "general_market_knowledge")
    assert "".join(event[0] or "" for event in events) == "Use TAM/SAM/SOM."


def test_stream_marks_verified_report_miss(monkeypatch):
    retrieval_finished = False

    def fake_retrieve(**kwargs):
        nonlocal retrieval_finished
        retrieval_finished = True
        return []

    def fake_has_indexed_documents(session_id):
        assert retrieval_finished
        return True

    monkeypatch.setattr(chat_engine, "retrieve_results", fake_retrieve)
    monkeypatch.setattr(
        chat_engine, "has_indexed_documents", fake_has_indexed_documents
    )

    events = list(chat_engine.chat_stream("session", "What is the capital of France?"))

    assert events[-1] == (None, [], "report_irrelevant")
    assert "checked the uploaded report first" in "".join(
        event[0] or "" for event in events
    )


def test_stream_relabels_retrieved_but_unsupported_context(monkeypatch):
    results = [
        (
            {
                "source": "market.pdf",
                "text": "The report covers vertical-farming appliances.",
                "chunk_index": 2,
            },
            0.62,
        )
    ]
    monkeypatch.setattr(chat_engine, "retrieve_results", lambda **kwargs: results)
    monkeypatch.setattr(
        chat_engine,
        "generate_stream",
        lambda prompt, system, **kwargs: iter(
            ["Not covered in the uploaded documents. ", "This is a different market."]
        ),
    )

    events = list(
        chat_engine.chat_stream(
            "session", "What is the market size of electric aircraft?"
        )
    )

    assert events[-1] == (None, [], "report_irrelevant")
    assert "Not covered in the uploaded documents" in "".join(
        event[0] or "" for event in events
    )


def test_stream_answers_natural_summary_request_from_documents(monkeypatch):
    captured = {}
    results = [
        (
            {
                "source": "market.pdf",
                "text": "The market is worth USD 4 billion.",
                "chunk_index": 2,
            },
            0.22,
        )
    ]

    def fake_retrieve(**kwargs):
        captured.update(kwargs)
        return results

    monkeypatch.setattr(chat_engine, "retrieve_results", fake_retrieve)
    monkeypatch.setattr(
        chat_engine,
        "generate_stream",
        lambda prompt, system, **kwargs: iter(["The important point is ", "USD 4 billion."]),
    )

    events = list(chat_engine.chat_stream("session", "Important points to note"))

    assert events[-1][2] == "documents"
    assert events[-1][1][0]["filename"] == "market.pdf"
    assert "".join(event[0] or "" for event in events) == (
        "The important point is USD 4 billion."
    )
    assert captured["minimum_score"] is None
