from tala.model.interpretation import Interpretation


class TestInterpretation:
    def test_create_ddd_specific_user_move_from_json(self):
        self.given_interpretation_as_dict({
            'moves': [{
                'ddd': 'some-ddd',
                'perception_confidence': 1.0,
                'semantic_expression': 'ask(?X.qna_response(X))',
                'understanding_confidence': 1.0,
            }],
            'utterance': 'some-utterance',
            'perception_confidence': 1.01,
            'modality': 'speech'
        })
        self.when_create_interpretation()
        self.then_interpretation_as_dict_equals_original_dict()

    def given_interpretation_as_dict(self, json_dict):
        self._interpretation_as_json_dict = json_dict

    def when_create_interpretation(self):
        self._interpretation = Interpretation.from_dict(self._interpretation_as_json_dict)

    def then_interpretation_as_dict_equals_original_dict(self):
        assert self._interpretation_as_json_dict == self._interpretation.as_dict()
