from tala.model.semantic_object import SemanticObject


class Done(SemanticObject):
    def __eq__(self, other):
        return isinstance(other, Done)

    def as_semantic_expression(self):
        return "done"
