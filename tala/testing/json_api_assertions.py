def normalize_expected_json_api(payload):
    if isinstance(payload, dict):
        if "version:id" in payload and not _looks_like_json_api_object(payload):
            return {key: normalize_expected_json_api(value) for key, value in payload.items()}
        meta_value = None
        normalized = {}
        for key, value in payload.items():
            if key == "version:id":
                meta_value = value
                continue
            if key == "attributes" and isinstance(value, dict):
                attributes = {}
                for attr_key, attr_value in value.items():
                    if attr_key == "version:id":
                        meta_value = attr_value
                        continue
                    attributes[attr_key] = normalize_expected_json_api(attr_value)
                normalized[key] = attributes
                continue
            normalized[key] = normalize_expected_json_api(value)

        if meta_value is not None:
            meta = {}
            if isinstance(normalized.get("meta"), dict):
                meta.update(normalized["meta"])
            meta["version:id"] = meta_value
            normalized["meta"] = meta
        return normalized
    if isinstance(payload, list):
        return [normalize_expected_json_api(item) for item in payload]
    return payload


def _looks_like_json_api_object(payload):
    for key in ("type", "id", "attributes", "relationships", "data"):
        if key in payload:
            return True
    return False
