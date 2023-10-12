import pytest

from tala.ddd.maker.ddd_maker import UnexpectedCharactersException

from .console_script_mixin import ConsoleScriptTestMixin


class TestCreateDDD(ConsoleScriptTestMixin):
    def test_create(self):
        self._when_creating_a_ddd(name="legal_name")
        self._then_result_is_successful()

    def _when_creating_a_ddd(self, name=None):
        self._create_ddd(name)

    def test_create_with_illegal_characters(self):
        self._when_creating_a_ddd_then_an_exception_is_raised(
            name="illegal-name",
            expected_exception=UnexpectedCharactersException,
            expected_pattern="Expected only alphanumeric ASCII and underscore characters in DDD name 'illegal-name', "
            "but found others"
        )

    def _when_creating_a_ddd_then_an_exception_is_raised(self, name, expected_exception, expected_pattern):
        with pytest.raises(expected_exception, match=expected_pattern):
            self._when_creating_a_ddd(name)
