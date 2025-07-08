import warnings

from tala.model import move
from tala.model.question import Question
from tala.model.action import Action
from tala.model import speaker
from tala.model.semantic_object import SemanticObject, SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify

PERFORM = "PERFORM_GOAL"
RESOLVE = "RESOLVE_GOAL"


class Goal(SemanticObject, AsSemanticExpressionMixin):
    @classmethod
    def create_from_json_api_data(cls, data, included):
        content = included.get_object_from_relationship(data["relationships"]["content"]["data"])
        type_ = data["attributes"]["type_"]
        target = data["attributes"]["target"]

        if type_.endswith(RESOLVE):
            question = Question.create_from_json_api_data(content, included)
            return Resolve(question, target)
        if type_.endswith(PERFORM):
            action = Action.create_from_json_api_data(content, included)
            return Perform(action, target)
        raise Exception(f"Unsupported goal: '{type_}'")

    def __init__(self, goal_type, target):
        self._goal_type = goal_type
        self._target = target
        self._background = None

    def is_goal(self):
        return True

    def is_perform_goal(self):
        return False

    def is_resolve_goal(self):
        return False

    def is_top_goal(self):
        return False

    @property
    def type_(self):
        return self._goal_type

    @property
    def target(self):
        return self._target

    def __eq__(self, other):
        try:
            return other.target == self.target and other.type_ == self.type_
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self._goal_type, self._target))

    def __repr__(self):
        return "%s(%s, %s)" % (Goal.__name__, self._goal_type, self._target)

    def __str__(self):
        return repr(self)

    def set_background(self, background):
        self._background = background

    @staticmethod
    def goal_filter(goal_type):
        warnings.warn("Goal.goal_filter() is deprecated.", DeprecationWarning, stacklevel=2)
        return lambda goal: goal.type_ == goal_type

    @staticmethod
    def goal_target_filter(target_speaker):
        return lambda goal: goal.target == target_speaker


class GoalWithSemanticContent(Goal, SemanticObjectWithContent):
    def __init__(self, goal_type, target, content):
        Goal.__init__(self, goal_type, target)
        SemanticObjectWithContent.__init__(self, content)
        self._content = content

    @property
    def content(self):
        return self._content

    def is_goal_with_semantic_content(self):
        return True

    def __hash__(self):
        try:
            return hash((self._goal_type, self._target, self._content, self.ontology_name))
        except NotImplementedError:
            return hash((self._goal_type, self._target, self._content))

    def __repr__(self):
        try:
            return "%s(%s, %s, %s, %s)" % (
                GoalWithSemanticContent.__name__, self.ontology_name, self._goal_type, self._target, self._content
            )
        except NotImplementedError:
            return "%s(%s, %s, %s)" % (GoalWithSemanticContent.__name__, self._goal_type, self._target, self._content)

    def __eq__(self, other):
        def ontologies_match():
            if self.is_ontology_specific():
                return other.is_ontology_specific() and other.ontology_name == self.ontology_name
            return not other.is_ontology_specific()

        try:
            return other.is_goal() \
                and other.has_semantic_content() \
                and other.content == self.content \
                and other.target == self.target \
                and other.type_ == self.type_ \
                and ontologies_match()
        except AttributeError:
            pass
        except NotImplementedError:
            pass
        return False

    def as_move(self):
        raise NotImplementedError()

    @property
    def json_api_id(self):
        return f"{self.type_}.{self.target}:{self.content}"

    @property
    def json_api_attributes(self):
        return ["type_", "target"]

    @property
    def json_api_relationships(self):
        return ["content"]


class Perform(GoalWithSemanticContent):
    def __init__(self, action, target=speaker.SYS):
        assert action.is_action()
        GoalWithSemanticContent.__init__(self, PERFORM, target, action)

    def is_perform_goal(self):
        return True

    @staticmethod
    def filter():
        warnings.warn("Perform.filter() is deprecated.", DeprecationWarning, stacklevel=2)
        return Goal.goal_filter(PERFORM)

    @property
    def action(self):
        return self.content

    def __str__(self):
        return f"perform({self.action})"

    def as_move(self):
        return move.Request(self.content)

    def is_top_goal(self):
        return self.action.is_top_action()


class PerformGoal(Perform):
    pass


class Resolve(GoalWithSemanticContent):
    def __init__(self, question, target):
        assert question.is_question()
        GoalWithSemanticContent.__init__(self, RESOLVE, target, question)

    def is_resolve_goal(self):
        return True

    @property
    def question(self):
        return self.content

    @property
    def issue(self):
        return self.content

    @staticmethod
    def filter():
        warnings.warn("Resolve.filter() is deprecated.", DeprecationWarning, stacklevel=2)
        return Goal.goal_filter(RESOLVE)

    def __str__(self):
        result = ""
        if self._target == speaker.USR:
            result += "resolve_user"
        else:
            result += "resolve"
        result += "(%s" % self.question
        if self._background:
            result += ", %s" % unicodify(self._background)
        result += ")"
        return result

    def as_move(self):
        return move.Ask(self.content)


class ResolveGoal(Resolve):
    pass
