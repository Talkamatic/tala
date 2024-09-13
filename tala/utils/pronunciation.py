TYPE = "type"
ATTRIBUTES = "attributes"
MATCH = "match"
TOKEN = "token"
REPLACEMENT = "replacement"
CORRECTION_ENTRY_TYPE = "correction_entry"
ATTRIBUTE_LIST = ["ddd_name", "voice", "language"]


class Lexicon:
    def __init__(self, entries):
        self._entries = entries

    def generate_pronunciation_text(self, input_entry):
        def is_correction_entry_matching(entry, token):
            return entry[TYPE] == CORRECTION_ENTRY_TYPE and entry[ATTRIBUTES][MATCH] == token

        def entry_matches_input(attributes, input_entry):
            def attribute_is_required(attribute):
                return attribute in attributes and attributes.get(attribute)

            for attribute in ATTRIBUTE_LIST:
                if attribute_is_required(attribute):
                    if attributes[attribute] != input_entry.get(attribute):
                        return False
            return True

        for entry in self._entries:
            if is_correction_entry_matching(entry, input_entry[TOKEN]):
                if entry_matches_input(entry[ATTRIBUTES], input_entry):
                    return entry[ATTRIBUTES][REPLACEMENT]
        return input_entry[TOKEN]
