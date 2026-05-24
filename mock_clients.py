"""
External API Mocking Utilities
==============================
Intercepts network calls to third parties to ensure tests remain fast, 
deterministic, and completely offline.
"""

import pytest
import respx
from httpx import Response

@pytest.fixture
def mock_openai_api():
    """Intercepts and mocks OpenAI's Chat Completion endpoint."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=Response(
                200, 
                json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "This is a strictly mocked AI response."
                        }
                    }],
                    "usage": {"total_tokens": 150}
                }
            )
        )
        yield route