# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

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
