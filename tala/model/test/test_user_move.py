import pytest

from tala.model import user_move


class TestUserMove:
    def test_create_ddd_specific_user_move_from_json(self):
        self.given_user_move_as_json({
            'ddd': 'some-ddd',
            'perception_confidence': 1.0,
            'semantic_expression': 'ask(?X.qna_response(X))',
            'understanding_confidence': 1.0,
        })
        self.when_create_user_move()
        self.then_move_as_dict_equals_original_goal()

    def given_user_move_as_json(self, json_dict):
        self._move_as_json_dict = json_dict

    def when_create_user_move(self):
        self._user_move = user_move.create(self._move_as_json_dict)

    def then_move_as_dict_equals_original_goal(self):
        assert self._move_as_json_dict == self._user_move.as_dict()

    def test_create_non_ddd_specific_user_move_from_json(self):
        self.given_user_move_as_json({
            'perception_confidence': 1.0,
            'semantic_expression': 'ask(?X.qna_response(X))',
            'understanding_confidence': 1.0,
        })
        self.when_create_user_move()
        self.then_move_as_dict_equals_original_goal()


class TestProperMove:
    def test_standard_answer_move(self):
        self.given_move_as_string('answer(user_character(stupid))')
        self.when_creating_move()
        self.then_move_is({"move_type": user_move.ANSWER, "predicate": "user_character", "individual": "stupid"})

    def given_move_as_string(self, move):
        self._move_as_string = move

    def when_creating_move(self):
        self._proper_move = user_move.ProperMove(self._move_as_string)

    def then_move_is(self, expected_move_as_json):
        assert self._proper_move.as_json() == expected_move_as_json

    def test_string_answer_move(self):
        self.given_move_as_string('answer(user_name("Fredrik"))')
        self.when_creating_move()
        self.then_move_is({"move_type": user_move.ANSWER, "predicate": "user_name", "individual": "\"Fredrik\""})

    def test_string_answer_move_with_spaces(self):
        self.given_move_as_string('answer(user_name("Fredrik Kronlid"))')
        self.when_creating_move()
        self.then_move_is({
            "move_type": user_move.ANSWER,
            "predicate": "user_name",
            "individual": "\"Fredrik Kronlid\""
        })

    def test_nullary_answer_move(self):
        self.given_move_as_string('answer(should_succeed)')
        self.when_creating_move()
        self.then_move_is({"move_type": user_move.ANSWER, "predicate": "should_succeed", "individual": None})

    def test_unary_ask_move(self):
        self.given_move_as_string('ask(?X.hallon(X))')
        self.when_creating_move()
        self.then_move_is({"move_type": user_move.ASK, "predicate": "hallon", "arity": 1})

    def test_nullary_ask_move(self):
        self.given_move_as_string('ask(?hallon_petunia)')
        self.when_creating_move()
        self.then_move_is({"move_type": user_move.ASK, "predicate": "hallon_petunia", "arity": 0})

    def test_request_move(self):
        self.given_move_as_string('request(some_action)')
        self.when_creating_move()
        self.then_move_is({"move_type": user_move.REQUEST, "action": "some_action"})

    @pytest.mark.parametrize(
        "move_as_string, move_type", [
            ("thanks", "thanks"),
            ("greet", "greet"),
            ("insult", "insult"),
            ("icm:per*neg", "icm:per*neg"),
            ("icm:acc*pos", "icm:acc*pos"),
        ]
    )
    def test_builtins(self, move_as_string, move_type):
        self.given_move_as_string(move_as_string)
        self.when_creating_move()
        self.then_move_is({"move_type": move_type})

    @pytest.mark.parametrize(
        "move_as_string", ["request(some_action", 'ask(X.hallon(X))', "answer(user_name('Fredrik'))", "astrakan"]
    )
    def test_bad_input(self, move_as_string):
        self.given_move_as_string(move_as_string)
        with pytest.raises(user_move.MalformedMoveStringException):
            self.when_creating_move()
