import argparse
import re

from tala.config import OverriddenDddConfig, BackendConfig


def add_common_backend_arguments(parser):
    def parse_ddd_config(string):
        match = re.search('^(.+):(.+)$', string)
        if match:
            ddd_name, path = match.group(1), match.group(2)
            return OverriddenDddConfig(ddd_name, path)
        else:
            raise argparse.ArgumentTypeError("Expected DDD configs on the format 'DDD:CONFIG' but got '%s'." % string)

    parser.add_argument(
        "--config",
        dest="config",
        default=None,
        help="override the default backend config %r" % BackendConfig.default_name()
    )
    parser.add_argument(
        "--ddd-config",
        dest="overridden_ddd_config_paths",
        type=parse_ddd_config,
        nargs="+",
        help="override a DDD config",
        metavar="DDD:CONFIG"
    )


def add_shared_frontend_and_backend_arguments(parser):
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    parser.add_argument(
        "--log-level", choices=log_levels, default="WARNING", help="include log entries with this severity and above"
    )
