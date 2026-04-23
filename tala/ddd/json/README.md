# JSON DDD format

This directory describes the JSON counterpart to the XML DDD formats.
JSON is intended to be the primary source format going forward.

## Structure
The JSON format supports both a single bundle file and separate files.
Each element is represented by a top-level key matching the XML root.

Bundle file:

```json
{
  "schema_version": "1.0",
  "ontology": { ... },
  "domain": { ... },
  "service_interface": { ... }
}
```

Separate files:

- `ontology.json` -> `{ "ontology": { ... } }`
- `domain.json` -> `{ "domain": { ... } }`
- `service_interface.json` -> `{ "service_interface": { ... } }`

Elements are represented as objects with:
- `@`: attributes for the element
- `children`: ordered list of child elements

If `children` is omitted, child elements can be provided directly as keys.
Use `children` whenever order matters (for example inside plans).

## Example

```json
{
  "domain": {
    "@": {"name": "MockupDomain"},
    "children": [
      {
        "goal": {
          "@": {"type": "perform", "action": "top"},
          "children": [
            {"plan": {"children": [{"findout": {"@": {"type": "goal"}}}]}}
          ]
        }
      }
    ]
  }
}
```

## Configuration
Configure free-form file names via `ddd.config.json`:

```json
{
  "ddd_bundle": "ddd.json"
}
```

For separate files:

```json
{
  "ddd_files": {
    "ontology": "ontology.json",
    "domain": "domain.json",
    "service_interface": "service_interface.json"
  }
}
```

File extensions determine format (`.json` or `.xml`). When `ddd_bundle` is
set, it takes precedence over `ddd_files`.
