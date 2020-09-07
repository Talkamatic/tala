class EqualityAssertionTestCaseMixin:
    def assert_eq_returns_true_and_ne_returns_false_symmetrically(self, object1, object2):
        assert object1 == object2
        assert not (object1 != object2)
        assert object2 == object1
        assert not (object2 != object1)

    def assert_eq_returns_false_and_ne_returns_true_symmetrically(self, object1, object2):
        assert object1 != object2
        assert not (object1 == object2)
        assert object2 != object1
        assert not (object2 == object1)
