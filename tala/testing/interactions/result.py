from unittest.runner import TextTestResult

DESCRIPTIONS = {
    "FAIL": "Failure in test '{}'",
    "ERROR": "Error in test '{}'",
}


class InteractionTestResult(TextTestResult):
    def addFailure(self, test, err):
        """Called when an error has occurred. 'err' is a tuple of values as
        returned by sys.exc_info()."""
        type_, exception, traceback = err
        self.failures.append((test, str(exception)))
        self._mirrorOutput = True
        if self.showAll:
            self.stream.writeln("FAIL")
        elif self.dots:
            self.stream.write('F')
            self.stream.flush()

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln(DESCRIPTIONS[flavour].format(test.name))
            self.stream.writeln(self.separator2)
            self.stream.writeln(str(err))
            self.stream.writeln()
