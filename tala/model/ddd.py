from tala.utils.as_json import convert_to_json, JSONLoggable


class DDD(JSONLoggable):
    def __init__(self, name, ontology, domain, rasa_nlu, service_interface, grammars, language_codes, use_rgl):
        super(DDD, self).__init__()
        self._name = name
        self._ontology = ontology
        self._domain = domain
        self._rasa_nlu = rasa_nlu
        self._service_interface = service_interface
        self._grammars = grammars
        self._language_codes = language_codes
        self._use_rgl = use_rgl

    @property
    def name(self):
        return self._name

    @property
    def ontology(self):
        return self._ontology

    @property
    def domain(self):
        return self._domain

    @property
    def rasa_nlu(self):
        return self._rasa_nlu

    @property
    def service_interface(self):
        return self._service_interface

    @property
    def grammars(self):
        return self._grammars

    @property
    def language_codes(self):
        return self._language_codes

    @property
    def use_rgl(self):
        return self._use_rgl

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__, (
                self.name, self.ontology, self.domain, self.rasa_nlu, self.service_interface, self.grammars,
                self.language_codes, self.use_rgl
            )
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (other == self)

    def as_json(self):
        return {
            "ontology": convert_to_json(self.ontology),
            "domain": convert_to_json(self.domain),
            "rasa_nlu": convert_to_json(self.rasa_nlu),
            "service_interface": convert_to_json(self.service_interface),
            "grammars": [convert_to_json(grammar) for grammar in self.grammars],
            "language_codes": self.language_codes,
            "use_rgl": self.use_rgl,
        }
