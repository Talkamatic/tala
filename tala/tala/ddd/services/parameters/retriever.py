from tala.ddd.services.service_interface import ParameterField, ParameterNotFoundException
from tala.ddd.services.parameters.binding import SingleInstanceParameterBinding, MultiInstanceParameterBinding


class MissingRequiredParameterException(Exception):
    pass


class UnexpectedNumberOfFactsException(Exception):
    pass


class ParameterRetriever(object):
    def __init__(self, service_interface, ontology):
        super(ParameterRetriever, self).__init__()
        self._service_interface = service_interface
        self._ontology = ontology

    def preprocess_validity_arguments(self, name, facts, session):
        validator = self._service_interface.get_validator(name)
        return self.preprocess_arguments(validator.parameters, facts, session)

    def preprocess_query_arguments(self, name, facts, session):
        query = self._service_interface.get_query(name)
        return self.preprocess_arguments(query.parameters, facts, session)

    def preprocess_action_arguments(self, name, facts, session):
        action = self._service_interface.get_action(name)
        return self.preprocess_arguments(action.parameters, facts, session)

    def preprocess_arguments(self, parameters, facts, session):
        return [self.preprocess_argument(parameter, facts, session) for parameter in parameters]

    def preprocess_argument(self, parameter, facts, session):
        def single_instance_parameter_binding(parameter_facts):
            if len(parameter_facts) == 0:
                return single_instance_parameter_binding_without_fact()
            elif len(parameter_facts) == 1:
                return single_instance_parameter_binding_with_fact(parameter_facts[0])
            else:
                raise UnexpectedNumberOfFactsException(
                    f"Expected 0 or 1 facts for predicate {parameter.name} but got {len(parameter_facts)}: "
                    f"{parameter_facts}"
                )

        def single_instance_parameter_binding_without_fact():
            if not parameter.is_optional:
                raise ParameterNotFoundException("failed to get argument '%s'" % parameter.name)
            return SingleInstanceParameterBinding(parameter=parameter, value=None, proposition=None)

        def single_instance_parameter_binding_with_fact(proposition):
            value = self._get_argument_value(parameter, proposition, session)
            return SingleInstanceParameterBinding(parameter, value, proposition)

        parameter_facts = list(self.get_facts_by_predicate_name(parameter.name, facts))
        predicate = self._ontology.get_predicate(parameter.name)
        if predicate.allows_multiple_instances():
            values = [self._get_argument_value(parameter, fact, session) for fact in parameter_facts]
            return MultiInstanceParameterBinding(parameter, values, parameter_facts)
        return single_instance_parameter_binding(parameter_facts)

    def _get_argument_value(self, parameter, fact, session):
        def get_grammar_entry_for_value_of_custom_sort(value):
            try:
                entities = session["entities"]
                for entity in entities:
                    if entity["name"] == value:
                        return entity["natural_language_form"]
            except KeyError:
                return None

        individual = fact.getArgument()
        sort = individual.getSort()
        value = individual.getValue()
        if parameter.format == ParameterField.VALUE:
            return sort.value_as_basic_type(value)
        elif parameter.format == ParameterField.GRAMMAR_ENTRY:
            if sort.is_builtin():
                return None
            else:
                return get_grammar_entry_for_value_of_custom_sort(value)
        else:
            raise Exception("unknown parameter field %r" % parameter.format)

    @classmethod
    def get_facts_by_predicate_name(cls, predicate_name, facts):
        for fact in cls.positive_predicate_proposition_facts(facts):
            if fact.getPredicate().get_name() == predicate_name:
                yield fact

    @classmethod
    def predicate_names_of_facts(cls, facts):
        predicate_facts = cls.positive_predicate_proposition_facts(facts)
        return [fact.getPredicate().get_name() for fact in predicate_facts]

    @staticmethod
    def positive_predicate_proposition_facts(facts):
        for fact in facts:
            if fact.is_predicate_proposition() and fact.is_positive():
                yield fact
