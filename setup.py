#!/usr/bin/env python2.7

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
        use_scm_version={"write_to": "tala/installed_version.py"},
        setup_requires=["setuptools_scm"],
        name="tala",
        description="Design dialogue domain descriptions (DDDs) for TDM",
        long_description=readme(),
        long_description_content_type="text/markdown",
        classifiers=[
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2.7",
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
            "Jinja2~=2.10",
            "pathlib==1.0.1",
            "lxml==4.2.5",
            "iso8601==0.1.12",
            "python-magic==0.4.15",
            "prompt-toolkit==2.0.8",
            "requests==2.21.0",
        ],
        dependency_links=[],
    )
