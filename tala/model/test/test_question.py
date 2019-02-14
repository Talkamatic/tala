import copy

from tala.model.error import OntologyError
from tala.model.goal import PerformGoal
from tala.model.lambda_abstraction import LambdaAbstractedPredicateProposition
from tala.model.proposition import PropositionSet, GoalProposition
from tala.model.question import AltQuestion, WhQuestion
from tala.testing.lib_test_case import LibTestCase


class WhQuestionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.lambda_abstracted_dest_city = LambdaAbstractedPredicateProposition(
            self.predicate_dest_city, self.ontology.get_name()
        )
        self.dest_city_wh_question = WhQuestion(self.lambda_abstracted_dest_city)

    def test_is_question(self):
        self.assertTrue(self.dest_city_wh_question.is_question())

    def test_string_format_predicate(self):
        self.assertEquals("?X.dest_city(X)", unicode(self.dest_city_wh_question))

    def test_string_format_goal(self):
        goal_question = WhQuestion(self.lambda_abstracted_goal_prop)
        self.assertEquals("?X.goal(X)", unicode(goal_question))

    def test_wh_question_get_content(self):
        self.assertEquals(self.lambda_abstracted_dest_city, self.dest_city_wh_question.get_content())

    def testWhQuestionEquality(self):
        question = self.dest_city_question
        identical_question = copy.copy(self.dest_city_question)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(question, identical_question)

    def testWhQuestionNonEquality(self):
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.dest_city_question, self.price_question)

    def test_is_wh_question(self):
        self.assertTrue(self.dest_city_wh_question.is_wh_question())


class QuestionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()

    def test_is_question(self):
        question = self.price_question
        non_question = self.proposition_dest_city_paris
        self.assertTrue(question.is_question())
        self.assertFalse(non_question.is_question())

    def test_questions_are_hashable(self):
        set([self.price_question])


class YesNoQuestionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.question = self.ontology.create_yes_no_question("dest_city", "paris")

    def test_is_question(self):
        self.assertTrue(self.question.is_question())

    def testYesNoQuestionunicode(self):
        question = self.ontology.create_yes_no_question("dest_city", "paris")
        self.assertEquals("?dest_city(paris)", unicode(question))

    def testInvalidYesNoQuestion(self):
        with self.assertRaises(OntologyError):
            self.ontology.create_yes_no_question("kalle", "paris")


class AltQuestionTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        propositions = [self.proposition_dest_city_paris, self.proposition_dest_city_london]
        self.question = AltQuestion(PropositionSet(propositions))

    def test_is_question(self):
        self.assertTrue(self.question.is_question())

    def test_is_alt_question(self):
        self.assertTrue(self.question.is_alt_question())

    def test_alt_question_equality(self):
        identical_question = copy.copy(self.question)
        self.assert_eq_returns_true_and_ne_returns_false_symmetrically(self.question, identical_question)

    def test_alt_question_inequality(self):
        other_propositions = PropositionSet([self.proposition_dest_city_paris])
        non_identical_question = AltQuestion(other_propositions)
        self.assert_eq_returns_false_and_ne_returns_true_symmetrically(self.question, non_identical_question)

    def test_string_format_for_goal_alt_question(self):
        alt_question = AltQuestion(
            PropositionSet([
                GoalProposition(PerformGoal(self.top_action)),
                GoalProposition(PerformGoal(self.buy_action))
            ])
        )
        self.assertEquals("?set([goal(perform(top)), goal(perform(buy))])", unicode(alt_question))

    def test_string_format_for_predicate_alt_question(self):
        self.assertEquals("?X.dest_city(X), set([dest_city(paris), dest_city(london)])", unicode(self.question))
