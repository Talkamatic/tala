from tala.model.stack import Stack
from tala.model.plan_item import PlanItem
from tala.model.semantic_object import SemanticObject


class UnableToDetermineOntologyException(Exception):
    pass


class Plan(Stack, SemanticObject):
    def __init__(self, content=set(), contentclass=None):
        Stack.__init__(self, content=content, contentclass=contentclass)
        SemanticObject.__init__(self)

    def is_ontology_specific(self):
        if not all([proposition.is_ontology_specific() for proposition in self.content]):
            return False
        if not self._ontology_names:
            return False
        return self._are_all_propositions_from_same_ontology()

    def _are_all_propositions_from_same_ontology(self):
        return len(self._ontology_names) < 2

    @property
    def ontology_name(self):
        if not self._ontology_names:
            raise UnableToDetermineOntologyException("Expected semantic content but found none")

        if self.is_ontology_specific():
            return self._ontology_names.pop()

        message = "Expected all propositions %s\n\nin ontology %s\n\nbut they're from %s" % (
            self.content, self.content[0].ontology_name, self._ontology_names
        )
        raise UnableToDetermineOntologyException(message)

    @property
    def _ontology_names(self):
        ontology_names = set(proposition.ontology_name for proposition in self.content)
        return ontology_names

    def has_semantic_content(self):
        return True

    def __iter__(self):
        flattened_items = self._flatten(self.content)
        return flattened_items.__iter__()

    def _flatten(self, items):
        result = []
        for item in items:
            if item.getType() == PlanItem.TYPE_IF_THEN_ELSE:
                if item.consequent:
                    result.append(item.get_consequent())
                if item.alternative:
                    result.append(item.get_alternative())
            else:
                result.append(item)
        return result

    def remove(self, item_to_remove):
        for item in self.content:
            if item == item_to_remove:
                self.content.remove(item)
            elif item.getType() == PlanItem.TYPE_IF_THEN_ELSE:
                self.remove_nested(item_to_remove, item)

    def remove_nested(self, to_remove, plan_item):
        if to_remove == plan_item.consequent:
            plan_item.consequent = None
        if to_remove == plan_item.alternative:
            plan_item.alternative = None

    def get_questions_in_plan_without_feature_question(self):
        for plan_item in self:
            if plan_item.is_question_plan_item():
                question = plan_item.getContent()
                yield question

    def __str__(self):
        return "Plan(%s)" % self.content

    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, (self.content or self.contentclass, ))


class InvalidPlansException(Exception):
    pass
