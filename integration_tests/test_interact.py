import pytest

from .console_script_mixin import ConsoleScriptTestMixin


@pytest.mark.skip("Issues with prompt toolkit not having a stdout on vt100")
class TestInteractIntegration(ConsoleScriptTestMixin):
    def test_interacting_with_unknown_environment(self):
        self._given_created_deployments_config()
        self._run_tala_with(["tala", "interact", "my-made-up-environment"])
        self._then_stdout_matches(
            r"Expected a URL or one of the known environments \['dev'\] but got 'my-made-up-environment'"
        )

    def _given_created_deployments_config(self):
        self._run_tala_with(["create-deployments-config"])
