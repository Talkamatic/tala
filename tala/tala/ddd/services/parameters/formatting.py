class ParameterBindingsFormatter:
    @staticmethod
    def to_values(bindings):
        return [binding.value for binding in bindings]

    @staticmethod
    def to_proposition_list(bindings):
        def get_propositions():
            for binding in bindings:
                for proposition in binding.propositions:
                    if proposition:
                        yield proposition

        return list(get_propositions())
