from tala.model.semantic_object import SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify


class Hint(SemanticObjectWithContent, AsSemanticExpressionMixin):
    def __init__(self, plan):
        SemanticObjectWithContent.__init__(self, plan)
        self._plan = plan

    def __eq__(self, other):
        try:
            equality = self.plan == other.plan
            return equality
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self._plan)

    @property
    def plan(self):
        return self._plan

    def __str__(self):
        return "Hint" + unicodify(self.plan)
