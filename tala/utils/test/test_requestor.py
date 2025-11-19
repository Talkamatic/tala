from tala.utils import requestor


class TestGPTRequest:
    @classmethod
    def setup_class(cls):
        def make_request(*args):
            return args

        cls._original_make_request = requestor.make_request
        requestor.make_request = make_request
        requestor.REQUESTOR_URL = "URL-FOR-REQUESTOR"

    @classmethod
    def teardown_class(cls):
        requestor.make_request = cls._original_make_request

    def test_basic_call(self):
        self.given_gpt_request([{
            "role": "system",
            "content": "you are a JSON creator. You get descriptions of JSON structures in NL, and you create the JSON."
        }, {
            "role": "user",
            "content": "i want keys 1 2 3 with values a b c"
        }])
        self.when_request_is_made()
        self.then_request_call_is((
            'URL-FOR-REQUESTOR', {
                'gpt_request': {
                    'messages': [{
                        'role': 'system',
                        'content': 'you are a JSON creator. You get descriptions of JSON structures in NL, and you create the JSON.'
                    }, {
                        'role': 'user',
                        'content': 'i want keys 1 2 3 with values a b c'
                    }],
                    'temperature': 0.1,
                    'max_tokens': 50,
                    'max_retries': 0,
                    'stop': [],
                    'default_gpt_response': '[]',
                    'use_json': True,
                    'model': 'gpt-4o-2024-05-13'
                },
                'priority': 10,
                'request_id': 'some-request-id'
            }
        ))

    def given_gpt_request(self, messages=None, use_json=True):
        msgs = messages if messages else []
        request_id = "some-request-id"
        self._gpt_request = requestor.GPTRequest(messages=msgs, use_json=use_json, request_id=request_id)

    def when_request_is_made(self):
        self._gpt_request.make()

    def then_request_call_is(self, expected_response):
        self._then_request_is_done()
        response = self._gpt_request._response[0:2]
        assert response == expected_response, f'Expected "{expected_response}", got "{response}"'

    def _then_request_is_done(self):
        assert self._gpt_request._done.is_set()

    def test_call_with_added_messages_for_all_three_roles(self):
        self.given_gpt_request()
        self.given_system_message(
            'you are a JSON creator. You get descriptions of JSON structures in NL, and you create the JSON.'
        )
        self.given_user_message('i want keys 1 2 3 with values a b c')
        self.given_assistant_message('you wanted keys 1 2 3 with values a b c')
        self.when_request_is_made()
        self.then_request_call_is((
            'URL-FOR-REQUESTOR', {
                'gpt_request': {
                    'messages': [{
                        'role': 'system',
                        'content': 'you are a JSON creator. You get descriptions of JSON structures in NL, and you create the JSON.'
                    }, {
                        'role': 'user',
                        'content': 'i want keys 1 2 3 with values a b c'
                    }, {
                        'role': 'assistant',
                        'content': 'you wanted keys 1 2 3 with values a b c'
                    }],
                    'temperature': 0.1,
                    'max_tokens': 50,
                    'max_retries': 0,
                    'stop': [],
                    'default_gpt_response': '[]',
                    'use_json': True,
                    'model': 'gpt-4o-2024-05-13'
                },
                'priority': 10,
                'request_id': 'some-request-id'
            }
        ))

    def given_system_message(self, message):
        self._gpt_request.add_system_message(message)

    def given_user_message(self, message):
        self._gpt_request.add_user_message(message)

    def given_assistant_message(self, message):
        self._gpt_request.add_assistant_message(message)

    def test_call_using_text(self):
        self.given_gpt_request(use_json=False)
        self.given_system_message('you say hey to mom')
        self.given_user_message('say hey to mom')
        self.when_request_is_made()
        self.then_request_call_is((
            'URL-FOR-REQUESTOR', {
                'gpt_request': {
                    'messages': [{
                        'role': 'system',
                        'content': 'you say hey to mom'
                    }, {
                        'role': 'user',
                        'content': 'say hey to mom'
                    }],
                    'temperature': 0.1,
                    'max_tokens': 50,
                    'max_retries': 0,
                    'stop': [],
                    'default_gpt_response': '[]',
                    'use_json': False,
                    'model': 'gpt-4o-2024-05-13'
                },
                'priority': 10,
                'request_id': 'some-request-id'
            }
        ))

    def test_add_messages(self):
        self.given_gpt_request(use_json=False)
        self.given_messages([{
            'role': 'system',
            'content': 'you say hey to mom'
        }, {
            'role': 'user',
            'content': 'say hey to mom'
        }])
        self.when_request_is_made()
        self.then_request_call_is((
            'URL-FOR-REQUESTOR', {
                'gpt_request': {
                    'messages': [{
                        'role': 'system',
                        'content': 'you say hey to mom'
                    }, {
                        'role': 'user',
                        'content': 'say hey to mom'
                    }],
                    'temperature': 0.1,
                    'max_tokens': 50,
                    'max_retries': 0,
                    'stop': [],
                    'default_gpt_response': '[]',
                    'use_json': False,
                    'model': 'gpt-4o-2024-05-13'
                },
                'priority': 10,
                'request_id': 'some-request-id'
            }
        ))

    def given_messages(self, messages):
        self._gpt_request.add_messages(messages)

    def test_get_json_response(self):
        self.given_gpt_request(use_json=True)
        self.given_request_was_made()
        self.when_response_is({"response_body": '{"JSON": true}'})
        self.then_json_response_is({"JSON": True})

    def given_request_was_made(self):
        self._gpt_request.make()

    def when_response_is(self, response):
        self._gpt_request._response = response

    def then_json_response_is(self, expected_response):
        self._then_request_is_done()
        assert self._gpt_request.json_response == expected_response, f'Expected "{expected_response}", got "{self._gpt_request.json_response}"'

    def test_get_text_response_unquotes(self):
        self.given_gpt_request(use_json=False)
        self.given_request_was_made()
        self.when_response_is({"response_body": '"This is not JSON"'})
        self.then_text_response_is("This is not JSON")

    def then_text_response_is(self, expected_response):
        self._then_request_is_done()
        assert self._gpt_request.text_response == expected_response, f'Expected "{expected_response}", got "{self._gpt_request.text_response}"'
