import pytest

from tala.ddd.ddd_component_manager import DDDComponentManager
from tala.ddd.loading.component_set_loader import ComponentSetLoader
from tala.testing import utils as test_utils


@pytest.fixture(scope="class")
def ddd_component_manager(request):
    ddd_component_manager = DDDComponentManager()
    request.cls.ddd_component_manager = ddd_component_manager


@pytest.fixture(scope="class")
def loaded_mockup_travel(request):
    component_set_loader = ComponentSetLoader(request.cls.ddd_component_manager)
    test_utils.load_mockup_travel(component_set_loader)
