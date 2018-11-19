# This module makes some unittest features from python 2.7 available in 2.6.

import sys
if sys.version_info >= (2, 7):
    pyunit = __import__('unittest')

    class TestLoader(pyunit.TestLoader):
        pass

    class TestSuite(pyunit.TestSuite):
        pass

    class TextTestRunner(pyunit.TextTestRunner):
        pass

    class TestCase(pyunit.TestCase):
        pass

else:
    import unittest2

    class TestLoader(unittest2.TestLoader):
        pass

    class TestSuite(unittest2.TestSuite):
        pass

    class TextTestRunner(unittest2.TextTestRunner):
        pass

    class _AssertRaisesContext(object):
        """A context manager used to implement TestCase.assertRaises* methods."""

        def __init__(self, expected, test_case, expected_regexp=None):
            self.expected = expected
            self.failureException = test_case.failureException
            self.expected_regexp = expected_regexp

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, tb):
            if exc_type is None:
                try:
                    exc_name = self.expected.__name__
                except AttributeError:
                    exc_name = unicode(self.expected)
                raise self.failureException(
                    "{0} not raised".format(exc_name))
            if not issubclass(exc_type, self.expected):
                # let unexpected exceptions pass through
                return False
            self.exception = exc_value # store for later retrieval
            if self.expected_regexp is None:
                return True

            expected_regexp = self.expected_regexp
            if isinstance(expected_regexp, basestring):
                expected_regexp = re.compile(expected_regexp)
            if not expected_regexp.search(unicode(exc_value)):
                raise self.failureException('"%s" does not match "%s"' %
                         (expected_regexp.pattern, unicode(exc_value)))
            return True

    class TestCase(unittest2.TestCase, MaharaniTestCase):
        def assertGreater(self, a, b, msg=None):
            """Just like self.assertTrue(a > b), but with a nicer default message."""
            if not a > b:
                standardMsg = '%s not greater than %s' % (safe_repr(a), safe_repr(b))
                self.fail(self._formatMessage(msg, standardMsg))

        def assertGreaterEqual(self, a, b, msg=None):
            """Just like self.assertTrue(a >= b), but with a nicer default message."""
            if not a >= b:
                standardMsg = '%s not greater than or equal to %s' % (safe_repr(a), safe_repr(b))
                self.fail(self._formatMessage(msg, standardMsg))

        def assertRaises(self, excClass, callableObj=None, *args, **kwargs):
            context = _AssertRaisesContext(excClass, self)
            if callableObj is None:
                return context
            with context:
                callableObj(*args, **kwargs)

        def assertItemsEqual(self, expected_seq, actual_seq, msg=None):
            self.assertEqual(sorted(expected_seq), sorted(actual_seq), msg)

    def assertMultiLineEqual(self, first, second, msg=None):
        """Assert that two multi-line strings are equal."""
        self.assertIsInstance(first, basestring,
                'First argument is not a string')
        self.assertIsInstance(second, basestring,
                'Second argument is not a string')

        if first != second:
            # don't use difflib if the strings are too long
            if (len(first) > self._diffThreshold or
                len(second) > self._diffThreshold):
                self._baseAssertEqual(first, second, msg)
            firstlines = first.splitlines(True)
            secondlines = second.splitlines(True)
            if len(firstlines) == 1 and first.strip('\r\n') == first:
                firstlines = [first + '\n']
                secondlines = [second + '\n']
            standardMsg = '%s != %s' % (safe_repr(first, True),
                                        safe_repr(second, True))
            diff = '\n' + ''.join(difflib.ndiff(firstlines, secondlines))
            standardMsg = self._truncateMessage(standardMsg, diff)
            self.fail(self._formatMessage(msg, standardMsg))
