import re
import subprocess

from .console_script_mixin import ConsoleScriptTestMixin


class TestVersionIntegration(ConsoleScriptTestMixin):
    def test_version(self):
        self._when_checking_tala_version()
        self._then_result_is_a_version_number()

    def _when_checking_tala_version(self):
        process = subprocess.Popen(["tala", "version"], stdout=subprocess.PIPE, text=True)
        stdout, _ = process.communicate()
        self._result = stdout

    def _then_result_is_a_version_number(self):
        base_version = r"[0-9]+\.[0-9]+(\.[0-9]+)*"
        dev_version_suffix = r"\.dev[0-9]+\+[a-z0-9]+"
        dirty_version_suffix = r"\.d[0-9]{8}"

        release_version_regexp = base_version
        dev_version_regexp = base_version + dev_version_suffix
        dirty_version_regexp = base_version + dev_version_suffix + dirty_version_suffix

        is_version_regexp = r"(?:%s|%s|%s)" % (release_version_regexp, dev_version_regexp, dirty_version_regexp)

        assert re.search(is_version_regexp, self._result) is not None
