# Requestor client

Tala’s `GPTRequest` class sends language-model requests to the platform’s
Requestor service. It communicates with that service; it does not call a model
provider directly.

## Configure the Requestor endpoint

Set `FUNCTION_ENDPOINT_REQUESTOR` in the environment of the process that runs
your Python code. Its value must be the URL of an accessible Requestor endpoint:

```bash
export FUNCTION_ENDPOINT_REQUESTOR="https://your-requestor-host/your-endpoint"
```

Use a model identifier supported by your Requestor configuration. Tala does not
provision the Requestor service or its model deployment.

## Request structured JSON

Pass an OpenAI-compatible JSON Schema response format to `GPTRequest`. Calling
`make()` starts the request; reading `json_response` waits for it to finish and
parses the returned JSON.

```python
from tala.utils.requestor import (
    GPTContentFilterError,
    GPTRequest,
    GPTStructuredOutputError,
)

request = GPTRequest(
    messages=[{"role": "user", "content": "Return the status."}],
    model="your-requestor-model",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "status",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"status": {"type": "string"}},
                "required": ["status"],
                "additionalProperties": False,
            },
        },
    },
)
request.make()

try:
    result = request.json_response
except GPTStructuredOutputError as error:
    print(f"Invalid structured response for request {error.request_id}")
except GPTContentFilterError as error:
    print(f"Request {error.request_id} was filtered")
else:
    print(result)

print(request.completion_status)
```

`completion_status` reports the status returned by Requestor, such as
`completed`, `truncated`, `refused`, `incomplete`, or `error`. A malformed JSON
response to a structured-output request raises `GPTStructuredOutputError`,
which includes the request ID.

## Generic JSON mode

For requests using `use_json=True` without a structured `response_format`,
`allow_json_repair` controls a legacy retry that asks the model to repair
invalid JSON. It defaults to `True`; set it to `False` to disable the retry.
Structured responses do not use this repair retry: malformed structured JSON
raises `GPTStructuredOutputError`.
