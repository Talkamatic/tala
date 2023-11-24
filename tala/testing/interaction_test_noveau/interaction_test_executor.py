from tala.testing.interaction_test_noveau.interaction_tester import InteractionTester


class InteractionTestExecutorBase:
    def run_ng_interaction_test(self, testcase):
        self._given_testcase(testcase)
        self._when_running_testcase()

    def _given_testcase(self, testcase):
        self._testcase = testcase

    def _when_running_testcase(self):
        tester = InteractionTester()
        self._result = tester.run_testcase(self._testcase)


class InteractionTestExecutorNoAssert(InteractionTestExecutorBase):
    @property
    def result(self):
        return self._result


class InteractionTestExecutorAssert(InteractionTestExecutorBase):
    def _when_running_testcase(self):
        super()._when_running_testcase()
        self._then_test_is_succesful()

    def _then_test_is_succesful(self):
        print(self._result["transcript"])
        assert self._result["success"], self._result["failure_description"]
