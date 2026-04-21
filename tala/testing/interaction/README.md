# Interaction testing

## Purpose
The interaction testing helpers validate multi-turn dialog flows by comparing
expected moves with recorded responses from the TDM service. These tests are
used in `tala/testing/interaction/test` and rely on the interaction tester to
send requests and assert structured responses.

## Key modules
- `interaction_tester.py`: sends requests to TDM and returns structured output.
- `comparison.py`: compares actual moves with expected sequences and reports
  mismatches.
- `interaction_test_executor.py`: coordinates running scripted interactions.
- `stream_listener.py`: listens to streamed responses where applicable.

## Running tests
Use pytest as usual:

```bash
python -m pytest tala/testing/interaction/test
```

## Configuration
- `TDM_REQUEST_TIMEOUT_SECONDS`: request timeout for interaction tests and the
  TDM client. Defaults to `120` seconds when unset or invalid.

## Adding tests
1. Create a new test module under `tala/testing/interaction/test`.
2. Build expected move sequences that match the structured output for each
   interaction step.
3. Use the interaction tester/executor helpers for request execution.
4. Keep tests deterministic by asserting only on stable fields.

## Expectations
Interaction comparisons can accept a single expected move list or a list of
alternative move sequences. When multiple alternatives are provided, the first
matching sequence is used for the assertion output.

## Format
Interaction tests live in `ddds/<name>/test/interaction_tests.json` and are a
JSON array of test cases. Each test case defines a `name`, `url`, `target_ddd`,
and an `interaction` list with alternating `user` and `system` entries.

Each interaction entry uses:
- `speaker`: `user` or `system`
- `move_content`: list of semantic move strings (system entries may use
  alternatives by providing a list of move lists)
- `speech_content`: expected system utterance (system entries) or user
  utterance to send as speech input (user entries)
- `utterance`: optional text attached to semantic user input
- `interpretations`: optional list of semantic interpretations for user input
- `entities`: optional entity list used with `interpretations`
- `expected_passivity`: optional boolean on user or system turns

Top-level test case fields:
- `name`: test name for logs
- `url`: TDM endpoint (supports port override in executor)
- `target_ddd`: DDD name for semantic user moves
- `interaction`: ordered list of user/system turns
- `neural`: optional flag passed into the session payload

Example (truncated):

```json
[
  {
    "name": "asking about time",
    "url": "http://localhost:9090/interact",
    "target_ddd": "hello_world",
    "interaction": [
      {
        "speaker": "user",
        "move_content": [
          "ask(?X.current_time(X))"
        ]
      },
      {
        "speaker": "system",
        "move_content": [
          "answer(current_time(\"10:05\"))"
        ]
      }
    ]
  }
]
```

Alternatives are expressed by supplying a list of move sequences in
`move_content`, for example when multiple system responses are acceptable.

### User input variants
You can supply semantic moves, free-form speech, or explicit interpretations.
When `move_content` is present, it takes precedence and `utterance` (if
provided) is attached to the semantic interpretation; `speech_content` is
ignored in that case.

Semantic moves (optionally with `utterance`):

```json
{
  "speaker": "user",
  "move_content": ["answer(hour_to_set(11))"],
  "utterance": "set it to eleven"
}
```

Speech input:

```json
{
  "speaker": "user",
  "speech_content": "set it to eleven"
}
```

Explicit interpretations (with per-move DDD info):

```json
{
  "speaker": "user",
  "utterance": "set it to eleven",
  "interpretations": [
    {
      "moves": [
        {
          "ddd": "hello_world",
          "semantic_expression": "answer(hour_to_set(11))",
          "perception_confidence": 0.9,
          "understanding_confidence": 0.95
        }
      ],
      "modality": "other"
    }
  ],
  "entities": []
}
```

### System expectations
System entries can assert moves, speech output, or passivity:

When both `move_content` and `speech_content` are provided in a system entry,
the tester asserts both the move list and the utterance.

```json
{
  "speaker": "system",
  "move_content": [
    "icm:acc*pos",
    "ask(?X.hour_to_set(X))"
  ],
  "speech_content": "What hour should I set?"
}
```

## Output
The interaction test executor returns a result dictionary with:
- `success`: boolean indicating test outcome
- `failure_description`: mismatch description on failure
- `transcript`: buffered transcript for the run

## Streaming
If the executor runs with streaming enabled, the system utterance can be
populated from the stream listener instead of the HTTP response.
