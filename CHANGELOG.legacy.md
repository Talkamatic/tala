# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## [12.0.0] - 2022-08-25
### Added
- `tala generate rasa` has a new optional command line argument `--generate-synonyms`. This makes optional the generation of synonyms in the training data as in most cases they are already specified in the annotated entities as "value".
- `tala generate rasa` has a new optional command line argument `--add-ddd-name`. This makes optional the DDD name in intents and entities of the training data.

### Changed
- `tala generate rasa` now generates entities with the individual name annotated as "value". Example:
```yaml
    - [John]{"entity": "test_ddd.sort.contact", "value": "test_ddd.individual.contact_john"}
```

## [11.0.0] - 2022-01-18
### Changed
- `tala interact` and `tala test` now include "tala" as a `device_id` in the session object when it sends a request to a served TDM instance.
- `tala interact` and `tala test` now mirror back the session object to the request when getting a response.
- The conditions model has been re-worked. Conditions for downdate and for if statements now supports new condition types for making conditions about propositions being in commitments, in beliefs or in any of them, as well as conditions about a proposition over a certain predicate being in any of these sets. See documentation for details.
### Fixed
- A missing class specific equality check for if/then/else plan items, which makes it possible to properly compare such items, was added.
### Deprecated
- The `<condition>` element as a child of an `<if>` element has been deprecated. Use `<proposition>` instead.


## [10.2.0] - 2021-08-25
### Added
- `tala generate` has a new optional command line argument `--exclude-sort` or `-x` whose value is the name of a sort. This argument can be specified more than once. Each value specifies a sort from which training data should not be generated.

### Changed
- `tala generate rasa` now generates entities with roles only when there are two or more propositional slots of the same sort in an entry from the grammar.
- `tala generate` now does not generate intents for actions which only contain one entry from the grammar. Since such actions with one entry are always actions which do not need to be invoked by a user, they should be skipped.
- `tala generate rasa` now doesn't raise `SortNotSupportedException` when a DDD ontology contains predicates of sort `boolean`. Since the builtin answers `answer:yes`, `answer:no` are generated as training data, this sort has been supported by Rasa models.

### Fixed
- `tala generate rasa` can now process more than one of the `--lookup-entries` argument in a single command.
- `tala generate rasa` can now process more than one of the `--entity-examples` argument in a single command.

## [10.1.1] - 2021-07-16
### Fixed
- Fixes a bug where an unexpected error message is shown when passivity is prompted while running "tala interact".

## [10.1.0] - 2021-07-16
### Added
- tala now supports one plan for handling zero-result searches for each question. The plan is referenced with an attribute in the `parameters` element for the question. The attribute `on_zero_hits_action` refers to an action which must be defined in the current DDD.
- tala now supports one plan for handling too-many-results searches for each question. The plan is referenced with an attribute in the `parameters` element for the question. The attribute `on_too_many_hits_action` refers to an action which must be defined in the current DDD. The plan is only loaded if the number of hits after the last ask feature question exceeds the value of the `max_spoken_alts` parameter.
- It is now possible to define person names directly in the domain.xml code. For instance adding alternatives to a question: `<alt><proposition predicate="person_to_call" value="Anna Kronlid"/></alt>`.
- `tala generate rasa` has a new optional command line argument `--lookup-entries` whose values have the expected format SORT:PATH. Each value specifies the path to a single-column CSV file containing entity values for a lookup table for the specified (custom) sort. The lookup table data will be used for generating the training examples and will be listed as a lookup table in the rasa training data. The selection of training data is randomized (set the environment variable `TALA_GENERATE_SEED` for control over randomization).

### Changed
- It is now possible to set confidence thresholds in the backend config file. Example:
```json
"confidence_thresholds": {
    "CHECK": 0.1,
    "ACKNOWLEDGE": 0.5,
    "TRUST": 0.9
},
```
This optional setting overrides the standard values (0.1, 0.15 and 0.3 respectively). Moves with a confidence below CHECK are not considered by TDM. Moves above CHECK but below ACKNOWLEDGE are grounded with interrogative ICM. Moves above ACKNOWLEDGE but below TRUST are grounded using positive ICM. Moves above TRUST are trusted and considered to not need explicit grounding. There is also a setting `confidence_prediction_thresholds` which set the same thresholds, but for values collected from a service.
- The optional command line argument `--entity-examples` of `tala generate rasa` also supports custom sorts. When used with custom sorts the examples from the CSV file overrides the data from the grammar.
- `tala generate` now generates training data that includes answers (using the answer intent) on the form `yes [answer]` and `no [answer]` in order to let the NLU recognize answers like "yes Berlin" and "no the mobile number".
- All Python dependencies have been upgraded to allow components which use Tala to support Flask 2.0.1.

## [10.0.0] - 2021-02-18
### Added
- `tala create-ddd` and `tala create-backend-config` have a new optional command line argument `--language` whose expected value is one of the DDD supported languages.
- `tala generate rasa` has a new optional command line argument `--entity-examples` whose values have the expected format SORT:PATH. Each value specifies the path to a single-column CSV file containing entity values for the respective built-in sort, thereby overriding tala's default entity examples.
- `tala generate rasa` has a new optional command line argument `--num-instances` or `-n`, which needs to be followed by an integer value. When provided, it sets the maximum number of Rasa training instances to generate for each grammar entry.
- `tala generate rasa` now generates sortal and propositional entities for the built-in sort `person name`.
- `tala generate rasa` now generates training data for report moves for specific actions (e.g. `report(action_status(some_action, done))`). The implementation is limited to reports of success (`done`), and the data is generated from `<report>` elements in the grammar_*.xml file.
- `tala generate rasa` now generates appropriate examples for the `icm:acc*neg:issue` ("I don't know" etc.).
- `tala generate rasa` now generates appropriate examples for the `greet` and `thanks` moves.
- `<inform>` element is now added to domain.xml. `<inform insist="false"><proposition predicate="p" value="value"/></inform>` is equivalent to first forgetting any fact of predicate `p`, then assuming the system belief `p(value)` and then assuming that the question `?X.p(X)` is an issue. This means that the system will inform the user about `p(value)`, unless this is known to already be shared with the user. If the attribute `insist` is set to `true`, then -- in order to inform the user regardless of whether the user has been informed of this fact before -- previous propositions of `p` are forgotten.
- `tala generate rasa` now generates training data for request for builtin action `how` as intent `intent:reqest:how`.
- Instructions are often prefixed with sequencing information, such as "first", "then", "finally", "secondly", etc. When designing DDDs, this kind of sequencing is often incorporated in the request for action directed to the user. If the request is repeated, for instance if the user says "pardon", or for other reasons, repeating the sequencing information sounds odd to some people. TDM can now handle sequencing information in connection with user-targeted requests, making it possible to separate the sequencing information from the instruction. The sequential number of the instruction is stated in the `get_done` plan item, and the syntax is `<get_done action="some_action" step="N"/>`, where `N` is an integer. The intended convention is to use number 1 for the first instruction, and -1 for the last one. TDM outputs ICM for each instruction.
- `tala` now properly tolerates indefinitely nested `<if>` elements in the domain xml. Previously there was an unintended limit of two levels of nesting.
-  Previously, reporting and downdating of perform goals required usage of a service action, even in cases where service integration does not seem motivated. For example, to cause the system to report success of an action such as adjusting temperature, a service action for adjusting temperature was required, even if the action is designed to be simulated. This change introduces two new plan items for indicating action success or failure directly in the plan, thereby eliminating the need to use a service action in certain cases. Two plan elements has been added to domain.xml (`<signal_action_completion/>` and `<signal_action_failure reason="r"/>`) for reporting action success and failure respectively.
- All definitions of questions in the domain.xml now defaults to the type `wh_question`.
- The parameter list for a question now includes the entry `always_ground`, which -- if set to true -- ensures that the answer to the question will always be grounded on ACKNOWLEDGE level (`icm:und*pos:USR*PROPOSITION`, where `PROPOSITION` is the propositional answer to the question).

### Changed
- Python 3.9 is now supported.
- `tala create-ddd` now generates language-specific grammar templates which include entries for the actions `top` and `up`.
- `tala create-ddd` and `tala create-ddd-config` now set the parameter `use_rgl` to `false` in the DDD config `ddd.config.json`.
- `tala generate rasa` now generates synonyms from individuals with just one grammar entry.
- `tala generate rasa` now organizes consistently the synonyms in the training data based on the alphabetical order the sorts of the individuals for generating such synonyms.
- `tala generate rasa` now generates training data according to the format of Rasa 2.1.
- `tala generate` now sorts the actions in the generated training data in alphabetical order.
- `tala generate rasa` now generates a user warning instead of failing when run on a DDD where the grammar doesn't provide utterances for all actions defined in the DDD.

## [9.0.0] - 2020-10-22
### Added
- `tala generate rasa` now generates training data for builtin report `done` as intent `report:done` and builtin negative perception ICM as `icm:per*neg`.
- The `<if>` element in `domain.xml` has been extended. Its `<then>`and `<else>` children can now contain more than one plan item; and they can contain other `<if>` elements, allowing them to be nested. Additionally, the `<then>` and `<else>` elements are now optional and can be omitted if not used.
- `tala extract` has been added as a console command. It lets users extract interaction tests from TDM logs. The extracted tests can then be used together with `tala test`, for instance to reproduce past sessions.
- `tala test` now supports interaction tests with a full semantic input object, including dynamic entities. For instance: `U> {"interpretations": [{"moves": ["request(call)", "answer(contact_john)"], "utterance": "call John", "modality": "speech"}], "entitites": []}`.
- `tala test` now accepts natural language user input wrapped in quotation marks. For instance `U> 'hello'`, or empty input as `U> ""`. Empty input can occur for instance with `tala interact`, and if a test is extracted from such a session with the new `tala extract`, `tala test` can now handle it.

### Changed
- `tala generate rasa` now generates requests for builtin actions `top`, `up` and builtin answers `yes`, `no`, as `request:top`, `request:up` and `answer:yes`, `answer:no`. This is done to comply with changes to the TDM-Rasa integration.

### Fixed
- TDM now tolerates semantic input consisting of dynamic entities of a static sort, and issues a warning in the http respononse instead of crashing. These warnings are now printed on the console when running `tala test` `tala interact` etc.

## [8.0.0] - 2020-09-09
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
- `tala test` now supports interaction tests with a single interpretation as semantic user input: `U> {"moves": ["request(call)", "answer(contact_john)"], "utterance": "an utterance", "modality": "speech"}`, where the `"moves"` field can contain either plain semantic expression or the new JSON objects.
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
