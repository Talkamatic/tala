from tala.utils.as_json import AsJSONMixin
from tala.utils.equality import EqualityMixin
from tala.utils.json_api import JSONAPIMixin, IncludedObject
from tala import model
from tala.ddd.services.service_interface import ServiceInterface


class DDD(AsJSONMixin, EqualityMixin, JSONAPIMixin):
    @classmethod
    def create_from_json_api_data(cls, ddd_as_dict):
        ddd_entry = ddd_as_dict["data"]
        included = IncludedObject(ddd_as_dict["included"])
        name = ddd_entry["attributes"]["name"]
        path = ddd_entry["attributes"]["path"]

        ontology_object = included.get_object_from_relationship(ddd_entry["relationships"]["ontology"]["data"])
        domain_object = included.get_object_from_relationship(ddd_entry["relationships"]["domain"]["data"])
        service_interface_object = included.get_object_from_relationship(
            ddd_entry["relationships"]["service_interface"]["data"]
        )
        ontology = model.ontology.Ontology.create_from_json_api_data(ontology_object, included)
        domain = model.domain.Domain.create_from_json_api_data(domain_object, included, ontology)
        service_interface = ServiceInterface.create_from_json_api_data(service_interface_object, included)

        return cls(name, ontology, domain, service_interface, path)

    def __init__(self, name, ontology, domain, service_interface, path=None):
        super(DDD, self).__init__()
        self._name = name
        self._ontology = ontology
        self._domain = domain
        self._service_interface = service_interface
        self._path = path

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

    @property
    def path(self):
        return self._path

    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, (self.name, self.ontology, self.domain, self.service_interface))

    def as_dict(self):
        return {
            "ddd_name": self._name,
            "ontology": self.ontology,
            "domain": self.domain,
            "service_interface": self.service_interface,
        }

    @property
    def json_api_id(self):
        return f"{self.name}"

    @property
    def json_api_attributes(self):
        return ["name", "path"]

    @property
    def json_api_relationships(self):
        return ["ontology", "domain", "service_interface"]
