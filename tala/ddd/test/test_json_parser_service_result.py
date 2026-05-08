from tala.ddd.json_parser import NonCheckingJSONParser
from tala.model.proposition import ServiceResultProposition
from tala.model.service_action_outcome import SuccessfulServiceAction


def test_parse_service_result_uses_private_service_action():
    parser = NonCheckingJSONParser()
    original = ServiceResultProposition("Sida8AOntology", "EndSession", [], SuccessfulServiceAction())

    parsed = parser.parse_proposition(original.as_json())

    assert parsed.service_action == "EndSession"
