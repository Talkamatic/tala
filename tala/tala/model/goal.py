from tala.model.move import RequestMove, AskMove
from tala.model.speaker import Speaker
from tala.model.semantic_object import OntologySpecificSemanticObject, SemanticObject, SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify


class Goal(SemanticObject, AsSemanticExpressionMixin):
    PERFORM_GOAL = "PERFORM_GOAL"
    RESOLVE_GOAL = "RESOLVE_GOAL"
    HANDLE_GOAL = "HANDLE_GOAL"

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

    def is_handle_goal(self):
        return False

    def get_goal_type(self):
        return self._goal_type

    def get_target(self):
        return self._target

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        try:
            return (other.get_target() == self.get_target() and other.get_goal_type() == self.get_goal_type())
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
        return lambda goal: goal.get_goal_type() == goal_type

    @staticmethod
    def goal_target_filter(target_speaker):
        return lambda goal: goal.get_target() == target_speaker


class GoalWithSemanticContent(Goal, SemanticObjectWithContent):
    def __init__(self, goal_type, target, content):
        Goal.__init__(self, goal_type, target)
        SemanticObjectWithContent.__init__(self, content)
        self._content = content

    def get_content(self):
        return self._content

    def is_goal_with_semantic_content(self):
        return True

    def __hash__(self):
        return hash((self._goal_type, self._target, self._content))

    def __repr__(self):
        return "%s(%s, %s, %s, %s)" % (
            GoalWithSemanticContent.__name__, self.ontology_name, self._goal_type, self._target, self._content
        )

    def __eq__(self, other):
        try:
            return (
                other.is_goal() and other.has_semantic_content() and other.get_content() == self.get_content()
                and other.get_target() == self.get_target() and other.get_goal_type() == self.get_goal_type()
            )
        except AttributeError:
            return False

    def as_move(self):
        raise NotImplementedError()


class PerformGoal(GoalWithSemanticContent):
    def __init__(self, action, target=Speaker.SYS):
        assert action.is_action()
        GoalWithSemanticContent.__init__(self, self.PERFORM_GOAL, target, action)

    def is_perform_goal(self):
        return True

    @staticmethod
    def filter():
        return Goal.goal_filter(PerformGoal.PERFORM_GOAL)

    def get_action(self):
        return self.get_content()

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "perform(%s)" % self.get_action()

    def as_move(self):
        return RequestMove(self.get_content())


class ResolveGoal(GoalWithSemanticContent):
    def __init__(self, question, target):
        assert question.is_question()
        GoalWithSemanticContent.__init__(self, self.RESOLVE_GOAL, target, question)

    def is_resolve_goal(self):
        return True

    def get_question(self):
        return self.get_content()

    @staticmethod
    def filter():
        return Goal.goal_filter(ResolveGoal.RESOLVE_GOAL)

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        result = ""
        if self._target == Speaker.USR:
            result += "resolve_user"
        else:
            result += "resolve"
        result += "(%s" % self.get_question()
        if self._background:
            result += ", %s" % unicodify(self._background)
        result += ")"
        return result

    def as_move(self):
        return AskMove(self.get_content())


class HandleGoal(Goal, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, device_event):
        Goal.__init__(self, self.HANDLE_GOAL, Speaker.SYS)
        OntologySpecificSemanticObject.__init__(self, ontology_name)
        self._device_event = device_event

    def get_device_event(self):
        return self._device_event

    def __eq__(self, other):
        try:
            return (
                other.is_ontology_specific() and other.ontology_name == self.ontology_name and Goal.__eq__(self, other)
                and other.get_device_event() == self.get_device_event()
            )
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def is_handle_goal(self):
        return True

    def __str__(self):
        return "handle(%s)" % self.get_device_event()

    def __hash__(self):
        return 17 * hash(str(self)) + 7 * hash(self.__class__.__name__)
