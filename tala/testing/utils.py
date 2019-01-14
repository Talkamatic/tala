class EqualityAssertionTestCaseMixin:
    def assert_eq_returns_true_and_ne_returns_false_symmetrically(self, object1, object2):
        self.assertEquals(
            object1, object2, "%s of type %s != %s of type %s" %
            (unicode(object1), object1.__class__, unicode(object2), object2.__class__)
        )
        self.assertFalse(object1 != object2)

        self.assertEquals(
            object2, object1, "%s of type %s != %s of type %s" %
            (unicode(object2), object2.__class__, unicode(object1), object1.__class__)
        )
        self.assertFalse(object2 != object1)

    def assert_eq_returns_false_and_ne_returns_true_symmetrically(self, object1, object2):
        self.assertNotEquals(object1, object2)
        self.assertFalse(object1 == object2)

        self.assertNotEquals(object2, object1)
        self.assertFalse(object2 == object1)
