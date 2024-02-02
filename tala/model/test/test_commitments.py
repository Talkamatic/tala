import unittest

from tala.model.commitments import Commitments
from tala.model.proposition import ActionStatusProposition
from tala.model.action_status import Done
from tala.model.action import Action


class CommitmentsTests(unittest.TestCase):
    def setUp(self):
        self.commitments = Commitments()

    def test_as_dict(self):
        self.given_a_commitment(ActionStatusProposition(Action("some_action", "some_ontology"), Done()))
        self.when_stored_as_json_dict()
        self.then_stored_dict_is({
            'commitments_set': {
                'set': [{
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                }],
                'semantic_expression': '{action_status(some_action, done)}'
            },
            'meta_com': [{
                'key': {
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                },
                'value': [None, '-1']
            }],
            'pcom': {
                'set': [],
                'semantic_expression': '{}'
            },
            'meta_pcom': [],
            'commitment_lifespan': '30',
            'semantic_expression': '{action_status(some_action, done)}'
        })

    def given_a_commitment(self, commitment):
        self.commitments.add(commitment)

    def when_stored_as_json_dict(self):
        self.commitments_as_dict = self.commitments.as_json()

    def then_stored_dict_is(self, expected):
        self.assertEqual(expected, self.commitments_as_dict)

    def test_as_dict_when_commitment_is_removed(self):
        self.given_a_commitment(ActionStatusProposition(Action("some_action", "some_ontology"), Done()))
        self.given_commitment_was_removed(ActionStatusProposition(Action("some_action", "some_ontology"), Done()))
        self.when_stored_as_json_dict()
        self.then_stored_dict_is({
            'commitments_set': {
                'set': [],
                'semantic_expression': '{}'
            },
            'meta_com': [{
                'key': {
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                },
                'value': [None, '-1']
            }],
            'pcom': {
                'set': [{
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                }],
                'semantic_expression': '{action_status(some_action, done)}'
            },
            'meta_pcom': [{
                'key': {
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                },
                'value': [None, '-1']
            }],
            'commitment_lifespan': '30',
            'semantic_expression': '{}'
        })

    def given_commitment_was_removed(self, commitment):
        self.commitments.remove(commitment)

    def test_creation_from_dict_single_commitment(self):
        self.maxDiff = None
        self.given_commitments_as_dict({
            'commitments_set': {
                'set': [],
                'semantic_expression': '{}'
            },
            'meta_com': [{
                'key': {
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                },
                'value': [None, '-1']
            }],
            'pcom': {
                'set': [{
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                }],
                'semantic_expression': '{action_status(some_action, done)}'
            },
            'meta_pcom': [{
                'key': {
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                },
                'value': [None, '-1']
            }],
            'commitment_lifespan': '30',
            'semantic_expression': '{}'
        })
        self.given_created_commitments_from_input_dict()
        self.when_stored_as_json_dict()
        self.then_stored_dict_is(self.input_commitments_as_dict)

    def given_commitments_as_dict(self, commitments_as_dict):
        self.input_commitments_as_dict = commitments_as_dict

    def given_created_commitments_from_input_dict(self):
        self.commitments = Commitments.create_from_json(self.input_commitments_as_dict)

    def test_creation_from_dict_and_purge(self):
        self.maxDiff = None
        self.given_commitments_as_dict({
            'commitments_set': {
                'set': [],
                'semantic_expression': '{}'
            },
            'meta_com': [{
                'key': {
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                },
                'value': [None, '-1']
            }],
            'pcom': {
                'set': [{
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                }],
                'semantic_expression': '{action_status(some_action, done)}'
            },
            'meta_pcom': [{
                'key': {
                    '_type': 'ACTION_STATUS',
                    '_polarity': 'POS',
                    '_predicted': False,
                    '_confidence_estimates': None,
                    '_content': {
                        '_ontology_name': 'some_ontology',
                        'value': 'some_action',
                        'semantic_expression': 'some_action'
                    },
                    '_status': {
                        'action_status': 'done'
                    },
                    'semantic_expression': 'action_status(some_action, done)'
                },
                'value': [None, '-1']
            }],
            'commitment_lifespan': '30',
            'semantic_expression': '{}'
        })
        self.given_created_commitments_from_input_dict()
        self.when_purged()
        self.then_no_exceptions_are_raised()

    def when_purged(self):
        self.commitments.should_purge_previous_commitments(12)

    def then_no_exceptions_are_raised(self):
        self.assertTrue(True)
