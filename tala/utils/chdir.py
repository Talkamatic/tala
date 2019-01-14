import contextlib
import os


class DirectoryException(Exception):
    pass


@contextlib.contextmanager
def chdir(new_dir):
    working_dir = os.getcwd()
    try:
        os.chdir(str(new_dir))
    except OSError:
        raise DirectoryException("Could not change directory from %r to %r" % (working_dir, new_dir))
    try:
        yield
    finally:
        os.chdir(working_dir)
