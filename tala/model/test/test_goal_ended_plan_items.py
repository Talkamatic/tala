import pytest

from tala.model import plan_item, action
from tala.utils import json_api


class TestGoalPerformed:
    def test_serialize_using_json_api(self):
        self.given_action("some-action", "some-ontology-name")
        self.given_postconfirm(True)
        self.given_goal_performed()
        self.when_as_json_api()
        self.then_json_api_is({
            'data': {
                'attributes': {
                    'postconfirm': True
                },
                'id': 'tala.model.plan_item.GoalPerformed:True:some-action',
                'relationships': {
                    'action': {
                        'data': {
                            'id': 'some-ontology-name:some-action',
                            'type': 'tala.model.action'
                        }
                    }
                },
                'type': 'tala.model.plan_item.GoalPerformed',
                'version:id': '2'
            },
            'included': [{
                'attributes': {
                    'name': 'some-action',
                    'ontology_name': 'some-ontology-name'
                },
                'id': 'some-ontology-name:some-action',
                'type': 'tala.model.action'
            }]
        })

    def given_action(self, action_name, ontology_name):
        self._action = action.Action(action_name, ontology_name)

    def given_postconfirm(self, postconfirm):
        self._postconfirm = postconfirm

    def given_goal_performed(self):
        self._goal_performed_item = plan_item.GoalPerformed(self._postconfirm, self._action)

    def when_as_json_api(self):
        self._json_api_as_dict = self._goal_performed_item.as_json_api_dict()

    def then_json_api_is(self, obj_as_json):
        assert self._json_api_as_dict == obj_as_json

    @pytest.mark.parametrize("params", ([True, "some-action"], [False, "some-action"], [True, None], [False, None]))
    def test_create_from_json_api_data(self, params):
        self.given_class(plan_item.GoalPerformed)
        self.given_parameters(params)
        self.given_json_api_data_for()
        self.when_create_from_data()
        self.then_object_equals(self._cls(*self._parameters))

    def given_class(self, cls):
        self._cls = cls

    def given_parameters(self, parameters):
        if parameters[1]:
            self._parameters = [parameters[0], action.Action(parameters[1], "some-ontology-name")]
        else:
            self._parameters = [parameters[0], None]

    def given_json_api_data_for(self):
        if self._parameters[1]:
            self._data = {
                'attributes': {
                    'postconfirm': self._parameters[0]
                },
                'id': f'tala.model.plan_item.GoalPerformed:{self._parameters[0]}',
                'relationships': {
                    'action': {
                        'data': {
                            'id': f'some-ontology-name:{self._parameters[1].name}',
                            'type': 'tala.model.action'
                        }
                    }
                },
                'type': 'tala.model.plan_item.GoalPerformed',
                'version:id': '2'
            }
            self._included = json_api.IncludedObject([{
                'attributes': {
                    'name': self._parameters[1].name,
                    'ontology_name': 'some-ontology-name'
                },
                'id': f'some-ontology-name:{self._parameters[1].name}',
                'type': 'tala.model.action'
            }])
        else:
            self._data = {
                'attributes': {
                    'postconfirm': self._parameters[0]
                },
                'id': f'tala.model.plan_item.GoalPerformed:{self._parameters[0]}',
                'relationships': {},
                'type': 'tala.model.plan_item.GoalPerformed',
                'version:id': '2'
            }
            self._included = json_api.IncludedObject([])

    def when_create_from_data(self):
        self._created_object = self._cls.create_from_json_api_data(self._data, self._included)

    def then_object_equals(self, expected_object, result=True):
        if result:
            assert expected_object == self._created_object
        else:
            assert expected_object != self._created_object

    @pytest.mark.parametrize(
        "params, equality",
        (([True, "some-action"], False), ([False, "some-action"], False), ([True, None], True), ([False, None], False))
    )
    def test_create_from_json_api_data_unequal(self, params, equality):
        self.given_class(plan_item.GoalPerformed)
        self.given_parameters(params)
        self.given_json_api_data()
        self.when_create_from_data()
        obj = self._cls(*self._parameters)
        self.then_object_equals(obj, equality)

    def given_json_api_data(self):
        self._data = {
            'attributes': {
                'postconfirm': True
            },
            'id': 'tala.model.plan_item.GoalPerformed:True',
            'relationships': {},
            'type': 'tala.model.plan_item.GoalPerformed',
            'version:id': '2'
        }
        self._included = json_api.IncludedObject([])


class TestGoalAborted:
    def test_serialize_using_json_api(self):
        self.given_action("some-action", "some-ontology-name")
        self.given_reason("some-reason")
        self.given_goal_aborted()
        self.when_as_json_api()
        self.then_json_api_is({
            'data': {
                'attributes': {
                    'reason': 'some-reason'
                },
                'id': 'tala.model.plan_item.GoalAborted:some-action:some-reason',
                'relationships': {
                    'action': {
                        'data': {
                            'id': 'some-ontology-name:some-action',
                            'type': 'tala.model.action'
                        }
                    }
                },
                'type': 'tala.model.plan_item.GoalAborted',
                'version:id': '2'
            },
            'included': [{
                'attributes': {
                    'name': 'some-action',
                    'ontology_name': 'some-ontology-name'
                },
                'id': 'some-ontology-name:some-action',
                'type': 'tala.model.action'
            }]
        })

    def given_action(self, action_name, ontology_name):
        self._action = action.Action(action_name, ontology_name)

    def given_reason(self, reason):
        self._reason = reason

    def given_goal_aborted(self):
        self._goal_aborted_item = plan_item.GoalAborted(self._reason, self._action)

    def when_as_json_api(self):
        self._json_api_as_dict = self._goal_aborted_item.as_json_api_dict()

    def then_json_api_is(self, obj_as_json):
        assert self._json_api_as_dict == obj_as_json

    @pytest.mark.parametrize(
        "params",
        (["some-reason", "some-action"], ["other-reason", "some-action"], ["some-reason", None], ["other-reason", None])
    )
    def test_create_from_json_api_data(self, params):
        self.given_class(plan_item.GoalAborted)
        self.given_parameters(params)
        self.given_json_api_data_for()
        self.when_create_from_data()
        self.then_object_equals(self._cls(*self._parameters))

    def given_class(self, cls):
        self._cls = cls

    def given_parameters(self, parameters):
        if parameters[1]:
            self._parameters = [parameters[0], action.Action(parameters[1], "some-ontology-name")]
        else:
            self._parameters = [parameters[0], None]

    def given_json_api_data_for(self):
        if self._parameters[1]:
            self._data = {
                'attributes': {
                    'reason': self._parameters[0]
                },
                'id': f'tala.model.plan_item.GoalAborted:{self._parameters[0]}',
                'relationships': {
                    'action': {
                        'data': {
                            'id': f'some-ontology-name:{self._parameters[1].name}',
                            'type': 'tala.model.action'
                        }
                    }
                },
                'type': 'tala.model.plan_item.GoalAborted',
                'version:id': '2'
            }
            self._included = json_api.IncludedObject([{
                'attributes': {
                    'name': self._parameters[1].name,
                    'ontology_name': 'some-ontology-name'
                },
                'id': f'some-ontology-name:{self._parameters[1].name}',
                'type': 'tala.model.action'
            }])
        else:
            self._data = {
                'attributes': {
                    'reason': self._parameters[0]
                },
                'id': f'tala.model.plan_item.GoalAborted:{self._parameters[0]}',
                'relationships': {},
                'type': 'tala.model.plan_item.GoalAborted',
                'version:id': '2'
            }
            self._included = json_api.IncludedObject([])

    def when_create_from_data(self):
        self._created_object = self._cls.create_from_json_api_data(self._data, self._included)

    def then_object_equals(self, expected_object, expected_result=True):
        if expected_result:
            assert expected_object == self._created_object
        else:
            assert expected_object != self._created_object

    @pytest.mark.parametrize(
        "params, equality", ((["some-reason", "some-action"], False), (["other-reason", "some-action"], False),
                             (["some-reason", None], True), (["other-reason", None], False))
    )
    def test_create_from_json_api_data_unequal(self, params, equality):
        self.given_class(plan_item.GoalAborted)
        self.given_parameters(params)
        self.given_json_api_data()
        self.when_create_from_data()
        self.then_object_equals(self._cls(*self._parameters), equality)

    def given_json_api_data(self):
        self._data = {
            'attributes': {
                'reason': "some-reason"
            },
            'id': 'tala.model.plan_item.GoalAborted:some-reason',
            'relationships': {},
            'type': 'tala.model.plan_item.GoalAborted',
            'version:id': '2'
        }
        self._included = json_api.IncludedObject([])
