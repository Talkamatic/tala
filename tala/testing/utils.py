from tala.config import BackendConfig


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


def load_mockup_travel(extended_ddd_set_loader):
    load_internal_ddds(extended_ddd_set_loader, ["mockup_travel"], ".")


def load_internal_ddds(extended_ddd_set_loader, ddds, package, rerank_amount=None):
    rerank_amount = rerank_amount or BackendConfig.DEFAULT_RERANK_AMOUNT
    extended_ddd_set_loader.ensure_ddds_loaded(ddds, path=f"{package}/ddds", rerank_amount=rerank_amount)
