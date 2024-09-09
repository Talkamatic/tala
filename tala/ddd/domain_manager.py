from tala.model.goal import ResolveGoal
from tala.model import speaker


class UnknownGoalException(Exception):
    pass


class DomainAlreadyAddedException(Exception):
    pass


class DomainManager(object):
    def __init__(self, ddd_manager):
        self._domains_of_goals = {}
        self._domains = set()
        self._ddd_manager = ddd_manager

    @property
    def domains(self):
        return self._domains

    def add(self, domain):
        for goal in domain.goals:
            self._domains_of_goals[goal] = domain
        self._domains.add(domain)

    def has_goal(self, goal):
        return goal in self._domains_of_goals

    def get_domain_of_goal(self, goal):
        self._load_domain_if_needed(goal)
        if goal not in self._domains_of_goals:
            if goal.is_resolve_goal():
                question = goal.get_content()
                if question.is_consequent_question():
                    return self.get_domain_of_goal(
                        ResolveGoal(question.get_embedded_consequent_question(), speaker.SYS)
                    )
            raise UnknownGoalException(
                "Goal %s not found among known goals %s" % (repr(goal), list(self._domains_of_goals.keys()))
            )
        return self._domains_of_goals[goal]

    def _load_domain_if_needed(self, goal):
        if goal.is_ontology_specific and goal not in self._domains_of_goals:
            self._ddd_manager.load_ddd_for_ontology_name(goal.ontology_name)

    def remove(self, domain):
        for goal in domain.goals:
            if goal not in self._domains_of_goals:
                raise UnknownGoalException(
                    f"Goal '{goal}' of domain '{domain}' not found among known "
                    f"goals '{list(self._domains_of_goals.keys())}'"
                )
            self._domains_of_goals[goal] = None
            del self._domains_of_goals[goal]
        self._domains.remove(domain)

    def get_downdate_conditions(self, goal):
        if self.has_goal(goal):
            domain = self.get_domain_of_goal(goal)
            return domain.get_downdate_conditions(goal)
        else:
            return []

    def goal_allows_accommodation_without_feedback(self, goal):
        domain = self.get_domain_of_goal(goal)
        return domain.get_goal_attribute(goal, "accommodate_without_feedback")

    def get_all_goals_in_defined_order(self):
        goals = []
        for domain in self._domains:
            domain_goals = domain.get_all_goals_in_defined_order()
            goals.extend(domain_goals)
        return goals

    def goal_is_preferred(self, goal):
        domain = self.get_domain_of_goal(goal)
        return domain.goal_is_preferred(goal)
