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
