from tala.utils.as_json import AsJSONMixin


class SemanticObject(AsJSONMixin):
    def is_yes(self):
        return False

    def is_no(self):
        return False

    def is_individual(self):
        return False

    def is_proposition(self):
        return False

    def is_question(self):
        return False

    def is_action(self):
        return False

    def is_goal(self):
        return False

    def is_plan_item(self):
        return False

    def is_predicate_proposition(self):
        return False

    def is_proposition_set(self):
        return False

    def is_lambda_abstracted_predicate_proposition(self):
        return False

    def is_lambda_abstracted_goal_proposition(self):
        return False

    def is_lambda_abstracted_domain_proposition(self):
        return False

    def is_move(self):
        return False

    def is_predicate(self):
        return False

    @property
    def ontology_name(self):
        message = "%s derives from %s and does not have an ontology name. Use %s instead." % (
            self, SemanticObject.__name__, OntologySpecificSemanticObject.__name__
        )
        raise NotImplementedError(message)

    def is_ontology_specific(self):
        return False

    def has_semantic_content(self):
        return False

    def __repr__(self):
        return repr(self.__dict__)


class OntologySpecificSemanticObject(SemanticObject):
    def __init__(self, ontology_name):
        self._ontology_name = ontology_name

    @property
    def ontology_name(self):
        return self._ontology_name

    def is_ontology_specific(self):
        return True


class SemanticObjectWithContent(SemanticObject):
    def __init__(self, content):
        self._content = content

    @property
    def ontology_name(self):
        return self._content.ontology_name

    def is_ontology_specific(self):
        return self._content.is_ontology_specific()

    def has_semantic_content(self):
        return True
