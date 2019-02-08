from tala.utils.as_json import convert_to_json


class DDD(object):
    def __init__(self, name, ontology, domain, is_rasa_enabled, service_interface, grammars, language_codes, use_rgl):
        self._name = name
        self._ontology = ontology
        self._domain = domain
        self._is_rasa_enabled = is_rasa_enabled
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
    def is_rasa_enabled(self):
        return self._is_rasa_enabled

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
                self.name, self.ontology, self.domain, self.is_rasa_enabled, self.service_interface, self.grammars,
                self.language_codes, self.use_rgl
            )
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (other == self)

    @property
    def can_convert_to_json(self):
        return True

    def as_json(self):
        return {
            "ontology": convert_to_json(self.ontology),
            "domain": convert_to_json(self.domain),
            "is_rasa_enabled": convert_to_json(self.is_rasa_enabled),
            "service_interface": convert_to_json(self.service_interface),
            "grammars": [convert_to_json(grammar) for grammar in self.grammars],
            "language_codes": self.language_codes,
            "use_rgl": self.use_rgl,
        }
