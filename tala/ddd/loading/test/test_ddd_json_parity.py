from tala.config import DddConfig
from tala.ddd.loading.ddd_loader import DDDLoader
from tala.utils.chdir import chdir


def test_mockup_travel_json_matches_xml():
    with chdir("ddds"):
        xml_loader = DDDLoader("mockup_travel", DddConfig.default_config())
        xml_ddd = xml_loader.load()

        json_config = DddConfig.default_config(ddd_files={
            "ontology": "ontology.json",
            "domain": "domain.json",
            "service_interface": "service_interface.json",
        })
        json_loader = DDDLoader("mockup_travel", json_config)
        json_ddd = json_loader.load()

    assert xml_ddd.as_json() == json_ddd.as_json()
