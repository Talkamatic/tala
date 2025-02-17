#!/usr/bin/env python3.11

from setuptools import find_packages, setup

try:
    from setuptools.command.build_py import build_py
except ImportError:
    from distutils.command.build_py import build_py  # noqa: F401


def readme():
    with open("README.md") as f:
        return f.read()


if __name__ == "__main__":
    setup(
        use_scm_version={
            "write_to": "tala/installed_version.py",
            "root": ".",
            "relative_to": __file__,
            "git_describe_command": "git describe --dirty --tags --long "
                    "--exclude tdm-* --exclude *candidate* --exclude *latest* --exclude *master* ",
        },
        setup_requires=["setuptools_scm"],
        name="tala",
        description="Design dialogue domain descriptions (DDDs) for TDM",
        long_description=readme(),
        long_description_content_type="text/markdown",
        classifiers=[
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3.11",
        ],
        keywords="tala tdm ddd ddds dialogue conversation AI",
        packages=find_packages(exclude=["tala/ddds", "test", "*.test", "test.*", "*.test.*"]),
        package_dir={"tala": "tala"},
        package_data={
            "tala": [
                "ddd/maker/templates/*.txt",
                "ddd/maker/templates/*.xml",
                "ddd/schemas/grammar.xsd",
                "ddd/schemas/grammar_rgl.xsd",
                "ddd/schemas/ontology.xsd",
                "ddd/schemas/service_interface.xsd",
                "ddd/schemas/domain.xsd",
                "nl/entity_examples/*/*.csv",
            ]
        },
        scripts=[],
        entry_points={
            "console_scripts": [
                "tala = tala.cli.console_script:main",
            ],
        },
        url="http://www.talkamatic.se",
        author="Talkamatic",
        author_email="dev@talkamatic.se",
        install_requires=[
            "Jinja2>=3.0.1, <4",
            "dill>=0.3.6",
            "iso8601>=0.1.14",
            "lxml>=4.6.3",
            "prompt-toolkit>=3.0.19",
            "requests>=2.26.0",
            "structlog>=21.1.0",
            "setuptools>=68.2.2",
            "setuptools-scm>=8.0.4",
            "paho-mqtt==2.1.0",
            "azure-data-tables>=12.5.0"

        ],
        dependency_links=[],
    )  # yapf: disable
