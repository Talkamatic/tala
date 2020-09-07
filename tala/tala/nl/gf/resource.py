class NP:
    def __init__(self, indefinite, definite=None, gender=None, number=None):
        self.indefinite = indefinite
        self.definite = definite
        self.gender = gender
        self.number = number


class VP:
    def __init__(self, infinitive, imperative, ing_form, object_):
        self.infinitive = infinitive
        self.imperative = imperative
        self.ing_form = ing_form
        self.object = object_


class FEMININE:
    pass


class MASCULINE:
    pass


class PLURAL:
    pass


class SINGULAR:
    pass
