from tala.model.polarity import Polarity


class HttpFormatter(object):
    def __init__(self, ddd_component_manager):
        self._ddd_component_manager = ddd_component_manager

    def facts_to_json_object(self, facts, session):
        return {
            proposition.getPredicate().get_name(): self.fact_to_json_object(proposition, session)
            for proposition in facts
            if proposition.is_predicate_proposition() and proposition.get_polarity() == Polarity.POS
        }

    def fact_to_json_object(self, proposition, session):
        def get_grammar_entry(value):
            if "entities" in session:
                for entity in session["entities"]:
                    if entity["name"] == value:
                        return entity["natural_language_form"]
            return None

        if proposition is None:
            return None
        individual = proposition.getArgument()
        if individual is None:
            return None
        value = individual.getValue()
        value_as_json = individual.value_as_json_object()
        grammar_entry = get_grammar_entry(value)
        resulting_dict = {
            "sort": proposition.getPredicate().getSort().get_name(),
            "grammar_entry": grammar_entry,
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
        resulting_dict.update(value_as_json)
        return resulting_dict
