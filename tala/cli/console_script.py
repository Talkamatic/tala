#!/usr/bin/env python2.7

import argparse
import contextlib
import os
import re
import sys
import warnings

from jinja2 import Template
from pathlib import Path

from tala.backend.dependencies.for_generating import BackendDependenciesForGenerating
from tala.cli.argument_parser import add_common_backend_arguments
from tala.cli.tdm.tdm_cli import TDMCLI
from tala.config import BackendConfig, DddConfig, RasaConfig, DeploymentsConfig, BackendConfigNotFoundException, \
    DddConfigNotFoundException, RasaConfigNotFoundException, DeploymentsConfigNotFoundException
from tala.ddd.building.ddd_builder_for_generating import DDDBuilderForGenerating
from tala import installed_version
from tala.cli import console_formatting
from tala.nl import languages
from tala.nl.rasa.generating.generator import RasaGenerator
from tala.ddd.maker import utils as ddd_maker_utils
from tala.ddd.maker.ddd_maker import DddMaker
from tala.utils.chdir import chdir


class ConfigAlreadyExistsException(Exception):
    pass


class ConfigNotFoundException(Exception):
    pass


class InvalidArgumentException(Exception):
    pass


class UnexpectedDDDException(Exception):
    pass


class UnexpectedEnvironmentException(Exception):
    pass


def create_ddd(args):
    def directory_to_class_name(directory_name):
        name_with_capitalized_words = directory_name.title()
        class_name = re.sub("[_ ]", "", name_with_capitalized_words)
        return class_name

    directory_name = args.name
    class_name = directory_to_class_name(directory_name)
    DddMaker(class_name, directory_name, args.target_dir).make()


def create_backend_config(args):
    if os.path.exists(args.filename):
        raise ConfigAlreadyExistsException(
            "Expected to be able to create backend config file '%s' but it already exists." % args.filename
        )
    BackendConfig().write_default_config(args.filename, args.ddd)


def create_ddd_config(args):
    if os.path.exists(args.filename):
        raise ConfigAlreadyExistsException(
            "Expected to be able to create DDD config file '%s' but it already exists." % args.filename
        )
    DddConfig().write_default_config(args.filename)


def create_rasa_config(args):
    if os.path.exists(args.filename):
        raise ConfigAlreadyExistsException(
            "Expected to be able to create RASA config file '%s' but it already exists." % args.filename
        )
    RasaConfig().write_default_config(args.filename)


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


def generate_rasa(args):
    backend_dependencies = BackendDependenciesForGenerating(args)
    ddd_path = Path(args.ddd)
    if not ddd_path.exists():
        raise UnexpectedDDDException("Expected DDD '{}' to exist but it didn't".format(args.ddd))

    with chdir(ddd_path / "grammar"):
        generator = RasaGenerator(backend_dependencies.ddds[0], args.language)
        data = generator.generate()
        language = languages.RASA_LANGUAGE[args.language]

        rasa_config_template = Template(
            "language: \"{{ language }}\"\n"
            "\n"
            "pipeline: \"spacy_sklearn\"\n"
            "\n"
            "data: |\n"
            "{% for line in data.splitlines() %}"
            "  {{ line }}\n"
            "{% endfor %}"
        )

        rasa_config_template.stream(language=language, data=data).dump(sys.stdout, encoding="utf-8")


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
    except RasaConfigNotFoundException as exception:
        message = generate_message("RASA", "create-rasa-config", exception.config_path)
        raise ConfigNotFoundException(message)
    except DeploymentsConfigNotFoundException as exception:
        message = generate_message("deployments", "create-deployments-config", exception.config_path)
        raise ConfigNotFoundException(message)


def version(args):
    print installed_version.version


def interact(args):
    def get_url():
        config = DeploymentsConfig(args.deployments_config).read()
        if args.environment not in config:
            raise UnexpectedEnvironmentException(
                "Expected one of the known environments {} but got '{}'".format(config.keys(), args.environment)
            )
        return config[args.environment]

    url = get_url()
    tdm_cli = TDMCLI(url)

    try:
        tdm_cli.run()
    except (KeyboardInterrupt, EOFError):
        tdm_cli.stop()


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
    parser.add_argument(
        "--rasa-config",
        dest="rasa_config",
        default=None,
        help="override the default RASA config %r" % RasaConfig.default_name()
    )


def add_generate_rasa_subparser(subparsers):
    parser = subparsers.add_parser("generate-rasa", help="generate training data for Rasa NLU 0.14")
    parser.set_defaults(func=generate_rasa)
    add_common_backend_arguments(parser)
    parser.add_argument("ddd", help="generate for this DDD")
    parser.add_argument("language", choices=languages.SUPPORTED_RASA_LANGUAGES, help="use the grammar of this language")
    parser.add_argument(
        "--rasa-config",
        dest="rasa_config",
        default=None,
        help="override the default RASA config %r" % RasaConfig.default_name()
    )


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
    parser.add_argument(
        "--filename",
        default=BackendConfig.default_name(),
        metavar="NAME",
        help="filename of the backend config, e.g. %s" % BackendConfig.default_name()
    )
    parser.add_argument("--ddd", help="name of the active DDD, e.g. my_ddd")


def add_create_ddd_config_subparser(subparsers):
    parser = subparsers.add_parser("create-ddd-config", help="create a DDD config")
    parser.set_defaults(func=create_ddd_config)
    parser.add_argument(
        "--filename",
        default=DddConfig.default_name(),
        metavar="NAME",
        help="filename of the DDD config, e.g. %s" % DddConfig.default_name()
    )


def add_create_rasa_config_subparser(subparsers):
    parser = subparsers.add_parser("create-rasa-config", help="create a TDM-specific RASA config")
    parser.set_defaults(func=create_rasa_config)
    parser.add_argument(
        "--filename",
        default=RasaConfig.default_name(),
        metavar="NAME",
        help="filename of the RASA config, e.g. %s" % RasaConfig.default_name()
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


def add_interact_subparser(subparsers):
    parser = subparsers.add_parser("interact", help="start an interactive chat with a deployed DDD")
    parser.add_argument(
        "environment",
        help="specify the environment to use, e.g. 'dev'; this maps to the keys of the deployments config"
    )
    parser.add_argument(
        "--config",
        dest="deployments_config",
        default=None,
        help="override the default deployments config %r" % DeploymentsConfig.default_name()
    )
    parser.set_defaults(func=interact)


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
    add_generate_rasa_subparser(subparsers)
    add_create_ddd_subparser(subparsers)
    add_create_backend_config_subparser(subparsers)
    add_create_ddd_config_subparser(subparsers)
    add_create_rasa_config_subparser(subparsers)
    add_create_deployments_config_subparser(subparsers)
    add_version_subparser(subparsers)
    add_interact_subparser(subparsers)

    parsed_args = root_parser.parse_args(args)
    with _config_exception_handling():
        parsed_args.func(parsed_args)


if __name__ == "__main__":
    main()
