import json
from types import SimpleNamespace

import httpx
import openai
import pytest

from product_copywriter.errors import ConfigurationError, ProviderError
from product_copywriter.models import ProductInput
from product_copywriter.prompts import SYSTEM_PROMPT, build_input_message
from product_copywriter.provider import OpenAIProvider


def valid_output(**overrides):
    values = {
        "seo_title": "Промышленный прибор",
        "seo_description": "А" * 800,
        "search_queries": ["прибор купить", "промышленный прибор", "прибор для предприятия"],
        "commercial_block": "Подходит для промышленных предприятий.",
    }
    values.update(overrides)
    return values


class FakeResponses:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, responses):
        self.responses = responses


def response_with_json(value):
    return SimpleNamespace(output_text=json.dumps(value, ensure_ascii=False), output=[])


def test_provider_sends_structured_stateless_responses_request():
    product = ProductInput(name="Прибор", manufacturer="Завод")
    responses = FakeResponses(response_with_json(valid_output()))
    provider = OpenAIProvider(model="gpt-test", client=FakeClient(responses))

    generated = provider.generate(product)

    assert generated.seo_title == "Промышленный прибор"
    assert len(responses.calls) == 1
    request = responses.calls[0]
    assert request["model"] == "gpt-test"
    assert request["instructions"] == SYSTEM_PROMPT
    assert request["input"] == build_input_message(product)
    assert request["store"] is False
    assert request["text"]["format"]["type"] == "json_schema"
    assert request["text"]["format"]["name"] == "product_card_copy"
    assert request["text"]["format"]["strict"] is True
    schema = request["text"]["format"]["schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "seo_title",
        "seo_description",
        "search_queries",
        "commercial_block",
    }


def test_provider_requires_api_key_without_injected_client():
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        OpenAIProvider(model="gpt-test", api_key="")


@pytest.mark.parametrize(
    "bad_output",
    [
        "not json",
        json.dumps(valid_output(seo_description="слишком коротко"), ensure_ascii=False),
    ],
)
def test_provider_rejects_malformed_or_out_of_contract_output(bad_output):
    response = SimpleNamespace(output_text=bad_output, output=[])
    provider = OpenAIProvider(
        model="gpt-test",
        client=FakeClient(FakeResponses(response)),
    )

    with pytest.raises(ProviderError, match="не соответствует ожидаемой структуре"):
        provider.generate(ProductInput(name="Прибор"))


def test_provider_reports_model_refusal():
    response = SimpleNamespace(
        output_text="",
        output=[
            SimpleNamespace(
                content=[SimpleNamespace(type="refusal", refusal="Cannot comply")]
            )
        ],
    )
    provider = OpenAIProvider(
        model="gpt-test",
        client=FakeClient(FakeResponses(response)),
    )

    with pytest.raises(ProviderError, match="отказалась сформировать"):
        provider.generate(ProductInput(name="Прибор"))


def test_provider_translates_timeout():
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    error = openai.APITimeoutError(request)
    provider = OpenAIProvider(
        model="gpt-test",
        client=FakeClient(FakeResponses(error=error)),
    )

    with pytest.raises(ProviderError, match="время ожидания"):
        provider.generate(ProductInput(name="Прибор"))


def test_provider_translates_rate_limit():
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(429, request=request)
    error = openai.RateLimitError("provider detail", response=response, body=None)
    provider = OpenAIProvider(
        model="gpt-test",
        client=FakeClient(FakeResponses(error=error)),
    )

    with pytest.raises(ProviderError, match="лимит") as captured:
        provider.generate(ProductInput(name="Прибор"))
    assert "provider detail" not in str(captured.value)


def test_provider_translates_http_status_without_leaking_body():
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(500, request=request)
    error = openai.APIStatusError("sensitive upstream body", response=response, body=None)
    provider = OpenAIProvider(
        model="gpt-test",
        client=FakeClient(FakeResponses(error=error)),
    )

    with pytest.raises(ProviderError, match="HTTP 500") as captured:
        provider.generate(ProductInput(name="Прибор"))
    assert "sensitive upstream body" not in str(captured.value)
