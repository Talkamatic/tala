#!/usr/bin/env python2.7

import argparse
import contextlib
import os
import sys
import warnings
import unittest
import logging

from pathlib import Path
from requests.exceptions import MissingSchema

from tala.backend.dependencies.for_generating import BackendDependenciesForGenerating
from tala.cli.argument_parser import add_common_backend_arguments
from tala.cli import console_formatting
from tala.cli.tdm.tdm_cli import TDMCLI
from tala.config import BackendConfig, DddConfig, DeploymentsConfig, BackendConfigNotFoundException, \
    DddConfigNotFoundException, DeploymentsConfigNotFoundException
from tala.ddd.building.ddd_builder_for_generating import DDDBuilderForGenerating
from tala.ddd.maker import utils as ddd_maker_utils
from tala.ddd.maker.ddd_maker import DddMaker
from tala import installed_version
from tala.log.logger import configure_stdout_logging
from tala.nl import languages
from tala.nl.rasa.generator import RasaGenerator
from tala.nl.alexa.generator import AlexaGenerator
from tala.testing.interactions.file import InteractionTestingFile
from tala.testing.interactions.testloader import InteractionTestingLoader
from tala.testing.interactions.result import InteractionTestResult
from tala.utils.tdm_client import TDMClient
from tala.utils.chdir import chdir

RASA = "rasa"
ALEXA = "alexa"

GENERATE_PLATFORMS = [RASA, ALEXA]


class UnexpectedDDDException(Exception):
    pass


class UnexpectedPlatformException(Exception):
    pass


class UnexpectedLanguageException(Exception):
    pass


class ConfigAlreadyExistsException(Exception):
    pass


class ConfigNotFoundException(Exception):
    pass


class InvalidArgumentException(Exception):
    pass


def create_ddd(args):
    DddMaker(args.name, use_rgl=True, target_dir=args.target_dir).make()


def create_backend_config(args):
    if os.path.exists(args.filename):
        raise ConfigAlreadyExistsException(
            "Expected to be able to create backend config file '%s' but it already exists." % args.filename
        )
    BackendConfig().write_default_config(args.ddd, args.filename)


def create_ddd_config(args):
    if os.path.exists(args.filename):
        raise ConfigAlreadyExistsException(
            "Expected to be able to create DDD config file '%s' but it already exists." % args.filename
        )
    DddConfig().write_default_config(path=args.filename, use_rgl=True)


def create_deployments_config(args):
    if os.path.exists(args.filename):
        raise ConfigAlreadyExistsException(
            "Expected to be able to create deployments config file '%s' but it already exists." % args.filename
        )
    DeploymentsConfig().write_default_config(args.filename)


def verify(args):
    backend_dependencies = BackendDependenciesForGenerating(args)

    ddds_builder = DDDBuilderForGenerating(
        backend_dependencies,
        verbose=args.verbose,
        ignore_warnings=args.ignore_warnings,
        language_codes=args.language_codes
    )
    ddds_builder.verify()


def generate(args):
    def create_generator(ddd):
        if args.platform == RASA:
            return RasaGenerator(ddd, args.language)
        elif args.platform == ALEXA:
            return AlexaGenerator(ddd, args.language)
        else:
            raise UnexpectedPlatformException(
                "Expected one of the known platforms {} but got '{}'".format(GENERATE_PLATFORMS, args.platform)
            )

    def validate(backend_dependencies, language):
        if language not in backend_dependencies.supported_languages:
            raise UnexpectedLanguageException(
                f"Expected one of the supported languages "
                f"{backend_dependencies.supported_languages} in backend config "
                f"'{backend_dependencies.path}', but got '{language}'"
            )

    backend_dependencies = BackendDependenciesForGenerating(args)
    validate(backend_dependencies, args.language)
    ddd_path = Path(args.ddd)
    if not ddd_path.exists():
        raise UnexpectedDDDException("Expected DDD '{}' to exist but it didn't".format(args.ddd))
    with chdir(ddd_path / "grammar"):
        ddds = {ddd.name: ddd for ddd in backend_dependencies.ddds}
        ddd = ddds[args.ddd]
        generator = create_generator(ddd)
        generator.stream(sys.stdout)


def _check_ddds_for_word_lists(ddds):
    for ddd in ddds:
        ddd_maker_utils.potentially_create_word_list_boilerplate(ddd.name)


@contextlib.contextmanager
def _config_exception_handling():
    def generate_message(name, command_name, config):
        return "Expected {name} config '{config}' to exist but it was not found. To create it, " \
               "run 'tala {command} --filename {config}'.".format(name=name, command=command_name, config=config)

    try:
        yield
    except BackendConfigNotFoundException as exception:
        message = generate_message("backend", "create-backend-config", exception.config_path)
        raise ConfigNotFoundException(message)
    except DddConfigNotFoundException as exception:
        message = generate_message("DDD", "create-ddd-config", exception.config_path)
        raise ConfigNotFoundException(message)
    except DeploymentsConfigNotFoundException as exception:
        message = generate_message("deployments", "create-deployments-config", exception.config_path)
        raise ConfigNotFoundException(message)


def version(args):
    print(installed_version.version)


def interact(args):
    config = DeploymentsConfig(args.deployments_config)
    url = config.get_url(args.environment_or_url)
    tdm_cli = TDMCLI(url)

    try:
        tdm_cli.run()
    except (KeyboardInterrupt, EOFError):
        tdm_cli.stop()
    except MissingSchema:
        environments = list(config.read().keys())
        print("Expected a URL or one of the known environments {} but got '{}'".format(environments, url))


def test_interactions(args):
    def _check_health(url):
        tdm = TDMClient(url)
        print(f"Connecting to {url}...", end="")
        sys.stdout.flush()
        try:
            tdm.wait_to_start()
            print("done.")
        except BaseException:
            print("failed.")
            raise
        sys.stdout.flush()

    def _test_suites(selected_tests, test_paths, url):
        test_files = [InteractionTestingFile.from_path(test_path) for test_path in test_paths]
        return _test_suites_from_files(selected_tests, test_files, url)

    def _test_suites_from_files(selected_tests, test_files, url):
        suites = []
        for file in test_files:
            test_loader = InteractionTestingLoader(url)
            suite = test_loader.load_interaction_tests(file, selected_tests)
            suites.append(suite)
        return suites

    def _run_tests_from_suites(suites):
        results = []
        runner = unittest.TextTestRunner(resultclass=InteractionTestResult)
        successful = False
        for suite in suites:
            print(f"Running interaction tests from {suite.filename}")
            result = runner.run(suite)
            results.append(result)
            successful = all([result.wasSuccessful() for result in results])
        return successful

    configure_stdout_logging(args.log_level)
    config = DeploymentsConfig(args.deployments_config)
    url = config.get_url(args.environment_or_url)
    _check_health(url)
    suites = _test_suites(args.selected_tests, args.tests_filenames, url)
    unittest.installHandler()
    successful = _run_tests_from_suites(suites)
    if not successful:
        sys.exit(-1)


def add_verify_subparser(subparsers):
    parser = subparsers.add_parser(
        "verify", help="verify the format of all DDDs supported by the backend, across all supported languages"
    )
    parser.set_defaults(func=verify)
    add_common_backend_arguments(parser)
    parser.add_argument(
        "--languages",
        dest="language_codes",
        choices=languages.SUPPORTED_LANGUAGES,
        nargs="*",
        help="override the backend config and verify the DDDs for these languages"
    )
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_argument(
        "--ignore-grammar-warnings",
        dest="ignore_warnings",
        action="store_true",
        help="ignore warnings when compiling the grammar"
    )


def add_generate_subparser(subparsers):
    parser = subparsers.add_parser("generate", help="generate training data for Rasa NLU 0.14")
    parser.set_defaults(func=generate)
    add_common_backend_arguments(parser)
    parser.add_argument("platform", help="generate for this platform", choices=GENERATE_PLATFORMS)
    parser.add_argument("ddd", help="generate for this DDD")
    parser.add_argument("language", choices=languages.SUPPORTED_RASA_LANGUAGES, help="use the grammar of this language")


def add_create_ddd_subparser(subparsers):
    parser = subparsers.add_parser("create-ddd", help="create a new DDD")
    parser.set_defaults(func=create_ddd)
    parser.add_argument("name", help="Name of the DDD, e.g. my_ddd")
    parser.add_argument(
        "--target-dir", default=".", metavar="DIR", help="target directory, will be created if it doesn't exist"
    )


def add_create_backend_config_subparser(subparsers):
    parser = subparsers.add_parser("create-backend-config", help="create a backend config")
    parser.set_defaults(func=create_backend_config)
    parser.add_argument("ddd", help="name of the active DDD, e.g. my_ddd")
    parser.add_argument(
        "--filename",
        default=BackendConfig.default_name(),
        metavar="NAME",
        help="filename of the backend config, e.g. %s" % BackendConfig.default_name()
    )


def add_create_ddd_config_subparser(subparsers):
    parser = subparsers.add_parser("create-ddd-config", help="create a DDD config")
    parser.set_defaults(func=create_ddd_config)
    parser.add_argument(
        "--filename",
        default=DddConfig.default_name(),
        metavar="NAME",
        help="filename of the DDD config, e.g. %s" % DddConfig.default_name()
    )


def add_create_deployments_config_subparser(subparsers):
    parser = subparsers.add_parser("create-deployments-config", help="create a deployments config")
    parser.set_defaults(func=create_deployments_config)
    parser.add_argument(
        "--filename",
        default=DeploymentsConfig.default_name(),
        metavar="NAME",
        help="filename of the deployments config, e.g. %s" % DeploymentsConfig.default_name()
    )


def add_version_subparser(subparsers):
    parser = subparsers.add_parser("version", help="print the Tala version")
    parser.set_defaults(func=version)


def add_deployment_config_arguments(parser):
    parser.add_argument(
        "environment_or_url",
        help="this is either an environment, e.g. 'dev', pointing to a url in the deployments config; "
        "alternatively, if not an environment, this is considered a url in itself; "
        "the url should point to a TDM deployment, e.g. 'https://my-deployment.ddd.tala.cloud:9090/interact'"
    )
    parser.add_argument(
        "--config",
        dest="deployments_config",
        default=None,
        help="override the default deployments config %r" % DeploymentsConfig.default_name()
    )


def add_interact_subparser(subparsers):
    parser = subparsers.add_parser("interact", help="start an interactive chat with a deployed DDD")
    add_deployment_config_arguments(parser)
    parser.set_defaults(func=interact)


def add_test_subparser(subparsers):
    parser = subparsers.add_parser("test", help="run interaction tests")
    add_deployment_config_arguments(parser)
    parser.add_argument(dest="tests_filenames", nargs="+", metavar="TEST-FILE", help="specify DDD test files")
    parser.add_argument("-t", dest="selected_tests", nargs="+", default=[], metavar="TEST", help="select test by name")
    parser.add_argument(
        "-l", "--log-level", nargs="?", default=logging.WARNING, metavar="LOG-LEVEL", help="select logging level"
    )
    parser.set_defaults(func=test_interactions)


def format_warnings():
    def warning_on_one_line(message, category, _filename, _lineno, _file=None, _line=None):
        string = "%s: %s\n" % (category.__name__, message)
        return console_formatting.bold(string)

    warnings.formatwarning = warning_on_one_line


def show_deprecation_warnings():
    warnings.simplefilter("always", category=DeprecationWarning)


def main(args=None):
    format_warnings()
    show_deprecation_warnings()
    root_parser = argparse.ArgumentParser(description="Use the Tala SDK for the Talkamatic Dialogue Manager (TDM).")
    subparsers = root_parser.add_subparsers()
    add_verify_subparser(subparsers)
    add_generate_subparser(subparsers)
    add_create_ddd_subparser(subparsers)
    add_create_backend_config_subparser(subparsers)
    add_create_ddd_config_subparser(subparsers)
    add_create_deployments_config_subparser(subparsers)
    add_version_subparser(subparsers)
    add_interact_subparser(subparsers)
    add_test_subparser(subparsers)

    parsed_args = root_parser.parse_args(args)
    with _config_exception_handling():
        parsed_args.func(parsed_args)


if __name__ == "__main__":
    main()
