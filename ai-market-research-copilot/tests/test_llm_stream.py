from types import SimpleNamespace

from backend.services import llm


class FakeStreamingClient:
    last_request = None

    def __init__(self, **kwargs):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self.create),
        )

    @staticmethod
    def create(**kwargs):
        FakeStreamingClient.last_request = kwargs
        return iter(
            [
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="Aravind Menon"))]
                ),
                SimpleNamespace(choices=[]),
            ]
        )


def test_nvidia_stream_ignores_terminal_event_without_choices(monkeypatch):
    monkeypatch.setattr(llm, "OpenAI", FakeStreamingClient)
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "nvidia")
    monkeypatch.setattr(llm.settings, "NVIDIA_API_KEY", "configured-for-test")
    monkeypatch.setattr(llm, "record_provider_call", lambda **kwargs: None)

    tokens = list(llm.generate_stream("Who founded SproutNest?"))

    assert tokens == ["Aravind Menon"]


def test_chat_stream_can_apply_a_smaller_output_limit(monkeypatch):
    monkeypatch.setattr(llm, "OpenAI", FakeStreamingClient)
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "nvidia")
    monkeypatch.setattr(llm.settings, "NVIDIA_API_KEY", "configured-for-test")
    monkeypatch.setattr(llm, "record_provider_call", lambda **kwargs: None)

    list(llm.generate_stream("Summarize this report", max_output_tokens=700))

    assert FakeStreamingClient.last_request["max_tokens"] == 700
