import argparse
import contextlib
import os
import warnings
import logging

import structlog
import json

from requests.exceptions import MissingSchema

from tala.cli import console_formatting
from tala.cli.tdm.tdm_cli import TDMCLI
from tala.config import BackendConfig, DddConfig, DeploymentsConfig, BackendConfigNotFoundException, \
    DddConfigNotFoundException, DeploymentsConfigNotFoundException
from tala.ddd.maker.ddd_maker import DddMaker
from tala import installed_version
from tala.log.logger import configure_stdout_logging, configure_file_logging
from tala.cli.argument_parser import add_common_backend_arguments, add_shared_frontend_and_backend_arguments
from tala.log.formats import VALID_TIS_LOGGING_FORMATS, TIS_LOGGING_AUTO, VALID_TIS_UPDATE_FORMATS, TIS_LOGGING_FULL
from tala.service.constants import DEFAULT_PORT
from tala import domain_orchestration


class UnexpectedDDDException(Exception):
    pass


class ConfigAlreadyExistsException(Exception):
    pass


class ConfigNotFoundException(Exception):
    pass


class InvalidArgumentException(Exception):
    pass


def create_ddd(args):
    DddMaker(args.name, use_rgl=False, target_dir=args.target_dir).make()


def create_backend_config(args):
    if os.path.exists(args.filename):
        raise ConfigAlreadyExistsException(
            f"Expected to be able to create backend config file '{args.filename}' but it already exists."
        )
    BackendConfig().write_default_config(args.ddd, args.filename)


def configure_structlog_and_create_logger(args):
    if args.log_to_stdout:
        configure_stdout_logging(args.log_level)
    else:
        configure_file_logging(level=args.log_level)
    return structlog.get_logger("tala")


def create_orchestrated_domain_bundle(args):
    odb_as_json = domain_orchestration.create_odb_as_json(
        args.config, args.overridden_ddd_config_paths, args.should_greet, args.logged_tis_format,
        args.tis_update_format, args.log_to_stdout, args.log_level
    )
    odb = domain_orchestration.OrchestratedDomainBundle(odb_as_json).as_json()
    _store_odb(odb, args.output)


def _store_odb(odb, output_dir):
    print(f"storing orchestrated domain bundle in file '{output_dir}'")
    file = open(output_dir, 'w')
    file.write(json.dumps(odb))
    file.close()


def create_ddd_config(args):
    if os.path.exists(args.filename):
        raise ConfigAlreadyExistsException(
            f"Expected to be able to create DDD config file '{args.filename}' but it already exists."
        )
    DddConfig().write_default_config(path=args.filename, use_rgl=False)


def create_deployments_config(args):
    if os.path.exists(args.filename):
        raise ConfigAlreadyExistsException(
            f"Expected to be able to create deployments config file '{args.filename}' but it already exists."
        )
    DeploymentsConfig().write_default_config(args.filename)


@contextlib.contextmanager
def _config_exception_handling():
    def generate_message(name, command_name, config):
        return f"Expected {name} config '{config}' to exist but it was not found. To create it, run " \
               f"'tala {command_name} --filename {config}'."

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
    resume_session = args.resume_session
    tdm_cli = TDMCLI(url, resume_session)

    try:
        tdm_cli.run()
    except (KeyboardInterrupt, EOFError):
        tdm_cli.stop()
    except MissingSchema:
        environments = list(config.read().keys())
        print(f"Expected a URL or one of the known environments {environments} but got '{url}'")


def add_create_ddd_subparser(subparsers):
    parser = subparsers.add_parser("create-ddd", help="create a new DDD")
    parser.set_defaults(func=create_ddd)
    parser.add_argument("name", help="Name of the DDD, e.g. my_ddd")
    parser.add_argument(
        "--target-dir", default=".", metavar="DIR", help="target directory, will be created if it doesn't exist"
    )


def add_create_odb_subparser(subparsers):
    parser = subparsers.add_parser("create-odb", help="create a new ODB")
    parser.set_defaults(func=create_orchestrated_domain_bundle)

    backend_group = parser.add_argument_group("backend")
    backend_group.add_argument("output", help="Directory where the ODB file will be stored")
    backend_group.add_argument("--should-greet", action="store_true", default=False)
    add_common_backend_arguments(backend_group)
    add_shared_frontend_and_backend_arguments(backend_group)
    logging_group = parser.add_argument_group("logging")
    logging_group.add_argument(
        "--log-to-stdout",
        action="store_true",
        default=False,
        help="If enabled, logging is done to stdout instead of to a file"
    )
    logging_group.add_argument("--port", type=int, default=DEFAULT_PORT, help="listen for connections on this port")
    choices = [TIS_LOGGING_AUTO] + VALID_TIS_LOGGING_FORMATS
    logging_group.add_argument(
        "--tis-format",
        "-tf",
        dest="logged_tis_format",
        choices=choices,
        default=TIS_LOGGING_AUTO,
        help="log TIS on this format"
    )
    logging_group.add_argument(
        "--tis-update-format",
        choices=VALID_TIS_UPDATE_FORMATS,
        default=TIS_LOGGING_FULL,
        help="log TIS updates on this format"
    )


def add_create_backend_config_subparser(subparsers):
    parser = subparsers.add_parser("create-backend-config", help="create a backend config")
    parser.set_defaults(func=create_backend_config)
    parser.add_argument("ddd", help="name of the active DDD, e.g. my_ddd")
    parser.add_argument(
        "--filename",
        default=BackendConfig.default_name(),
        metavar="NAME",
        help=f"filename of the backend config, e.g. {BackendConfig.default_name()}"
    )


def add_create_ddd_config_subparser(subparsers):
    parser = subparsers.add_parser("create-ddd-config", help="create a DDD config")
    parser.set_defaults(func=create_ddd_config)
    parser.add_argument(
        "--filename",
        default=DddConfig.default_name(),
        metavar="NAME",
        help=f"filename of the DDD config, e.g. {DddConfig.default_name()}"
    )


def add_create_deployments_config_subparser(subparsers):
    parser = subparsers.add_parser("create-deployments-config", help="create a deployments config")
    parser.set_defaults(func=create_deployments_config)
    parser.add_argument(
        "--filename",
        default=DeploymentsConfig.default_name(),
        metavar="NAME",
        help=f"filename of the deployments config, e.g. {DeploymentsConfig.default_name()}"
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
        help=f"override the default deployments config {DeploymentsConfig.default_name()!r}"
    )
    parser.add_argument(
        "--resume-session",
        dest="resume_session",
        default=None,
        const="tala-session.state",
        nargs="?",
        help="Session object to be resumed. If parameter omitted, tala will resume latest session."
    )


def add_interact_subparser(subparsers):
    parser = subparsers.add_parser("interact", help="start an interactive chat with a deployed DDD")
    add_deployment_config_arguments(parser)
    parser.set_defaults(func=interact)


def _add_test_arguments(parser):
    add_deployment_config_arguments(parser)
    parser.add_argument(dest="tests_filenames", nargs="+", metavar="TEST-FILE", help="specify DDD test files")
    parser.add_argument("-t", dest="selected_tests", nargs="+", default=[], metavar="TEST", help="select test by name")
    parser.add_argument(
        "-l", "--log-level", nargs="?", default=logging.WARNING, metavar="LOG-LEVEL", help="select logging level"
    )


def format_warnings():
    def warning_on_one_line(message, category, _filename, _lineno, _file=None, _line=None):
        string = f"{category.__name__}: {message}\n"
        return console_formatting.bold(string)

    warnings.formatwarning = warning_on_one_line


def show_deprecation_warnings():
    warnings.simplefilter("always", category=DeprecationWarning)


def main(args=None):
    format_warnings()
    show_deprecation_warnings()
    root_parser = argparse.ArgumentParser(description="Use the Tala SDK for the Talkamatic Dialogue Manager (TDM).")
    subparsers = root_parser.add_subparsers()
    add_create_ddd_subparser(subparsers)
    add_create_odb_subparser(subparsers)
    add_create_backend_config_subparser(subparsers)
    add_create_ddd_config_subparser(subparsers)
    add_create_deployments_config_subparser(subparsers)
    add_version_subparser(subparsers)
    add_interact_subparser(subparsers)

    parsed_args = root_parser.parse_args(args)
    with _config_exception_handling():
        parsed_args.func(parsed_args)


if __name__ == "__main__":
    main()
