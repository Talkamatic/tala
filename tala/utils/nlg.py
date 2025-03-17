import re
import random
from string import Formatter

from tala.utils.func import log_models
from tala.utils.compression import ensure_decompressed_json

PROTOCOL_VERSION = "1.0"

SUCCESS = "success"
FAIL = "fail"
ERROR = "error"
VALID_STATUSES = [SUCCESS, FAIL, ERROR]

RERAISE_SV = "Så "
RERAISE_EN = "So "

ICM_SLOT_PATTERN = r'icm:per\*pos\:(.*)'
PROPOSITIONAL_SLOT_PATTERN = r'(\$[a-zA-Z0-9_]+)'
STRING_ANSWER_PATTERN = r'[a-zA-Z0-9_]+\(\"([^"]*)\"\)'
INDIVIDUAL_SLOT = "&individual"
PREDICATE_WILDCARD = "*predicate"
PROPOSITION_SET_WILDCARD = "*proposition_set"
VALIDITY_WILDCARD = "*validity"


class SlotDefinitionException(Exception):
    def __init__(self, message):
        super().__init__()
        self._message = message

    @property
    def message(self):
        return self._message


class NoMoveSequenceFoundException(Exception):
    pass


def get_predicate(proposition_expression):
    m = re.match(r"([a-zA-Z0-9_]+)\(.*", proposition_expression)
    if m:
        return m.groups()[0]


def list_of_strings_to_string(list_of_strings):
    def quote_string(string):
        return "'" + string + "'"

    def quote_strings(list_of_strings):
        return [quote_string(string) for string in list_of_strings]

    return "[" + (", ".join(quote_strings(list_of_strings))) + "]"


def generate(moves, context, session, logger):
    moves = [{"semantic_expression": move} for move in moves]

    request = {"moves": moves, "context": context, "session": session}
    result = nlg(request, logger)
    logger.info("generate() returns", result=result)
    return result


def generate_utterance(moves, context, session, logger):
    result = generate(moves, context, session, logger)
    if result["status"] == SUCCESS:
        return result["utterance"]
    return ""


def nlg(body, logger):
    def get_nlg_model():
        try:
            if body.get("nlg"):
                logger.debug("Collecting NLG data from the request")
                nlg_model = body["nlg"]
            if "session" in body and body["session"].get("nlg"):
                logger.debug("Collecting NLG data from the session object")
                nlg_model = body["session"].get("nlg")

            return ensure_decompressed_json(nlg_model)
        except UnboundLocalError as e:
            logger.warning("No NLG model could be found in the request body or the session object", error=e)

    def lowercase_question_with_reraise_sw_en(utterance):
        for target_token in [RERAISE_EN, RERAISE_SV]:
            if target_token in utterance:
                index = utterance.find(target_token) + len(target_token)
                utterance = utterance[:index] + utterance[index].lower() + utterance[index + 1:]
                return utterance
        return utterance

    def decide_persona(utterances):
        for utterance in utterances:
            persona = utterance.get("persona", "tutor")
            if persona is not None:
                return persona
        return None

    def get_voice(nlg_data, utterance_persona):
        persona = nlg_data["personas"].get(utterance_persona, {})
        return persona.get("voice")

    def make_and_log_response(response):
        try:
            if "_" in response["utterance"]:
                logger.warning("response contains an underscore character: _", utterance=response["utterance"])
        except Exception:
            pass
        logger.info("responding", response=response)
        return response

    def get_facts():
        return body.get("context", {}).get("facts", {})

    def get_facts_being_grounded():
        return body.get("context", {}).get("facts_being_grounded", {})

    def get_entities_under_discussion():
        return body.get("context", {}).get("entities_under_discussion", {})

    log_models(body, logger, ["nlg"])
    logger.info("incoming request", body=body)
    moves = [move["semantic_expression"] for move in body["moves"]]

    nlg_data = get_nlg_model()
    if not nlg_data:
        return make_and_log_response(
            response={
                "status": FAIL,
                "message": "No NLG model could be found in the request body or the session object"
            }
        )

    g = Generator(nlg_data, get_facts(), get_facts_being_grounded(), get_entities_under_discussion(), logger)

    try:
        utterance = g.generate_sequence(moves)
        persona = utterance.get("persona", "tutor")
        return make_and_log_response(
            response={
                "status": SUCCESS,
                "utterance": utterance["utterance"],
                "persona": persona,
                "voice": get_voice(nlg_data, persona)
            }
        )
    except NoMoveSequenceFoundException:
        pass
    try:
        utterances = list(g.generate(move) for move in moves)
        logger.debug("utterances", utterances=utterances)
        clean_utterances = [utterance for utterance in utterances if utterance["utterance"]]
        final_utterance = " ".join(utterance["utterance"] for utterance in clean_utterances)
        potentially_lowercased_utterance = lowercase_question_with_reraise_sw_en(final_utterance)
        logger.debug(
            "potentially_lowercased_utterance", potentially_lowercased_utterance=potentially_lowercased_utterance
        )
        if potentially_lowercased_utterance == "":
            return make_and_log_response(
                response={
                    "status": FAIL,
                    "message": f"moves {moves} was generated as the empty string."
                }
            )
    except SlotDefinitionException as exception:
        logger.warning(exception.message)
        return make_and_log_response(response={"status": FAIL, "message": exception.message})
    persona = decide_persona(utterances)
    return make_and_log_response(
        response={
            "status": SUCCESS,
            "utterance": potentially_lowercased_utterance,
            "persona": persona,
            "voice": get_voice(nlg_data, persona)
        }
    )


class Generator:
    def __init__(self, nlg_data, facts, facts_being_grounded, entities_under_discussion, logger):
        self._facts = facts
        self._nlg_data = nlg_data
        self._facts_being_grounded = facts_being_grounded
        self._entities_under_discussion = entities_under_discussion
        self._logger = logger

    def generate_sequence(self, moves):
        moves_as_string = list_of_strings_to_string(moves)
        sequence_content = self._nlg_data.get(moves_as_string)
        if sequence_content:
            utterance = self._select_candidate_utterance_from_string(sequence_content["utterance"])
            sequence_content["utterance"] = utterance
            return sequence_content
        raise NoMoveSequenceFoundException(f"no sequence matching '{moves}' found")

    def generate(self, move):
        def _is_move_in_patterns_with_exact_match(nlg_data_doc):
            if nlg_data_doc:
                return True
            return False

        nlg_data_doc = self._nlg_data.get(move)
        if _is_move_in_patterns_with_exact_match(nlg_data_doc):
            utterance = self._handle_utterance_possibly_with_og_slots(nlg_data_doc["utterance"])
            if "_" in utterance:
                self._logger.warning("base case: move in mappings", utterance=utterance)
            return {"utterance": utterance, "persona": nlg_data_doc.get("persona")}

        self._logger.debug("move is not exact match, try slots.")
        slot_pattern = self._get_generalized_slot_pattern(move)
        self._logger.debug("slot_pattern", slot_pattern)
        nlg_data_doc = self._nlg_data.get(slot_pattern)

        if nlg_data_doc:
            self._logger.debug("calling _handle_utterance_with_ng_slots", nlg_data_doc["utterance"])
            utterance = self._handle_utterance_with_ng_slots(nlg_data_doc["utterance"])
            if "_" in utterance:
                self._logger.warning("base case: move in mappings", utterance=utterance)
            return {"utterance": utterance, "persona": nlg_data_doc.get("persona")}

        for population_function in [
            self._populate_predicate_and_validity_patterns,
            self._populate_proposition_set_patterns,
            self._populate_validity_patterns,
            self._populate_individual_slot_patterns,
            self._populate_propositional_slot_patterns,
            self._populate_icm_references,
            self._get_string_from_string_answer_move,
        ]:
            result = population_function(move)
            if result and result["utterance"] is not None:
                if "_" in result:
                    self._logger.warning(f"{population_function.__name__} applied to utterance", utterance=result)
                return result
        self._logger.warning(f"The move '{move}' was not found in the database. Generating the empty string.")

        return {"utterance": "", "persona": None}

    def _get_generalized_slot_pattern(self, move):
        self._logger.debug("_get_generalized_slot_pattern for move", move)
        m = re.match(r'(answer\([a-zA-Z0-9_]+\()[a-zA-Z0-9_]+(\)\))', move)
        if m:
            replacement = m.group(1) + "*" + m.group(2)
            self._logger.debug("replacing", move, "with", replacement)
            return replacement

    def _handle_utterance_possibly_with_og_slots(self, utterance_candidates):
        utterance = self._select_candidate_utterance_from_string(utterance_candidates)
        return self._populate_slots_in(utterance)

    def _handle_utterance_with_ng_slots(self, utterance_candidates):
        def is_utterance_with_ng_slots(utterance):
            fields = list(Formatter().parse(utterance))
            if len(fields) > 1:
                self._fields = fields
                return True
            return False

        utterance = self._select_candidate_utterance_from_string(utterance_candidates)
        return self._populate_ng_slots_in(utterance)

    def _populate_ng_slots_in(self, utterance):
        def all_facts_dict():
            return self._facts | self._facts_being_grounded | self._entities_under_discussion

        def create_filler_dict():
            d = {}
            all_facts = all_facts_dict()
            for predicate_name in all_facts:
                d[predicate_name] = grammar_entry(predicate_name, all_facts)
            return d

        def grammar_entry(entry, all_facts):
            if all_facts[entry].get("grammar_entry", None):
                return all_facts[entry].get("grammar_entry", None)
            if all_facts[entry]["sort"] in ["integer", "real"]:
                return all_facts[entry].get("value")
            individual = all_facts[entry].get("value", None)
            result = self.generate(f"answer({individual})")
            return result["utterance"]

        filler_dict = create_filler_dict()
        return utterance.format_map(filler_dict)

    def _select_candidate_utterance_from_string(self, candidates):
        candidate_utterances = candidates.split("|")
        return self._select_candidate_from_utterances(candidate_utterances)

    def _select_candidate_from_utterances(self, utterances):
        selected_utterance = random.choice(utterances)
        stripped_utterance = selected_utterance.strip()
        return stripped_utterance

    def _populate_slots_in(self, utterance):
        def get_predicate_from_slot(slot_definition):
            m = re.match(r"@([a-zA-Z0-9_]+)", slot_definition)
            if m:
                return m.groups()[0]

        def get_slot_definition(utterance):
            m = re.search(r'(@[a-zA-Z0-9_]+)', utterance)
            if m:
                match = m.groups()[0]
                return match
            return None

        slot_definition = get_slot_definition(utterance)
        if slot_definition is None:
            return utterance
        predicate = get_predicate_from_slot(slot_definition)
        grammar_entry = self._get_grammar_entry_for(predicate)
        return utterance.replace(slot_definition, grammar_entry)

    def _get_matcher_pattern_for(self, move_pattern, slot_definitions):
        replacement = "(.*)"
        escaped_move_pattern = re.escape(move_pattern)
        matcher_pattern = escaped_move_pattern
        for slot_definition in slot_definitions:
            escaped_slot_definition = re.escape(slot_definition)
            matcher_pattern = matcher_pattern.replace(escaped_slot_definition, replacement)
        return matcher_pattern

    def _get_grammar_entry_for(self, predicate):
        for collection in [self._facts, self._facts_being_grounded, self._entities_under_discussion]:
            if predicate in collection:
                if collection[predicate]["sort"] == "string":
                    return collection[predicate]["value"]
                if collection[predicate].get("grammar_entry", None) is not None:
                    return collection[predicate]["grammar_entry"]
                return collection[predicate]["value"]
        self._logger.warning(f"Expected predicate with entry in context, but got '{predicate}'.")
        return ""

    def _replace_slot(self, utterance_pattern, slot_reference, grammar_entry):
        utterance = utterance_pattern.replace(slot_reference, grammar_entry)
        return utterance

    def _pattern_matches_move(self, pattern, move, slot_references):
        re_pattern = self._get_matcher_pattern_for(pattern, slot_references)
        match_object = re.match(re_pattern, move)
        return match_object

    def _populate_predicate_and_validity_patterns(self, move):
        for entry in self._nlg_data["validity_wildcard_entries"]["docs"]:
            if VALIDITY_WILDCARD in entry["match"] and PREDICATE_WILDCARD in entry["match"]:
                matches_predicate = self._pattern_matches_move(
                    entry["match"], move, [PREDICATE_WILDCARD, VALIDITY_WILDCARD]
                )
                if matches_predicate:
                    return {"utterance": entry["utterance"], "persona": entry.get("persona")}

        for entry in self._nlg_data["predicate_wildcard_entries"]["docs"]:
            if VALIDITY_WILDCARD in entry["match"] and PREDICATE_WILDCARD in entry["match"]:
                matches_predicate = self._pattern_matches_move(
                    entry["match"], move, [PREDICATE_WILDCARD, VALIDITY_WILDCARD]
                )
                if matches_predicate:
                    return {"utterance": entry["utterance"], "persona": entry.get("persona")}

    def _populate_validity_patterns(self, move):
        for entry in self._nlg_data["validity_wildcard_entries"]["docs"]:
            if VALIDITY_WILDCARD in entry["match"]:
                if self._pattern_matches_move(entry["match"], move, [VALIDITY_WILDCARD]):
                    return {"utterance": entry["utterance"], "persona": entry.get("persona")}

    def _populate_proposition_set_patterns(self, move):
        for entry in self._nlg_data["proposition_set_wildcard_entries"]["docs"]:
            if PROPOSITION_SET_WILDCARD in entry["match"]:
                if self._pattern_matches_move(entry["match"], move, [PROPOSITION_SET_WILDCARD]):
                    return {"utterance": entry["utterance"], "persona": entry.get("persona")}

    def _populate_individual_slot_patterns(self, move):
        def populate_pattern_with_individual_slots(utterance_pattern, move_pattern, propositional_slot):
            re_pattern = self._get_matcher_pattern_for(move_pattern, [propositional_slot])
            match_object = re.match(re_pattern, move)
            if match_object:
                proposition_expression = match_object.group(1)
                predicate = get_predicate(proposition_expression)
                grammar_entry = self._get_grammar_entry_for(predicate)
                result = self._replace_slot(utterance_pattern, INDIVIDUAL_SLOT, grammar_entry)
                return result

        def get_propositional_slot_reference_for_individual(pattern):
            m = re.search(r'([a-zA-Z0-9_]+\(' + INDIVIDUAL_SLOT + r'\))', pattern)
            if m:
                match = m.groups()[0]
                return match
            return None

        for entry in self._nlg_data["individual_entries"]["docs"]:
            utterance_pattern = entry["utterance"]
            propositional_slot_for_individual = get_propositional_slot_reference_for_individual(entry["match"])
            if propositional_slot_for_individual is not None:
                if self._pattern_matches_move(entry["match"], move, ["&individual"]):
                    if INDIVIDUAL_SLOT in entry["match"] and INDIVIDUAL_SLOT not in utterance_pattern:
                        return {"utterance": utterance_pattern, "persona": entry.get("persona")}
                    result_utterance = populate_pattern_with_individual_slots(
                        utterance_pattern, entry["match"], propositional_slot_for_individual
                    )
                    return {"utterance": result_utterance, "persona": entry.get("persona")}

    def _populate_propositional_slot_patterns(self, move):
        def populate_pattern_with_propositional_slots(utterance_pattern, move_pattern, slot_definition):
            re_pattern = self._get_matcher_pattern_for(move_pattern, [slot_definition])
            match_object = re.match(re_pattern, move)
            if match_object:
                proposition_expression = match_object.group(1)
                predicate = get_predicate(proposition_expression)
                grammar_entry = self._get_grammar_entry_for(predicate)
                if grammar_entry == "":
                    self._logger.warning(f"Expected move with entry in context, but got '{move}'.")
                    return ""
                return self._replace_slot(utterance_pattern, slot_definition, grammar_entry)

        for entry in self._nlg_data["propositional_entries"]["docs"]:
            slot_reference = self._get_propositional_slot_reference_for(entry["match"])
            if slot_reference:
                utterance_pattern = entry["utterance"]
                if slot_reference in entry["match"] and slot_reference not in utterance_pattern:
                    raise SlotDefinitionException(
                        f"Expected '{entry['match']}' and '{utterance_pattern}' to contain same slot."
                    )
                if self._pattern_matches_move(entry["match"], move, [slot_reference]):
                    result_utterance = populate_pattern_with_propositional_slots(
                        utterance_pattern, entry["match"], slot_reference
                    )
                    return {"utterance": result_utterance, "persona": entry.get("persona")}

    def _get_propositional_slot_reference_for(self, pattern):
        m = re.search(PROPOSITIONAL_SLOT_PATTERN, pattern)
        if m:
            match = m.groups()[0]
            return match
        return None

    def _populate_icm_references(self, move):
        def get_icm_slot_reference_for(match):
            m = re.search(ICM_SLOT_PATTERN, match)
            if m:
                match = m.groups()[0]
                return match
            return None

        def populate_pattern_with_string(entry, icm_slot_reference, move):
            utterance_pattern = entry["utterance"]
            re_pattern = self._get_matcher_pattern_for(entry["match"], [icm_slot_reference])
            match_object = re.match(re_pattern, move)
            if match_object:
                embedded_string = match_object.group(1)
                result = self._replace_slot(utterance_pattern, icm_slot_reference, embedded_string)
                return result

        for entry in self._nlg_data["icm_slot_entries"]["docs"]:
            icm_slot_reference = get_icm_slot_reference_for(entry["match"])
            if icm_slot_reference is not None \
               and self._pattern_matches_move(entry["match"], move, [icm_slot_reference]):
                result_utterance = populate_pattern_with_string(entry, icm_slot_reference, move)
                return {"utterance": result_utterance, "persona": entry.get("persona")}

    def _get_string_from_string_answer_move(self, move):
        m = re.search(STRING_ANSWER_PATTERN, move)
        if m:
            match = m.groups()[0]
            return {"utterance": match, "persona": None}
        return None
