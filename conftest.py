import pytest

from tala.ddd.ddd_manager import DDDManager
from tala.ddd.loading.extended_ddd_set_loader import ExtendedDDDSetLoader
from tala.testing import utils as test_utils


@pytest.fixture(scope="class")
def ddd_manager(request):
    request.cls.ddd_manager = DDDManager()


@pytest.fixture(scope="class")
def loaded_mockup_travel(request):
    extended_ddd_set_loader = ExtendedDDDSetLoader(request.cls.ddd_manager)
    test_utils.load_mockup_travel(extended_ddd_set_loader)
