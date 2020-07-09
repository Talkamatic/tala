import json
import os
import re
import shutil
import subprocess
import tempfile

from pathlib import Path
import pytest

from tala.config import BackendConfig, DddConfig, DeploymentsConfig
from tala.cli import console_script
from tala.ddd.maker.ddd_maker import UnexpectedCharactersException
from tala.utils.chdir import chdir


class UnexpectedContentsException(Exception):
    pass


class TempDirTestCase(object):
    def setup(self):
        self._temp_dir = tempfile.mkdtemp(prefix="TalaIntegrationTest")
        self._working_dir = os.getcwd()
        os.chdir(self._temp_dir)

    def teardown(self):
        os.chdir(self._working_dir)
        shutil.rmtree(self._temp_dir)


class ConsoleScriptTestCase(TempDirTestCase):
    def setup(self):
        super(ConsoleScriptTestCase, self).setup()
        self._process = None

    def _given_created_ddd_in_a_target_dir(self, name=None):
        self._create_ddd(name)

    def _create_ddd(self, name=None):
        name = name or "test_ddd"
        self._run_tala_with(["create-ddd", "--target-dir", "test_root", name])

    def _given_changed_directory_to_target_dir(self):
        return chdir("test_root")

    def _given_changed_directory_to_ddd_folder(self):
        return chdir("test_root/test_ddd")

    def _then_result_is_successful(self):
        def assert_no_error_occured():
            pass

        assert_no_error_occured()

    def _when_running_command(self, command_line):
        self._stdout, self._stderr = self._run_command(command_line)

    def _run_tala_with(self, args):
        console_script.main(args)

    def _run_command(self, command_line):
        self._process = subprocess.Popen(
            command_line.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = self._process.communicate()
        return stdout, stderr

    def _then_stderr_contains_constructive_error_message_for_missing_backend_config(self, config_path):
        pattern = "Expected backend config '.*{config}' to exist but it was not found. To create it, " \
                  r"run 'tala create-backend-config --filename .*{config}'\.".format(config=config_path)
        assert re.search(pattern, self._stderr) is not None

    def _then_stderr_contains_constructive_error_message_for_missing_ddd_config(self, config_path):
        pattern = "Expected DDD config '.*{config}' to exist but it was not found. To create it, " \
                  r"run 'tala create-ddd-config --filename .*{config}'\.".format(config=config_path)
        assert re.search(pattern, self._stderr) is not None

    def _given_config_overrides_missing_parent(self, path):
        self._set_in_config_file(path, "overrides", "missing_parent.json")

    def _set_in_config_file(self, path, key, value):
        with path.open(mode="r") as f:
            config = json.load(f)
        config[key] = value
        with path.open(mode="w") as f:
            string = json.dumps(config)
            f.write(str(string))

    def _then_file_contains(self, filename, expected_string):
        actual_content = self._read_file(filename)
        assert expected_string in actual_content

    def _read_file(self, filename):
        with open(filename) as f:
            actual_content = f.read()
        return actual_content

    def _then_stderr_contains(self, string):
        assert string in self._stderr

    def _given_file_contains(self, filename, string):
        f = open(filename, "w")
        f.write(string)
        f.close()

    def _then_stdout_matches(self, expected_pattern):
        self._assert_matches(expected_pattern, self._stdout)

    def _then_stderr_matches(self, expected_pattern):
        self._assert_matches(expected_pattern, self._stderr)

    @staticmethod
    def _assert_matches(expected_pattern, string):
        assert re.search(expected_pattern, string) is not None, "Expected string to match '{}' but got '{}'".format(
            expected_pattern, string
        )

    def _given_ontology_contains(self, new_content):
        old_content = """
<ontology name="TestDddOntology">
</ontology>"""
        self._replace_in_file(Path("ontology.xml"), old_content, new_content)

    def _replace_in_file(self, path, old, new):
        with path.open() as f:
            old_contents = f.read()
        if old not in old_contents:
            raise UnexpectedContentsException(
                "Expected to find string to be replaced '{}' in '{}' but got '{}'".format(old, str(path), old_contents)
            )
        new_contents = old_contents.replace(old, new)
        with path.open("w") as f:
            f.write(new_contents)

    def _given_grammar_contains(self, new_content):
        old_content = """
<grammar>
</grammar>"""
        self._replace_in_file(Path("grammar") / "grammar_eng.xml", old_content, new_content)

    def _given_domain_contains(self, new_content):
        old_content = """
<domain name="TestDddDomain" is_super_domain="true">
  <goal type="perform" action="top">
    <plan>
      <forget_all/>
      <findout type="goal"/>
    </plan>
  </goal>
</domain>"""
        self._replace_in_file(Path("domain.xml"), old_content, new_content)

    def _given_rgl_is_disabled(self):
        config = Path("ddd.config.json")
        self._replace_in_file(config, '"use_rgl": true', '"use_rgl": false')


class TestCreateDDD(ConsoleScriptTestCase):
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


class TestVersionIntegration(ConsoleScriptTestCase):
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


class TestBackendConfigCreationIntegration(ConsoleScriptTestCase):
    def test_create_backend_config(self):
        self._when_running_command("tala create-backend-config test_ddd --filename test.config.json")
        self._then_backend_config_has_active_ddd("test.config.json", "test_ddd")

    def _then_backend_config_has_active_ddd(self, config_path, expected_active_ddd):
        config = BackendConfig(config_path).read()
        assert expected_active_ddd == config["active_ddd"]


class TestConfigFileIntegration(ConsoleScriptTestCase):
    EXPECTED_CONFIGS = {
        BackendConfig: {
            "active_ddd": "my_ddd",
            "ddds": ["my_ddd"],
            "supported_languages": ["eng"],
            "asr": "none",
            "use_recognition_profile": False,
            "repeat_questions": True,
            "use_word_list_correction": False,
            "rerank_amount": 0.2,
            "inactive_seconds_allowed": 7200,
            "response_timeout": 2.5,
        },
        DddConfig: {
            "use_rgl": True,
            "use_third_party_parser": False,
            "device_module": None,
            "word_list": "word_list.txt",
            "rasa_nlu": {}
        },
        DeploymentsConfig: {
            "dev": "https://127.0.0.1:9090/interact"
        }
    }

    @pytest.mark.parametrize(
        "ConfigClass,command", [(BackendConfig, "create-backend-config my_ddd"), (DddConfig, "create-ddd-config"),
                                (DeploymentsConfig, "create-deployments-config")]
    )
    def test_create_config_without_path(self, ConfigClass, command):
        self._when_running_command(f"tala {command}")
        self._then_config_contains(ConfigClass, ConfigClass.default_name(), self.EXPECTED_CONFIGS[ConfigClass])

    def _then_config_contains(self, ConfigClass, name, expected_config):
        actual_config = ConfigClass(name).read()
        assert expected_config == actual_config

    @pytest.mark.parametrize(
        "ConfigClass,command", [(BackendConfig, "create-backend-config my_ddd"), (DddConfig, "create-ddd-config"),
                                (DeploymentsConfig, "create-deployments-config")]
    )
    def test_create_config_with_path(self, ConfigClass, command):
        self._when_running_command(f"tala {command} --filename my_ddd.config.json")
        self._then_config_contains(ConfigClass, "my_ddd.config.json", self.EXPECTED_CONFIGS[ConfigClass])

    @pytest.mark.parametrize(
        "name,command", [
            ("backend", "create-backend-config mock_ddd"),
            ("DDD", "create-ddd-config"),
            ("deployments", "create-deployments-config"),
        ]
    )
    def test_exception_raised_if_config_file_already_exists(self, name, command):
        self._given_config_was_created_with("tala {} --filename test.config.json".format(command))
        self._when_running_command("tala {} --filename test.config.json".format(command))
        self._then_stderr_contains(
            "Expected to be able to create {} config file 'test.config.json' but it already exists.".format(name)
        )

    def _given_config_was_created_with(self, command):
        self._run_command(command)

    @pytest.mark.parametrize(
        "command", [
            "create-backend-config mock_ddd",
            "create-ddd-config",
            "create-deployments-config",
        ]
    )
    def test_config_file_not_overwritten(self, command):
        self._given_file_contains("test.config.json", "unmodified_mock_content")
        self._when_running_command("tala {} --filename test.config.json".format(command))
        self._then_file_contains("test.config.json", "unmodified_mock_content")

    @pytest.mark.parametrize("command", [
        "tala verify --config non_existing_config.json",
    ])
    def test_missing_config_causes_constructive_error_message(self, command):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command(command)
            self._then_stderr_contains_constructive_error_message_for_missing_backend_config("non_existing_config.json")

    @pytest.mark.parametrize("command", [
        "tala verify",
    ])
    def test_missing_parent_backend_config_causes_constructive_error_message(self, command):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._given_config_overrides_missing_parent(Path(BackendConfig.default_name()))
            self._when_running_command(command)
            self._then_stderr_contains_constructive_error_message_for_missing_backend_config("missing_parent.json")

    @pytest.mark.parametrize("command", [
        "tala verify",
    ])
    def test_missing_parent_ddd_config_causes_constructive_error_message(self, command):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_config_overrides_missing_parent(Path(DddConfig.default_name()))
        with self._given_changed_directory_to_target_dir():
            self._when_running_command(command)
            self._then_stderr_contains_constructive_error_message_for_missing_ddd_config("missing_parent.json")


class TestVerifyIntegration(ConsoleScriptTestCase):
    def setup(self):
        super(TestVerifyIntegration, self).setup()

    def test_that_verifying_boilerplate_ddd_succeeds(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_verifying()
        self._then_result_is_successful()

    def _when_verifying(self):
        self._run_tala_with(["verify"])

    def test_stdout_when_verifying_boilerplate_ddd(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_stdout_matches(
            "^Verifying models for DDD 'test_ddd'.\n"
            r"\[eng\] Verifying grammar.\n"
            r"\[eng\] Finished verifying grammar.\n"
            "Finished verifying models for DDD 'test_ddd'.\n$"
        )

    def test_stdout_when_verifying_boilerplate_ddd_with_rasa_enabled(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_enabled_rasa()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_stdout_matches(
            "^Verifying models for DDD 'test_ddd'.\n"
            r"\[eng\] Verifying grammar.\n"
            r"\[eng\] Finished verifying grammar.\n"
            "Finished verifying models for DDD 'test_ddd'.\n$"
        )

    def _given_enabled_rasa(self):
        self._set_in_config_file(Path(DddConfig.default_name()), "rasa_nlu", {"eng": {"url": "mock-url", "config": {}}})

    def test_stderr_when_verifying_boilerplate_ddd(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_stderr_is_empty()

    def _then_stderr_is_empty(self):
        assert self._stderr == ""

    def test_verify_creates_no_build_folders(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_there_are_no_build_folders()

    def _then_there_are_no_build_folders(self):
        ddd_folder = Path("test_root") / "test_ddd" / "grammar"
        build_folders = [path for path in ddd_folder.iterdir() if path.is_dir() and path.name.startswith("build")]
        assert not any(build_folders), "Expected no build folders but got {}".format(build_folders)

    def test_verify_creates_no_build_folders_with_rasa_enabled(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_enabled_rasa()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_there_are_no_build_folders()

    def test_verify_returncode_with_schema_violation(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_schema_violation_in_ontology()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_returncode_signals_error()

    def _given_schema_violation_in_ontology(self):
        self._replace_in_file(Path("ontology.xml"), "ontology", "hello")

    def _then_returncode_signals_error(self):
        assert self._process.returncode != 0

    def test_verify_stderr_with_schema_violation(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_schema_violation_in_ontology()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala verify")
        self._then_stderr_contains(
            "Expected ontology.xml compliant with schema but it's in violation: "
            "Element 'hello': "
            "No matching global declaration available for the validation root., line 2"
        )


class TestInteractIntegration(ConsoleScriptTestCase):
    def test_interacting_with_unknown_environment(self):
        self._given_created_deployments_config()
        self._when_running_command("tala interact my-made-up-environment")
        self._then_stdout_matches(
            r"Expected a URL or one of the known environments \['dev'\] but got 'my-made-up-environment'"
        )

    def _given_created_deployments_config(self):
        self._run_tala_with(["create-deployments-config"])


class TestGenerateRASAIntegration(ConsoleScriptTestCase):
    def setup(self):
        super(TestGenerateRASAIntegration, self).setup()

    def test_that_generating_boilerplate_ddd_succeeds(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_generating()
        self._then_result_is_successful()

    def _when_generating(self):
        self._run_tala_with(["generate", "rasa", "test_ddd", "eng"])

    def test_stdout_when_generating_boilerplate_ddd(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_ontology_contains("""
<ontology name="TestDddOntology">
  <action name="call"/>
</ontology>""")
            self._given_grammar_contains(
                """
<grammar>
  <action name="call">
    <verb-phrase>
      <verb ref="call"/>
    </verb-phrase>
  </action>
  <lexicon>
    <verb id="call">
      <infinitive>call</infinitive>
    </verb>
  </lexicon>
  <request action="call"><utterance>make a call</utterance></request>
</grammar>"""
            )
        with self._given_changed_directory_to_target_dir():
            self._given_ddd_verifies_successfully()
            self._when_running_command("tala generate rasa test_ddd eng")
        self._then_stdout_matches(
            r'''language: "en"

pipeline: "spacy_sklearn"

data: \|
  ## intent:test_ddd:action::call
  - make a call
  
  ## intent:NEGATIVE
  - aboard
  - about
''')  # yapf: disable  # noqa: W293

    def _given_ddd_verifies_successfully(self):
        self._run_tala_with(["verify"])

    def test_generating_for_unknown_ddd(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala generate rasa unknown-ddd eng")
        self._then_stderr_matches("UnexpectedDDDException: Expected DDD 'unknown-ddd' to exist but it didn't")

    def test_generating_for_unknown_language(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala generate rasa test_ddd unknown-language")
        self._then_stderr_matches("tala generate: error: argument language: invalid choice: 'unknown-language'")

    def test_generating_for_unsupported_language(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala generate rasa test_ddd pes")
        self._then_stderr_matches(
            r"Expected one of the supported languages \['eng'\] in backend config "
            "'backend.config.json', but got 'pes'"
        )

    def test_stdout_when_generating_ddd_with_action_and_question_and_sortal_and_propositional_answers_without_rgl(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_rgl_is_disabled()
            self._given_ontology_contains(
                """
<ontology name="TestDddOntology">
  <sort name="contact"/>
  <sort name="phone_number" dynamic="true"/>
  <predicate name="phone_number_of_contact" sort="phone_number"/>
  <predicate name="selected_contact" sort="contact"/>
  <individual name="contact_john" sort="contact"/>
  <action name="buy"/>
  <predicate name="selected_amount" sort="integer"/>
</ontology>"""
            )
            self._given_domain_contains(
                """
<domain name="TestDddDomain">
  <goal type="perform" action="top">
    <plan>
      <forget_all/>
      <findout type="goal"/>
    </plan>
  </goal>
  <goal type="resolve" question_type="wh_question" predicate="phone_number_of_contact">
    <plan>
      <findout type="wh_question" predicate="selected_contact"/>
    </plan>
  </goal>
  <goal type="perform" action="buy">
    <plan>
      <findout type="wh_question" predicate="selected_amount"/>
      <invoke_service_action name="Buy" postconfirm="true"/>
    </plan>
  </goal>
</domain>"""
            )
            self._given_grammar_contains(
                """
<grammar>
  <question speaker="user" predicate="phone_number_of_contact">
    <one-of>
      <item>tell me a phone number</item>
      <item>what is <slot type="individual" sort="contact"/>'s number</item>
      <item>tell me <slot type="individual" predicate="selected_contact"/>'s number</item>
    </one-of>
  </question>
  <individual name="contact_john">John</individual>
  <action name="buy">
    <one-of>
      <item>
        <vp>
          <infinitive>buy</infinitive>
          <imperative>buy</imperative>
          <ing-form>buying</ing-form>
          <object>apples</object>
        </vp>
      </item>
      <item>buy apples</item>
      <item>buy <slot type="individual" sort="integer"/> apples</item>
      <item>buy <slot type="individual" predicate="selected_amount"/> apples</item>
    </one-of>
  </action>
</grammar>"""
            )
        with self._given_changed_directory_to_target_dir():
            self._given_ddd_verifies_successfully()
            self._when_running_command("tala generate rasa test_ddd eng")
        self._then_stdout_matches(
            r'''language: "en"

pipeline: "spacy_sklearn"

data: |
  ## intent:test_ddd:action::buy
  - buy apples
  - buy 0 apples
  - buy 99 apples
  - buy 1224 apples
  - buy a hundred and fifty seven apples
  - buy three apples
  - buy two thousand fifteen apples
  
  ## intent:test_ddd:question::phone_number_of_contact
  - tell me a phone number
  - what is [John](test_ddd.sort.contact)'s number
  - tell me [John]{"entity":"test_ddd.sort.contact" "role":"test_ddd.predicate.selected_contact"}'s number
  
  ## intent:test_ddd:answer
  - 0
  - 99
  - 1224
  - a hundred and fifty seven
  - three
  - two thousand fifteen
  - [John](test_ddd.sort.contact)
  
  ## intent:test_ddd:answer_negation
  - not 0
  - not 99
  - not 1224
  - not a hundred and fifty seven
  - not three
  - not two thousand fifteen
  - not [John](test_ddd.sort.contact)
  
  ## intent:NEGATIVE
  - aboard
  - about
''')  # yapf: disable  # noqa: W293


class TestGenerateAlexaIntegration(ConsoleScriptTestCase):
    def setup(self):
        super(TestGenerateAlexaIntegration, self).setup()

    def test_that_generating_boilerplate_ddd_succeeds(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_target_dir():
            self._when_generating()
        self._then_result_is_successful()

    def _when_generating(self):
        self._run_tala_with(["generate", "alexa", "test_ddd", "eng"])

    def test_stdout_when_generating_ddd_with_action_and_question_and_sortal_and_propositional_answers(self):
        self._given_created_ddd_in_a_target_dir()
        with self._given_changed_directory_to_ddd_folder():
            self._given_rgl_is_disabled()
            self._given_ontology_contains(
                """
<ontology name="TestDddOntology">
  <sort name="contact"/>
  <sort name="phone_number" dynamic="true"/>
  <predicate name="phone_number_of_contact" sort="phone_number"/>
  <predicate name="selected_contact" sort="contact"/>
  <individual name="contact_john" sort="contact"/>
  <action name="buy"/>
  <predicate name="selected_amount" sort="integer"/>
</ontology>"""
            )
            self._given_domain_contains(
                """
<domain name="TestDddDomain">
  <goal type="perform" action="top">
    <plan>
      <forget_all/>
      <findout type="goal"/>
    </plan>
  </goal>
  <goal type="resolve" question_type="wh_question" predicate="phone_number_of_contact">
    <plan>
      <findout type="wh_question" predicate="selected_contact"/>
    </plan>
  </goal>
  <goal type="perform" action="buy">
    <plan>
      <findout type="wh_question" predicate="selected_amount"/>
      <invoke_service_action name="Buy" postconfirm="true"/>
    </plan>
  </goal>
</domain>"""
            )
            self._given_grammar_contains(
                """
<grammar>
  <question speaker="user" predicate="phone_number_of_contact">
    <one-of>
      <item>tell me a phone number</item>
      <item>what is <slot type="individual" sort="contact"/>'s number</item>
      <item>tell me <slot type="individual" predicate="selected_contact"/>'s number</item>
    </one-of>
  </question>
  <individual name="contact_john">John</individual>
  <action name="buy">
    <one-of>
      <item>
        <vp>
          <infinitive>buy</infinitive>
          <imperative>buy</imperative>
          <ing-form>buying</ing-form>
          <object>apples</object>
        </vp>
      </item>
      <item>buy apples</item>
      <item>buy <slot type="individual" sort="integer"/> apples</item>
      <item>buy <slot type="individual" predicate="selected_amount"/> apples</item>
    </one-of>
  </action>
</grammar>"""
            )
        with self._given_changed_directory_to_target_dir():
            self._when_running_command("tala generate alexa test_ddd eng")
        self._then_stdout_has_json({
            "interactionModel": {
                "languageModel": {
                    "intents": [
                        {
                            "name": "test_ddd_action_buy",
                            "samples": [
                                "buy apples",
                                "buy {test_ddd_sort_integer} apples",
                                "buy {test_ddd_predicate_selected_amount} apples"
                            ],
                            "slots": [
                                {
                                    "name": "test_ddd_sort_integer",
                                    "type": "AMAZON.NUMBER"
                                },
                                {
                                    "name": "test_ddd_predicate_selected_amount",
                                    "type": "AMAZON.NUMBER"
                                }
                            ]
                        },
                        {
                            "name": "test_ddd_question_phone_number_of_contact",
                            "samples": [
                                "tell me a phone number",
                                "what is {test_ddd_sort_contact}'s number",
                                "tell me {test_ddd_predicate_selected_contact}'s number"
                            ],
                            "slots": [
                                {
                                    "name": "test_ddd_sort_contact",
                                    "type": "test_ddd_sort_contact"
                                },
                                {
                                    "name": "test_ddd_predicate_selected_contact",
                                    "type": "test_ddd_sort_contact"
                                }
                            ]
                        },
                        {
                            "name": "test_ddd_answer",
                            "samples": [
                                "{test_ddd_sort_integer}",
                                "{test_ddd_sort_contact}",
                            ],
                            "slots": [
                                {
                                    "name": "test_ddd_sort_integer",
                                    "type": "AMAZON.NUMBER"
                                },
                                {
                                    'name': 'test_ddd_sort_contact',
                                    'type': 'test_ddd_sort_contact'
                                }
                            ]
                        },
                        {
                            "name": "test_ddd_answer_negation",
                            "samples": [
                                "not {test_ddd_sort_integer}",
                                "not {test_ddd_sort_contact}",
                            ],
                            "slots": [
                                {
                                    "name": "test_ddd_sort_integer",
                                    "type": "AMAZON.NUMBER"
                                },
                                {
                                    'name': 'test_ddd_sort_contact',
                                    'type': 'test_ddd_sort_contact'
                                }
                            ]
                        },
                        {
                            "name": "AMAZON.YesIntent",
                            "samples": []
                        },
                        {
                            "name": "AMAZON.NoIntent",
                            "samples": []
                        },
                        {
                            "name": "AMAZON.CancelIntent",
                            "samples": []
                        },
                        {
                            "name": "AMAZON.StopIntent",
                            "samples": []
                        }
                    ],
                    "invocationName": "test_ddd",
                    "types": [
                        {
                            "name": "test_ddd_sort_contact",
                            "values": [
                                {
                                    "id": "contact_john",
                                    "name": {
                                        "synonyms": [],
                                        "value": "John",
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        })  # yapf: disable

    def _given_ontology_contains(self, new_content):
        old_content = """
<ontology name="TestDddOntology">
</ontology>"""
        self._replace_in_file(Path("ontology.xml"), old_content, new_content)

    def _given_grammar_contains(self, new_content):
        old_content = """
<grammar>
</grammar>"""
        self._replace_in_file(Path("grammar") / "grammar_eng.xml", old_content, new_content)

    def _then_stdout_has_json(self, expected_json):
        def unicodify(o):
            if isinstance(o, dict):
                return {str(key): unicodify(value) for key, value in list(o.items())}
            if isinstance(o, list):
                return [unicodify(element) for element in o]
            return str(o)

        actual_json = json.loads(self._stdout)
        assert actual_json == unicodify(expected_json)
