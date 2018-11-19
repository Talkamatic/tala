import contextlib
import os

class DirectoryException(Exception): pass

@contextlib.contextmanager
def chdir(new_dir):
    working_dir = os.getcwd()
    try:
        os.chdir(new_dir)
    except OSError:
        raise DirectoryException("Could not change directory from %r to %r" % (working_dir, new_dir))
    try:
        yield
    finally:
        os.chdir(working_dir)


def readable_list(elements):
    if len(elements) == 0:
        return ""
    if len(elements) == 1:
        return elements[0]
    return "%s and %s" % (", ".join(elements[:-1]), elements[-1])


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    """
    For float comparison. See https://www.python.org/dev/peps/pep-0485/#proposed-implementation.

    Use relative tolerance, absolute tolerance, or both.

    :param a: Left operand
    :param b: Right operand
    :param rel_tol: Relative tolerance. The amount of error allowed. E.g. 5%, or the default: 1 PPB.
    :param abs_tol: Minimum absolute tolerance level.
    :return: True if a and b are within at least one of the relative or the absolute tolerances. False otherwise.
    """
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)