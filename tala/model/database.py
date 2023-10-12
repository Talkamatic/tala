from tala.model.proposition import PredicateProposition


class Database:
    def __init__(self, resourceclass, ontology):
        self.resource = resourceclass()
        self.ontology = ontology

    def consultDB(self, question, commitments):
        value = self.resource.consultDB(question, commitments)
        predicate = question.get_predicate()
        individual = self.ontology.create_individual(value)
        proposition = PredicateProposition(predicate, individual)
        return proposition
