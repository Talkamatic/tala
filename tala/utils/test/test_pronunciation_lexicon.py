import pytest

from tala.utils.pronunciation import Lexicon

BASIC_LEXICON = [{
    "type": "correction_entry",
    "id": "8726b03b272f90",
    "attributes": {
        "match": "utterance",
        "replacement": "spoken words"
    }
}, {
    "type": "correction_entry",
    "id": "8726b03b272f0",
    "attributes": {
        "match": "ddd_specific_entry",
        "replacement": "ddd_specific_replacement",
        "ddd_name": "some_ddd",
    }
}, {
    "type": "correction_entry",
    "id": "8726b03b272f05675",
    "attributes": {
        "match": "completely_specified_token",
        "replacement": "completely_specified_replacement",
        "ddd_name": "some_ddd",
        "voice": "some_voice",
        "locale": "some_locale",
    }
}]


class TestLexicon(object):
    def setup_method(self):
        pass

    def test_basic_succesful_lookup(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"token": "utterance"})
        self.when_correction_called()
        self.then_result_is("spoken words")

    def given_lexicon(self, lexicon):
        self._lexicon = Lexicon(lexicon)

    def given_input_data(self, input_data):
        self._input_data = input_data

    def when_correction_called(self):
        self._pronunciation = self._lexicon.generate_pronunciation_text(self._input_data)

    def then_result_is(self, expected_pronunciation):
        assert expected_pronunciation == self._pronunciation

    def test_empty_string_lookup(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"token": ""})
        self.when_correction_called()
        self.then_result_is("")

    def test_succesful_lookup_ddd_given_general_correction(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"token": "utterance", "ddd_name": "some_ddd"})
        self.when_correction_called()
        self.then_result_is("spoken words")

    def test_no_match_lookup(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"token": "token_not_in_lexicon"})
        self.when_correction_called()
        self.then_result_is("token_not_in_lexicon")

    def test_ddd_based_lookup(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"token": "ddd_specific_entry", "ddd_name": "some_ddd"})
        self.when_correction_called()
        self.then_result_is("ddd_specific_replacement")

    def test_ddd_based_lookup_wrong_ddd(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"token": "ddd_specific_entry", "ddd_name": "some_other_ddd"})
        self.when_correction_called()
        self.then_result_is("ddd_specific_entry")

    def test_ddd_based_lookup_voice_no_impact_if_not_in_lexicon_entry(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"token": "ddd_specific_entry", "ddd_name": "some_ddd", "voice": "some_voice"})
        self.when_correction_called()
        self.then_result_is("ddd_specific_replacement")

    def test_ddd_based_lookup_locale_no_impact_if_not_in_lexicon_entry(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"token": "ddd_specific_entry", "ddd_name": "some_ddd", "locale": "locale"})
        self.when_correction_called()
        self.then_result_is("ddd_specific_replacement")

    def test_ddd_based_lookup_all_parameters(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({
            "token": "completely_specified_token",
            "ddd_name": "some_ddd",
            "locale": "some_locale",
            "voice": "some_voice"
        })
        self.when_correction_called()
        self.then_result_is("completely_specified_replacement")

    @pytest.mark.parametrize("non_matching_param", ["ddd_name", "locale", "voice"])
    def test_ddd_based_lookup_all_parameters_fails_non_matching_param(self, non_matching_param):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({
            "token": "token_with_one_non_matching_param",
            "ddd_name": "some_ddd",
            "locale": "some_locale",
            "voice": "some_voice"
        })
        self.given_non_matching_param(non_matching_param)
        self.when_correction_called()
        self.then_result_is("token_with_one_non_matching_param")

    def given_non_matching_param(self, param):
        self._input_data[param] = "non_matching_value"

    def test_generate_replacement_dict(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"locale": "some_locale"})
        self.when_get_replacement_dict_called()
        self.then_result_is({"utterance": "spoken words"})

    def when_get_replacement_dict_called(self):
        self._pronunciation = self._lexicon.get_replacement_dict(self._input_data)

    def test_generate_replacement_dict_anything_goes(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"locale": "some_locale", "ddd_name": "other_name", "voice": "hmv"})
        self.when_get_replacement_dict_called()
        self.then_result_is({"utterance": "spoken words"})

    def test_generate_replacement_dict_ddd_and_locale(self):
        self.given_lexicon(BASIC_LEXICON)
        self.given_input_data({"locale": "some_locale", "ddd_name": "some_ddd", "voice": "hmv"})
        self.when_get_replacement_dict_called()
        self.then_result_is({'ddd_specific_entry': 'ddd_specific_replacement', 'utterance': 'spoken words'})
