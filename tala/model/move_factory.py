from tala.model.speaker import Speaker
from tala.model.move import AnswerMove, AskMove, RequestMove
from tala.model.question import WhQuestion


class DddSpecificMoveFactory(object):
    def __init__(self, ddd):
        self._ddd = ddd

    def create_from_dict(self, move_as_dict, language_code):
        type_ = move_as_dict["type"]
        if type_ == "answer":
            move = self._create_answer_move_and_potentially_add_it_to_entity_db(move_as_dict, language_code)
        elif type_ == "ask":
            move = self._create_ask_move(move_as_dict)
        elif type_ == "request":
            move = self._create_request_move(move_as_dict)
        else:
            raise Exception("create_from_dict does not support move type: %s" % type_)
        score = self._get_score_from_move_as_dict(move_as_dict)
        utterance = self._get_utterance_from_move_as_dict(move_as_dict)
        move.set_realization_data(
            speaker=Speaker.USR,
            perception_confidence=score,
            understanding_confidence=1.0,
            utterance=utterance,
            ddd_name=self._ddd.name)
        return move

    def _create_answer_move_and_potentially_add_it_to_entity_db(self, move_as_dict, language_code):
        sort = self._get_sort_for_answer_move(move_as_dict, self._ddd)
        value = self._get_value_for_answer_move_and_potentially_add_it_to_entity_db(move_as_dict, sort, language_code)
        individual = self._ddd.ontology.create_individual(value, sort)
        return AnswerMove(individual)

    def _get_sort_for_answer_move(self, move_as_dict, ddd):
        if "sort" not in move_as_dict:
            predicate = ddd.ontology.get_predicate(move_as_dict["predicate"])
            sort = predicate.getSort()
        else:
            sort_name = move_as_dict["sort"]
            sort = ddd.ontology.get_sort(sort_name)
        return sort

    def _get_value_for_answer_move_and_potentially_add_it_to_entity_db(self, move_as_dict, sort, language_code):
        if sort.is_dynamic() and "grammar_entry" in move_as_dict:
            grammar_entry = move_as_dict["grammar_entry"]
            sort_name = sort.get_name()
            entity_db = self._ddd.entity_dbs[language_code]
            if "value" in move_as_dict:
                name = move_as_dict["value"]
                value = entity_db.add_entity(sort=sort_name, grammar_entry=grammar_entry, name=name)
            else:
                value = entity_db.add_entity(sort=sort_name, grammar_entry=grammar_entry)
        else:
            value = move_as_dict["value"]
        return value

    def _create_ask_move(self, move_as_dict):
        predicate = self._ddd.ontology.get_predicate(move_as_dict["predicate"])
        lambda_abstracted_predicate_proposition = self._ddd.ontology.create_lambda_abstracted_predicate_proposition(predicate)
        question = WhQuestion(lambda_abstracted_predicate_proposition)
        return AskMove(question)

    def _create_request_move(self, move_as_dict):
        action = self._ddd.ontology.create_action(move_as_dict["action"])
        return RequestMove(action)

    def _get_score_from_move_as_dict(self, move_as_dict):
        key = "score"
        return float(move_as_dict[key]) if key in move_as_dict else 1.0

    def _get_utterance_from_move_as_dict(self, move_as_dict):
        if "utterance" in move_as_dict:
            return move_as_dict['utterance']
        else:
            return None
