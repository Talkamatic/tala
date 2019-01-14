# encoding: utf-8

import os
import os.path
import shutil
import tempfile

import pytest
from pathlib import Path

from tala.utils.file_writer import UTF8FileWriter


class TestFileWriter(object):
    def setup(self):
        self._temp_dir = tempfile.mkdtemp(prefix=self.__class__.__name__)
        self._cwd = os.getcwd()
        os.chdir(self._temp_dir)

        self._file_writer = None

    def teardown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._temp_dir)

    @pytest.mark.parametrize("path", [
        "mocked-data.txt",
        Path("mocked-data.txt"),
    ])
    def test_write(self, path):
        self.given_file_writer_created_with(path)
        self.given_directories_created()
        self.when_writing("mocked data")
        self.then_file_contains(expected_file=Path("mocked-data.txt"), expected_contents="mocked data")

    def given_file_writer_created_with(self, path):
        self._file_writer = UTF8FileWriter(path)

    def given_directories_created(self):
        self._file_writer.create_directories()

    def when_writing(self, data):
        self._file_writer.write(data)

    def then_file_contains(self, expected_file, expected_contents):
        with expected_file.open() as actual_file:
            actual_contents = actual_file.read()
            assert actual_contents == expected_contents

    @pytest.mark.parametrize("path", [
        "mocked-data.txt",
        Path("mocked-data.txt"),
    ])
    def test_write_utf8(self, path):
        self.given_file_writer_created_with(path)
        self.given_directories_created()
        self.when_writing(u"småfisk")
        self.then_file_contains_utf8(expected_file=Path("mocked-data.txt"), expected_contents=u"småfisk")

    def then_file_contains_utf8(self, expected_file, expected_contents):
        with expected_file.open(encoding="utf-8") as actual_file:
            actual_contents = actual_file.read()
            assert actual_contents == expected_contents

    @pytest.mark.parametrize("path", [
        "mocked/data.txt",
        Path("mocked") / "data.txt",
    ])
    def test_write_in_nested_path(self, path):
        self.given_file_writer_created_with(path)
        self.given_directories_created()
        self.when_writing("mocked data")
        self.then_file_contains(expected_file=Path("mocked") / "data.txt", expected_contents="mocked data")
