This is a command line SDK for managing TDM-based dialogue domain descriptions (DDDs). For further information, see [talkamatic.se](http://talkamatic.se).

# Installation

Install the latest version of Tala with pip:

```bash
pip3 install tala
```

# CLI

Tala ships a single CLI entry point: `tala-interact`.

```bash
tala-interact https://host/interact/<id>
tala-interact https://host/interact/<id> --ddd my_ddd
```

# Requestor GPT API

`GPTRequest` in `tala.utils.requestor` can pass an OpenAI-compatible
`response_format` to Requestor. For example, strict JSON Schema output can be
requested like this:

```python
from tala.utils.requestor import GPTRequest, GPTStructuredOutputError

request = GPTRequest(
    messages=[{"role": "user", "content": "Return the status."}],
    model="gpt-6-luna-2026-09-22",
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
else:
    print(result)

print(request.completion_status)
```

Accessing `json_response` waits for the request to finish and parses its JSON.
Malformed JSON returned for a structured response raises
`GPTStructuredOutputError`, which includes the request ID, rather than being
replaced with the default response. `completion_status` exposes the Requestor
status, such as `completed`, `truncated`, `refused`, `incomplete`, or `error`.

For generic JSON-mode requests, `allow_json_repair` controls the legacy retry
that asks the model to repair invalid JSON. It defaults to `True`; set it to
`False` to disable that retry. Structured responses raise
`GPTStructuredOutputError` for malformed JSON instead of using generic repair.
