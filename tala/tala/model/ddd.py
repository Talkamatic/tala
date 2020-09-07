from tala.utils.as_json import AsJSONMixin
from tala.utils.equality import EqualityMixin


class DDD(AsJSONMixin, EqualityMixin):
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
        return "%s%s" % (
            self.__class__.__name__, (
                self.name, self.ontology, self.domain, self.rasa_nlu, self.service_interface, self.grammars,
                self.language_codes, self.use_rgl
            )
        )

    def as_dict(self):
        return {
            "ontology": self.ontology,
            "domain": self.domain,
            "rasa_nlu": self.rasa_nlu,
            "service_interface": self.service_interface,
            "grammars": self.grammars,
            "language_codes": self.language_codes,
            "use_rgl": self.use_rgl,
        }
