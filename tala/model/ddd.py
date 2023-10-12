from tala.utils.as_json import AsJSONMixin
from tala.utils.equality import EqualityMixin


class DDD(AsJSONMixin, EqualityMixin):
    def __init__(self, name, ontology, domain, service_interface):
        super(DDD, self).__init__()
        self._name = name
        self._ontology = ontology
        self._domain = domain
        self._service_interface = service_interface

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
    def service_interface(self):
        return self._service_interface

    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, (self.name, self.ontology, self.domain, self.service_interface))

    def as_dict(self):
        return {
            "ddd_name": self._name,
            "ontology": self.ontology,
            "domain": self.domain,
            "service_interface": self.service_interface,
        }
