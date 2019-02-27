# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added
- `tala verify` now validates schema compliance for domain XML files.
- Command `tala generate-rasa` has been added. Use it to generate training data for RASA NLU.

### Changed
- Boolean attribute values in domain XML files, e.g. values for the attribute `downdate_plan`, are now only supported in lowercase, i.e. `"true"` or `"false"`.
- `tala verify` now issues warnings when propositional slots are encountered in the grammar and RASA NLU is enabled.

### Removed
- The attribute `type` for the domain XML element `<proposition>` has been removed.

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
- Command `tala create-rasa-config` has been added. Run it to create a RASA config with default values.
- Command `tala verify` has been added. It verifies DDD files with XML schemas and additionally checks the sanity of the grammar.
