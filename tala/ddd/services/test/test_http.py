import json
import unittest
import requests
import logging

from unittest.mock import patch, Mock

from tala.ddd.services.service_interface import ServiceParameter
from tala.model.individual import Individual
from tala.model.predicate import Predicate
from tala.model.proposition import PredicateProposition
from tala.model.polarity import Polarity
from tala.model.question import WhQuestion
from tala.model.service_query_result import QueryResultFromService
from tala.model.service_action_outcome import SuccessfulServiceAction, FailedServiceAction
from tala.model.service_invocation import Context, PROTOCOL_VERSION
from tala.model.sort import Sort

import tala.ddd.services.http
from tala.ddd.extended_ddd import ExtendedDDD
from tala.ddd.services.http import HttpServiceClient, HttpServiceInvocationException
from tala.ddd.services.parameters.binding import SingleInstanceParameterBinding


class HttpServiceClientTest(unittest.TestCase):
    def setUp(self):
        self._requests_patcher = patch(f"{tala.ddd.services.http.__name__}")
        self._mock_logger = Mock(spec=logging.Logger)
        self._mock_session = self._requests_patcher.start()
        self._mock_ddd_components = self._create_mock_ddd_components()
        self._mock_parameter_bindings = [
            SingleInstanceParameterBinding(
                parameter=self._mock_service_parameter("mock_predicate_name"),
                value="mock_value",
                proposition=self.mock_predicate_proposition(
                    predicate_name="mock_predicate_name", sort_name="mock_sort_name", value="mock_value"
                )
            )
        ]

    def tearDown(self):
        self._requests_patcher.stop()

    def _expected_facts_as_dict(
        self,
        sort="mock_sort_name",
        grammar_entry="mock_grammar_entry",
        value="mock_value",
        perception_confidence=None,
        understanding_confidence=None,
        weighted_confidence=None,
        weighted_understanding_confidence=None
    ):
        return {
            "mock_predicate_name": {
                "sort": sort,
                "grammar_entry": grammar_entry,
                "perception_confidence": perception_confidence,
                "understanding_confidence": understanding_confidence,
                "weighted_confidence": weighted_confidence,
                "weighted_understanding_confidence": weighted_understanding_confidence,
                "value": value
            }
        }

    def _expected_parameters_as_dict(
        self,
        sort="mock_sort_name",
        grammar_entry="mock_grammar_entry",
        value="mock_value",
        perception_confidence=None,
        understanding_confidence=None,
        weighted_confidence=None,
        weighted_understanding_confidence=None
    ):
        return {
            "mock_predicate_name": {
                "sort": sort,
                "grammar_entry": grammar_entry,
                "perception_confidence": perception_confidence,
                "understanding_confidence": understanding_confidence,
                "weighted_confidence": weighted_confidence,
                "weighted_understanding_confidence": weighted_understanding_confidence,
                "value": value
            }
        }

    def _create_mock_ddd_components(self):
        mock_components = Mock(spec=ExtendedDDD)
        return mock_components

    def _mock_service_parameter(self, name):
        mock_service_parameter = Mock(spec=ServiceParameter)
        mock_service_parameter.name = name
        return mock_service_parameter

    def given_http_service_client(self, endpoint, name):
        self._http_service_client = HttpServiceClient(self._mock_logger, endpoint, name)
        self._http_service_client._session = self._mock_session

    def then_request_is_posted(self, expected_url, expected_data, expected_headers):
        self._mock_session.post.assert_called_once_with(
            expected_url, data=expected_data, headers=expected_headers, timeout=2
        )

    def given_requests_post_returns_response(self, response_text):
        self._mock_session.post.return_value = self._mock_response(response_text)

    def _mock_response(self, text):
        mock_response = Mock(spec=requests.Response)
        mock_response.text = text
        return mock_response

    def then_result_is(self, expected):
        self.assertEqual(expected, self._actual_result)

    def test_perform_posts_request(self):
        self.given_http_service_client("mock_endpoint", "mock_action")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "success",
                "data": {
                    "version": PROTOCOL_VERSION,
                }
            })
        )
        self.given_session([{
            "sort": "mock_sort",
            "natural_language_form": "mock_grammar_entry",
            "name": "mock_value"
        }], "mock_session_id")

        self.when_perform(
            "mock_action", self._mock_parameter_bindings,
            Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id")
        )
        self.then_request_is_posted(
            expected_url="mock_endpoint",
            expected_data=json.dumps({
                "version": PROTOCOL_VERSION,
                "session": {
                    "session_id": "mock_session_id",
                    "entities": [{
                        "sort": "mock_sort",
                        "natural_language_form": "mock_grammar_entry",
                        "name": "mock_value"
                    }]
                },
                "request": {
                    "type": "request",
                    "name": "mock_action",
                    "parameters": self._expected_parameters_as_dict()
                },
                "context": {
                    "active_ddd": "mock_active_ddd",
                    "facts": self._expected_facts_as_dict(),
                    "invocation_id": "mock_invocation_id"
                }
            }),
            expected_headers={"Content-type": "application/json"}
        )

    def given_session(self, entities, session_id):
        self._session = {"session_id": session_id, "entities": entities}

    def when_perform(self, action, parameters, context):
        self._actual_result = self._http_service_client.perform(action, parameters, self._session, context)

    def test_perform_returns_successful_result(self):
        self.given_http_service_client("mock_endpoint", "mock_action")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "success",
                "data": {
                    "version": PROTOCOL_VERSION,
                }
            })
        )
        self.given_session([], "mock_session_id")
        self.when_perform(
            "mock_action", self._mock_parameter_bindings,
            Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id")
        )
        self.then_result_is(SuccessfulServiceAction())

    def test_perform_returns_failed_result(self):
        self.given_http_service_client("mock_endpoint", "mock_action")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "fail",
                "data": {
                    "version": PROTOCOL_VERSION,
                    "reason": "mock_failure_reason"
                }
            })
        )
        self.given_session([], "mock_session_id")
        self.when_perform(
            "mock_action", self._mock_parameter_bindings,
            Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id")
        )
        self.then_result_is(FailedServiceAction("mock_failure_reason"))

    def test_query_posts_request(self):
        self.given_http_service_client("mock_endpoint", "mock_question_predicate")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "success",
                "data": {
                    "version": PROTOCOL_VERSION,
                    "result": []
                }
            })
        )
        self.given_session([{
            "sort": "mock_sort",
            "natural_language_form": "mock_grammar_entry",
            "name": "mock_value"
        }], "mock_session_id")

        self.when_query(
            question=self.mock_wh_question("mock_question_predicate"),
            parameters=self._mock_parameter_bindings,
            min_results=0,
            max_results=None,
            session=self._session,
            context=Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id")
        )
        self.then_request_is_posted(
            expected_url="mock_endpoint",
            expected_data=json.dumps({
                "version": PROTOCOL_VERSION,
                "session": {
                    "session_id": "mock_session_id",
                    "entities": [{
                        "sort": "mock_sort",
                        "natural_language_form": "mock_grammar_entry",
                        "name": "mock_value"
                    }]
                },
                "request": {
                    "type": "query",
                    "name": "mock_question_predicate",
                    "parameters": self._expected_parameters_as_dict(),
                    "min_results": 0,
                    "max_results": None
                },
                "context": {
                    "active_ddd": "mock_active_ddd",
                    "facts": self._expected_facts_as_dict(),
                    "invocation_id": "mock_invocation_id"
                }
            }),
            expected_headers={"Content-type": "application/json"}
        )

    def mock_wh_question(self, predicate_name, sort_name="mock_sort"):
        mock_question = Mock(spec=WhQuestion)
        sort = self._mock_sort(sort_name)
        predicate = self._mock_predicate(predicate_name, sort)
        mock_question.predicate = predicate
        return mock_question

    def when_query(self, *args, **kwargs):
        self._actual_result = self._http_service_client.query(*args, **kwargs)

    def test_query_returns_parsed_response(self):
        self.given_http_service_client("mock_endpoint", "mock_question_predicate")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "success",
                "data": {
                    "version": PROTOCOL_VERSION,
                    "result": [{
                        "value": "mock_value",
                        "confidence": "mock_confidence",
                        "grammar_entry": "mock_grammar_entry"
                    }]
                }
            })
        )
        self.when_query(
            question=self.mock_wh_question("mock_question_predicate"),
            parameters=self._mock_parameter_bindings,
            min_results=0,
            max_results=None,
            session={'session_id': 'mock_session_id'},
            context=Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id")
        )
        self.then_result_is([QueryResultFromService("mock_value", "mock_confidence", "mock_grammar_entry")])

    def test_request_for_validate_with_grammar_entry(self):
        self.given_http_service_client("mock_endpoint", "MockValidator")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "success",
                "data": {
                    "version": PROTOCOL_VERSION,
                    "is_valid": True,
                }
            })
        )
        self.given_session([{
            "sort": "mock_sort",
            "natural_language_form": "mock_grammar_entry",
            "name": "mock_value"
        }], "mock_session_id")
        self.when_validate(
            "MockValidator", self._mock_parameter_bindings,
            Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id")
        )
        self.then_request_is_posted(
            expected_url="mock_endpoint",
            expected_data=json.dumps({
                "version": PROTOCOL_VERSION,
                "session": {
                    "session_id": "mock_session_id",
                    "entities": [{
                        "sort": "mock_sort",
                        "natural_language_form": "mock_grammar_entry",
                        "name": "mock_value"
                    }]
                },
                "request": {
                    "type": "validator",
                    "name": "MockValidator",
                    "parameters": self._expected_parameters_as_dict()
                },
                "context": {
                    "active_ddd": "mock_active_ddd",
                    "facts": self._expected_facts_as_dict(),
                    "invocation_id": "mock_invocation_id"
                }
            }),
            expected_headers={"Content-type": "application/json"}
        )

    def when_validate(self, validator_name, parameters, context):
        self._actual_result = self._http_service_client.validate(validator_name, parameters, self._session, context)

    def mock_predicate_proposition(
        self,
        predicate_name,
        sort_name,
        value,
        polarity=Polarity.POS,
        perception_confidence=None,
        understanding_confidence=None,
        weighted_confidence=None,
        weighted_understanding_confidence=None
    ):
        sort = self._mock_sort(sort_name)
        predicate = self._mock_predicate(predicate_name, sort)
        individual = self._mock_individual(value, sort)
        mock_predicate_proposition = Mock(spec=PredicateProposition)
        mock_predicate_proposition.is_predicate_proposition.return_value = True
        mock_predicate_proposition.get_polarity.return_value = polarity
        mock_predicate_proposition.predicate = predicate
        mock_predicate_proposition.individual = individual
        mock_predicate_proposition.confidence_estimates.perception_confidence = perception_confidence
        mock_predicate_proposition.confidence_estimates.understanding_confidence = understanding_confidence
        mock_predicate_proposition.confidence_estimates.weighted_confidence = weighted_confidence
        mock_predicate_proposition.confidence_estimates.weighted_understanding_confidence = weighted_understanding_confidence
        return mock_predicate_proposition

    def _mock_facts(
        self,
        predicate_name="mock_predicate_name",
        sort_name="mock_sort_name",
        value="mock_value",
        polarity=Polarity.POS,
        perception_confidence=None,
        understanding_confidence=None,
        weighted_confidence=None,
        weighted_understanding_confidence=None
    ):
        return [
            self.mock_predicate_proposition(
                predicate_name=predicate_name,
                sort_name=sort_name,
                value=value,
                polarity=polarity,
                perception_confidence=perception_confidence,
                understanding_confidence=understanding_confidence,
                weighted_confidence=weighted_confidence,
                weighted_understanding_confidence=weighted_understanding_confidence
            )
        ]

    def _mock_predicate(self, name, sort):
        mock_predicate = Mock(spec=Predicate)
        mock_predicate.get_name.return_value = name
        mock_predicate.sort = sort
        return mock_predicate

    def _mock_sort(self, name):
        mock_sort = Mock(spec=Sort)
        mock_sort.get_name.return_value = name
        return mock_sort

    def _mock_individual(self, value, sort):
        mock_individual = Mock(spec=Individual)
        mock_individual.sort = sort
        mock_individual.value = value
        mock_individual.value_as_json_object.return_value = {"value": value}
        return mock_individual

    def test_request_for_validate_without_grammar_entry(self):
        self.given_http_service_client("mock_endpoint", "MockValidator")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "success",
                "data": {
                    "version": PROTOCOL_VERSION,
                    "is_valid": True,
                }
            })
        )
        self.given_session([], "mock_session_id")
        self.when_validate(
            "MockValidator", self._mock_parameter_bindings,
            Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id")
        )
        self.then_request_is_posted(
            expected_url="mock_endpoint",
            expected_data=json.dumps({
                "version": PROTOCOL_VERSION,
                "session": {
                    "session_id": "mock_session_id",
                    "entities": []
                },
                "request": {
                    "type": "validator",
                    "name": "MockValidator",
                    "parameters": self._expected_parameters_as_dict(grammar_entry=None)
                },
                "context": {
                    "active_ddd": "mock_active_ddd",
                    "facts": self._expected_facts_as_dict(grammar_entry=None),
                    "invocation_id": "mock_invocation_id"
                }
            }),
            expected_headers={"Content-type": "application/json"}
        )

    def test_successful_validation_response(self):
        self.given_http_service_client("mock_endpoint", "MockValidator")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "success",
                "data": {
                    "version": PROTOCOL_VERSION,
                    "is_valid": True
                }
            })
        )
        self.given_session([], "mock_session_id")
        self.when_validate(
            "MockValidator", self._mock_parameter_bindings,
            Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id")
        )
        self.then_result_is(True)

    def test_failed_validation_response(self):
        self.given_http_service_client("mock_endpoint", "MockValidator")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "success",
                "data": {
                    "version": PROTOCOL_VERSION,
                    "is_valid": False,
                }
            })
        )
        self.given_session([], "mock_session_id")
        self.when_validate(
            "MockValidator", self._mock_parameter_bindings,
            Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id")
        )
        self.then_result_is(False)

    def test_fail_with_query(self):
        self.given_http_service_client("mock_endpoint", "MockQuery")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "fail",
                "data": {
                    "version": PROTOCOL_VERSION,
                }
            })
        )
        self.when_query_then_exception_is_raised_matching(
            question=self.mock_wh_question("mock_question_predicate"),
            parameters=self._mock_parameter_bindings,
            min_results=0,
            max_results=None,
            session={'session_id': 'mock_session_id'},
            context=Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id"),
            expected_exception=HttpServiceInvocationException,
            expected_message="Expected status 'success' but got 'fail'."
        )

    def when_query_then_exception_is_raised_matching(self, expected_exception, expected_message, *args, **kwargs):
        with self.assertRaisesRegex(expected_exception, expected_message):
            self._http_service_client.query(*args, **kwargs)

    def test_fail_with_validator(self):
        self.given_http_service_client("mock_endpoint", "MockValidator")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "fail",
                "data": {
                    "version": PROTOCOL_VERSION,
                }
            })
        )
        self.when_validating_then_exception_is_raised_matching(
            validator_name="MockValidator",
            parameters=self._mock_parameter_bindings,
            session={'session_id': 'mock_session_id'},
            context=Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id"),
            expected_exception=HttpServiceInvocationException,
            expected_message="Expected status 'success' but got 'fail'."
        )

    def when_validating_then_exception_is_raised_matching(self, expected_exception, expected_message, *args, **kwargs):
        with self.assertRaisesRegex(expected_exception, expected_message):
            self._http_service_client.validate(*args, **kwargs)

    def test_error_with_validator(self):
        self.given_http_service_client("mock_endpoint", "MockValidator")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "error",
                "message": "an error message",
                "data": {
                    "version": PROTOCOL_VERSION,
                }
            })
        )
        self.when_validating_then_exception_is_raised_matching(
            validator_name="MockValidator",
            parameters=self._mock_parameter_bindings,
            session={'session_id': 'mock_session_id'},
            context=Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id"),
            expected_exception=HttpServiceInvocationException,
            expected_message="Expected service to succeed but it had an error with message: 'an error message'."
        )

    def test_error_with_perform(self):
        self.given_http_service_client("mock_endpoint", "mock_action")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "error",
                "message": "an error message",
                "data": {
                    "version": PROTOCOL_VERSION,
                }
            })
        )
        self.when_perform_then_exception_is_raised_matching(
            action="mock_action",
            parameters=self._mock_parameter_bindings,
            session={'session_id': 'mock_session_id'},
            context=Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id"),
            expected_exception=HttpServiceInvocationException,
            expected_message="Expected service to succeed but it had an error with message: 'an error message'."
        )

    def when_perform_then_exception_is_raised_matching(self, expected_exception, expected_message, *args, **kwargs):
        with self.assertRaisesRegex(expected_exception, expected_message):
            self._http_service_client.perform(*args, **kwargs)

    def test_unexpected_version(self):
        self.given_http_service_client("mock_endpoint", "mock_action")
        self.given_requests_post_returns_response(json.dumps({
            "status": "success",
            "data": {
                "version": "0.0",
            }
        }))
        self.when_perform_then_exception_is_raised_matching(
            action="mock_action",
            parameters=self._mock_parameter_bindings,
            session={'session_id': 'mock_session_id'},
            context=Context("mock_active_ddd", self._mock_facts(), "mock_invocation_id"),
            expected_exception=HttpServiceInvocationException,
            expected_message=r"Expected one of the supported versions \['1.0', '1.1'\] but got '0.0'"
        )

    def test_request_containing_confidence_scores(self):
        self.given_http_service_client("mock_endpoint", "MockValidator")
        self.given_requests_post_returns_response(
            json.dumps({
                "status": "success",
                "data": {
                    "version": PROTOCOL_VERSION,
                    "result": [{
                        "value": "mock_value",
                        "confidence": "mock_confidence",
                        "grammar_entry": "mock_grammar_entry"
                    }]
                }
            })
        )  # yapf: disable
        self.when_query(
            question=self.mock_wh_question("mock_question_predicate"),
            parameters=self._mock_parameter_bindings,
            min_results=0,
            max_results=None,
            session={'session_id': 'mock_session_id'},
            context=Context(
                "mock_active_ddd",
                self._mock_facts(
                    perception_confidence=0.5,
                    understanding_confidence=1.0,
                    weighted_confidence=0.6,
                    weighted_understanding_confidence=1.2
                ), "mock_invocation_id"
            )
        )
        self.then_result_is([QueryResultFromService("mock_value", "mock_confidence", "mock_grammar_entry")])
