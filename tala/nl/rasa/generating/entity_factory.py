from tala.nl.rasa.generating.entity import PropositionalEntity, SortalEntity


class EntityFactory(object):
    def create(self, identifier, text, start, end):
        raise NotImplementedError("%s.create(...) need to be implemented" % self.__class__.__name__)


class PropositionalEntityFactory(EntityFactory):
    def create(self, identifier, text, start, end):
        return PropositionalEntity(identifier, text, start, end)


class SortalEntityFactory(EntityFactory):
    def create(self, identifier, text, start, end):
        return SortalEntity(identifier, text, start, end)
