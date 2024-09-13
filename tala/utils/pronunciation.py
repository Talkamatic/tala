TYPE = "type"
ATTRIBUTES = "attributes"
MATCH = "match"
TOKEN = "token"
REPLACEMENT = "replacement"
CORRECTION_ENTRY_TYPE = "correction_entry"
ATTRIBUTE_LIST = ["ddd_name", "voice", "locale"]


def is_correction_entry_matching(entry, token):
    return entry[TYPE] == CORRECTION_ENTRY_TYPE and entry[ATTRIBUTES][MATCH] == token


def entry_matches_input(dict_attributes, input_entry):
    def attribute_is_required(attribute):
        if attribute in dict_attributes and dict_attributes.get(attribute):
            return True
        return False

    for attribute in ATTRIBUTE_LIST:
        if attribute_is_required(attribute):
            if dict_attributes[attribute] != input_entry.get(attribute):
                return False
    return True


class Lexicon:
    def __init__(self, entries):
        self._entries = entries

    def generate_pronunciation_text(self, input_entry):
        for entry in self._entries:
            if is_correction_entry_matching(entry, input_entry[TOKEN]):
                if entry_matches_input(entry[ATTRIBUTES], input_entry):
                    return entry[ATTRIBUTES][REPLACEMENT]
        return input_entry[TOKEN]

    def _create_replacements(self, input_entry):
        for entry in self._entries:
            if entry_matches_input(entry[ATTRIBUTES], input_entry):
                yield entry[ATTRIBUTES][MATCH], entry[ATTRIBUTES][REPLACEMENT]

    def get_replacement_dict(self, input_entry):
        return {k: v for k, v in self._create_replacements(input_entry)}
