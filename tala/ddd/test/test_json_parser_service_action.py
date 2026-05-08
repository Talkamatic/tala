from tala.ddd.json_parser import NonCheckingJSONParser
from tala.model import plan_item


def test_invoke_service_action_parses_action_fallback():
    parser = NonCheckingJSONParser()
    data = {
        "action": "EndSession",
        "ontology": "TestOntology",
        "preconfirm": None,
        "postconfirm": True,
        "downdate_plan": True,
    }

    item = parser.parse_invoke_service_action_plan_item(data)

    assert item.type_ == plan_item.TYPE_INVOKE_SERVICE_ACTION
    assert item.service_action == "EndSession"


def test_invoke_service_action_parses_action_dict():
    parser = NonCheckingJSONParser()
    data = {
        "service_action": {"name": "EndSession"},
        "ontology_name": "TestOntology",
        "preconfirm": None,
        "postconfirm": False,
        "_downdate_plan": True,
    }

    item = parser.parse_invoke_service_action_plan_item(data)

    assert item.type_ == plan_item.TYPE_INVOKE_SERVICE_ACTION
    assert item.service_action == "EndSession"
