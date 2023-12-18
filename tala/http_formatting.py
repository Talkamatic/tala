from tala.model.polarity import Polarity


class HTTPFormatter(object):
    def facts_to_json_object(self, facts, session):
        def positive_predicate_proposition(proposition):
            return proposition.is_predicate_proposition() and proposition.get_polarity() == Polarity.POS

        return {
            proposition.predicate.get_name(): self.fact_to_json_object(proposition, session)
            for proposition in facts if positive_predicate_proposition(proposition)
        }

    def fact_to_json_object(self, proposition, session):
        def get_grammar_entry(value):
            if "entities" in session:
                for entity in session["entities"]:
                    if entity["name"] == value:
                        return entity["natural_language_form"]
            return None

        if proposition is None or proposition.individual is None:
            return None

        resulting_dict = {
            "sort": proposition.predicate.sort.get_name(),
            "grammar_entry": get_grammar_entry(proposition.individual.value),
            "perception_confidence":
                proposition.confidence_estimates.perception_confidence if proposition.confidence_estimates else None,
            "understanding_confidence":
                proposition.confidence_estimates.understanding_confidence if proposition.confidence_estimates else None,
            "weighted_confidence":
                proposition.confidence_estimates.weighted_confidence if proposition.confidence_estimates else None,
            "weighted_understanding_confidence":
                proposition.confidence_estimates.weighted_understanding_confidence
                if proposition.confidence_estimates else None
        }  # yapf: disable

        resulting_dict.update(proposition.individual.value_as_json_object())

        return resulting_dict


class HttpFormatter(HTTPFormatter):
    def __init__(self, _dummy):
        pass
