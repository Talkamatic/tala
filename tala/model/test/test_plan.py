import unittest

from tala.model.plan import Plan, UnableToDetermineOntologyException
from tala.model.plan_item import IfThenElse
from tala.model.question_raising_plan_item import FindoutPlanItem, RaisePlanItem
from tala.model.semantic_object import OntologySpecificSemanticObject
from tala.testing.lib_test_case import LibTestCase


class PlanTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.findout_price = FindoutPlanItem(self.domain_name, self.price_question)
        self.findout_dest_city = FindoutPlanItem(self.domain_name, self.dest_city_question)
        self.consequent = RaisePlanItem(self.domain_name, self.price_question)
        self.alternative = RaisePlanItem(self.domain_name, self.dest_city_question)
        self.if_then_else_item = IfThenElse("mockup_condition", self.consequent, self.alternative)

    def test_plan_iteration_steps_into_nested_blocks(self):
        self._given_plan_with_nested_item()
        expected_list = [self.findout_price, self.findout_dest_city, self.consequent, self.alternative]
        self.assertEquals(expected_list, list(self.plan))

    def _given_plan_with_nested_item(self):
        self.plan = Plan([self.if_then_else_item, self.findout_dest_city, self.findout_price])

    def test_plan_iteration_after_modification(self):
        plan = Plan()
        plan.push(self.findout_price)
        expected_list = [self.findout_price]
        self.assertEquals(expected_list, list(plan))

    def test_removal_of_findout_from_nested_block(self):
        self._given_plan_with_nested_item()
        self._when_consequent_is_removed()
        self._then_all_elements_but_consequent_are_left()

    def _when_consequent_is_removed(self):
        self.plan.remove(self.consequent)

    def _then_all_elements_but_consequent_are_left(self):
        expected_list = [self.findout_price, self.findout_dest_city, self.alternative]
        self.assertEquals(expected_list, list(self.plan))


class SemanticObjectPlanTests(unittest.TestCase):
    def setUp(self):
        self._semantic_objects = set()

    def test_ontology_name_with_ontology_specific_semantic_object(self):
        self._given_semantic_object_of_ontology("an ontology")
        self._given_plan()
        self._when_asking_for_ontology_name()
        self._then_ontology_name_is("an ontology")

    def _given_semantic_object_of_ontology(self, ontology):
        semantic_object = OntologySpecificSemanticObject(ontology)
        self._semantic_objects.add(semantic_object)

    def _given_plan(self):
        self._plan = Plan(self._semantic_objects)

    def _when_asking_for_ontology_name(self):
        self._result = self._plan.ontology_name

    def _then_ontology_name_is(self, expected_name):
        actual_name = self._result
        self.assertEqual(expected_name, actual_name)

    def test_ontology_name_with_multiple_ontology_specific_semantic_objects(self):
        self._given_semantic_object_of_ontology("an ontology")
        self._given_semantic_object_of_ontology("another ontology")
        self._given_plan()
        self._when_asking_for_ontology_name_then_exception_is_raised()

    def _when_asking_for_ontology_name_then_exception_is_raised(self):
        with self.assertRaises(UnableToDetermineOntologyException):
            self._result = self._plan.ontology_name

    def test_ontology_name_with_multiple_ontology_specific_semantic_objects_of_same_ontology(self):
        self._given_semantic_object_of_ontology("an ontology")
        self._given_semantic_object_of_ontology("an ontology")
        self._given_plan()
        self._when_asking_for_ontology_name()
        self._then_ontology_name_is("an ontology")
