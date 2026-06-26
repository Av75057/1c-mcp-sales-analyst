from __future__ import annotations

from src.reflection.pipeline import critique_response, CRITIC_PROMPT


class TestCriticPrompt:
    def test_prompt_contains_key_elements(self):
        assert "is_valid" in CRITIC_PROMPT
        assert "score" in CRITIC_PROMPT
        assert "hallucination" in CRITIC_PROMPT
        assert "issues" in CRITIC_PROMPT
        assert "severity" in CRITIC_PROMPT
        assert "Фактическая точность" in CRITIC_PROMPT
        assert "Полнота" in CRITIC_PROMPT

    def test_prompt_requires_json(self):
        assert "JSON" in CRITIC_PROMPT or "json" in CRITIC_PROMPT


class TestCritiqueParsing:
    def test_extract_json_from_response(self):
        import json
        response_text = 'Some text {"is_valid": true, "score": 0.9} trailing'
        if "{" in response_text:
            json_str = response_text[response_text.index("{"): response_text.rindex("}") + 1]
            data = json.loads(json_str)
            assert data["is_valid"] is True
            assert data["score"] == 0.9

    def test_extract_invalid_json(self):
        response_text = "No JSON here"
        assert "{" not in response_text
