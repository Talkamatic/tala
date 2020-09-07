# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Changed
- `tala generate rasa` no longer generates the config alongside the actual markdown training data in YAML. It now only generates the pure markdown training data, requiring a config to be added in other ways. 

### Removed
- Managing a GUI is no longer part of TDM's responsibilities and as a consequence several such constructs have been removed from DDD files. They include `<gui_context>` and `<label_question>` elements as well as `dynamic_title` attributes in `domain.xml`, and `<title>` elements in `grammar_x.xml`.

## [7.0.0] - 2020-08-27
### Added
- `tala endurancetest` has been added as a console command. It lets users run endurance tests towards DDDs deployed with the TDM pipeline.
- `tala generate rasa` now generates semantic roles for propositional entites of custom sorts.
- `tala test` now supports interaction tests with system output on a semantic level. Example: `S> ["icm:acc*pos", "ask(?X.a_question(X))"]`.
- `tala test` now supports interaction tests with rich moves in semantic user input. In addition to the existing plain semantic expressions (`U> ["request(call)", "answer(contact_john)"]`), it now also supports JSON objects that include perception and understanding confidence. Example: `U> [{"semantic_expression": "request(call)", "understanding_confidence": 0.55, "perception_confidence": 0.79}]`.
- `tala test` now supports interaction tests with interpretations as semantic user input: `U> {"moves": ["request(call)", "answer(contact_john)"], "utterance": "an utterance", "modality": "speech"}`, where the `"moves"` field can contain either plain semantic expression or the new JSON objects.
- `tala.utils.tdm_client.TDMClient` has a new method `wait_to_start(timeout=3)`, which attempts to connect to TDM's `/health` endpoint up to `timeout` seconds. If it succeeds to connect, the method returns; otherwise it raises an exception.

### Changed
- Semantic interactions, from both the user and system, in interaction tests used with `tala test` now need to comply with JSON. Most notably, this means that `"` need to be used for strings, whereas previously both `"` and `'` were accepted.
- `tala test` now checks TDM connectivity before tests start. If a connection can not be established, it retries for up to 3 seconds before aborting.

### Fixed
- A code injection loophole in interaction tests has been plugged.
- `tala.utils.tdm_client.TDMClient` now raises a `requests.HTTPError` exception when the TDM pipeline responds with an unexpected HTTP status code.
- `tala test` now properly prints its `Running tests from path/to/interaction_tests.txt` when the corresponding tests are about to start instead of in the beginning of the test session. The improvement can be noticed when running `tala test` on more than one test file at once.

## [6.0.0] - 2020-07-03
### Added
- `tala test` has been added as a console command. It lets users run interaction tests towards DDDs deployed with the TDM pipeline.
- Persian has been added as a new language. It is currently supported when `use_rgl` is set to `false` in the DDD config.
- The format for domain XML files now supports the "assume_issue" plan item, for assuming an issue for the system to resolve.
- A new plan item `<log message="message"/>` has been added to the domain langugage for allowing user defined log messages on `DEBUG` level, where `message` is a string.
- A new plan item `<assume_system_belief>` has been added to the domain langugage. It takes as a child element a proposition. When executed, the proposition is added to the system's private beliefs and is available as a parameter for service queries and actions as well as for answers to user queries. It is also available for conditions inside `<if>` elements.
- The definition of downdate conditions for perform and handle plans has been updated. `<goal>` elements now has a new child `<downdate_condition>`, which replaces the previous `<postcond>` element. The new element can take as a child either an `<is_shared_fact>` or a `<has_value>` element.

### Changed
- Python 3 is now supported. Python 2 support is dropped along with its end-of-life on Jan 1 2020.
- The argument `ddd` for the command `tala create-backend-config` is now required and passed positionally, instead of optionally.
- Most fields in config files are now optional instead of required. The only required fields are `ddds`, `active_ddd` and `supported_languages` for backend configs, as well as `use_rgl` for DDD configs.
- `tala generate rasa` now adds the DDD name to entity names when generating samples with custom sortal and propositional entities. This is needed to support a new TDM-Rasa integration upstream. Example: `my_ddd.sort.my_sort`.
- `tala generate rasa` now uses the individuals' semantic name when generating synonym names instead of the first grammar entry. This is helpful for the TDM-Rasa integration upstream so that Rasa can properly return the individuals' names. Additionally, synonyms now contain the first grammar entry, which was previously part of the synonym name. Example:
 ```md
 ## synonyms:ddd_name:contact_john
 - John
 - Johnny
 ```
 instead of:
 ```md
 ## synonyms:ddd_name:John
 - Johnny
 ```

### Fixed
- Running `tala generate` on a language that is not supported by the DDD now renders a helpful error message.
- `tala create-ddd` now prevents illegal DDD names, avoiding errors downstream. ASCII alphanumerics and underscores are allowed.
- Running `tala verify` on a DDD with newlines and spaces in `condition` and `forget` elements no longer generate error messages.

### Deprecated
- The `<postcond>` element has been deprecated, and `<downdate_condition>` should be used instead.

## [5.0.0] - 2019-11-28
### Added
- A new method `request_semantic_input` has been added to `tala.utils.tdm_client.TDMClient`.
- A new optional parameter `session_data` with default value `None` has been added to `start_session`, `request_text_input`, `request_speech_input`, `request_semantic_input` and `request_passivity` methods in `tala.utils.tdm_client.TDMClient` to accept arbitrary JSON-compatible data for “session”.

### Changed
- `tala.utils.tdm_client.TDMClient` now supports protocol '3.1' of the HTTP API for frontends.
- `tala generate rasa` now generates training data for builtin intents `yes`, `no`, `top` and `up`.

## [4.0.0] - 2019-10-08
### Added
- A new optional attribute `selection` is supported for `<one-of>` elements in `<report>` in grammars with RGL disabled, with supported values `disabled` (default) or `cyclic`.
- A new builtin sort `person_name` has been added. Use it together with a `PERSON` or `PER` NER in Rasa NLU.
- `tala interact` now accepts deployment URLs directly, for instance `tala interact https://my-deployment.ddd.tala.cloud:9090/interact`.
- `tala generate` has been added. It generates training data for NLUs.
- `tala generate` now supports the `alexa` format. It generates training data for Alexa Skills.

### Changed
- Command `tala generate-rasa` has been changed to `tala generate rasa`.

### Fixed
- `tala generate my-ddd ...` now properly selects the provided DDD `my-ddd` when more than one DDD is supported by the backend config.

## [3.0.0] - 2019-05-10
### Added
- A new method `request_speech_input` has been added to `tala.utils.tdm_client.TDMClient`.

### Changed
- `tala.utils.tdm_client.TDMClient` no longer manages a single session internally. The caller needs to manage sessions instead, injecting them into the `TDMClient`. This enables the client to be reused for several sessions.
- In `tala.utils.tdm_client.TDMClient`, the method `say` has been renamed to `request_text_input`.

## [2.0.0] - 2019-04-12
### Added
- Command `tala generate-rasa` has been added. Use it to generate training data for Rasa NLU.

### Changed
- `tala verify` now validates schema compliance for domain XML files.
- Boolean attribute values in domain XML files, e.g. values for the attribute `downdate_plan`, are now only supported in lowercase, i.e. `"true"` or `"false"`.
- The DDD config `ddd.config.json` has a new parameter `rasa_nlu`, replacing `enable_rasa_nlu`. Instead of the previous boolean value, it takes language specific runtime parameters, used when TDM calls Rasa's `/parse` endpoints. For instance:
```json
"rasa_nlu": {
    "eng": {
        "url": "https://eng.my-rasa.tala.cloud/parse",
        "config": {
            "project": "my-project-eng",
            "model": "my-model"
        }
    }
}
```
- The way warnings are issued for predicate compatibility with Rasa NLU has changed when running `tala verify`. Now, warnings are issued when used sorts have limitations with the builtin NLU. Currently, this applies to sorts `datetime` and `integer`. Previously, when Rasa NLU was part of TDM, warnings were more detailed and based on how Rasa was configured.
- `tala verify` now issues warnings when propositional slots are encountered in the grammar and Rasa NLU is enabled.
- `tala verify` no longer verifies the DDD from a Rasa NLU perspective. The new command `tala generate-rasa` now does this instead.

### Removed
- The attribute `type` for the domain XML element `<proposition>` has been removed.
- Command `tala create-rasa-config` has been removed along with the `--rasa-config` parameter of `tala verify` since the Rasa config `rasa.config.json` is no longer used.

## [1.1.0] - 2019-02-22
### Added
- Command `tala interact` has been added. Use it to chat with a deployed DDD. It uses the new deployments config.
- Command `tala create-deployments-config` has been added. Run it to create a deployments config with default values.

## [1.0.0] - 2019-02-12
### Added
- Command `tala version` has been added. It displays which version of Tala that's being used.
- Command `tala create-ddd` has been added. Run it to create boilerplate files for a new DDD.
- Command `tala create-ddd-config` has been added. Run it to create a DDD config with default values.
- Command `tala create-backend-config` has been added. Run it to create a backend config with default values.
- Command `tala create-rasa-config` has been added. Run it to create a Rasa config with default values.
- Command `tala verify` has been added. It verifies DDD files with XML schemas and additionally checks the sanity of the grammar.