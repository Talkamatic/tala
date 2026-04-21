from tala.model.user_move import DDDSpecificUserMove
from tala.testing.interaction.interaction_tester import InteractionTester


class TestInteractionTesterMovePrefix:
    def test_prefixed_move_overrides_target_ddd(self):
        tester = InteractionTester(port=None)
        tester._ddd_name = "fallback"

        move = tester._create_user_move("other:answer(hour_to_set(11))")

        assert isinstance(move, DDDSpecificUserMove)
        assert move.ddd == "other"
        assert move.semantic_expression == "answer(hour_to_set(11))"

    def test_unprefixed_move_uses_target_ddd(self):
        tester = InteractionTester(port=None)
        tester._ddd_name = "hello_world"

        move = tester._create_user_move("answer(hour_to_set(11))")

        assert isinstance(move, DDDSpecificUserMove)
        assert move.ddd == "hello_world"

    def test_prefixed_move_without_target_ddd(self):
        tester = InteractionTester(port=None)

        move = tester._create_user_move("hello_world:answer(hour_to_set(11))")

        assert isinstance(move, DDDSpecificUserMove)
        assert move.ddd == "hello_world"

    def test_icm_move_does_not_parse_as_prefix(self):
        tester = InteractionTester(port=None)
        tester._ddd_name = "hello_world"

        move = tester._create_user_move("icm:acc*pos")

        assert isinstance(move, DDDSpecificUserMove)
        assert move.ddd == "hello_world"
        assert move.semantic_expression == "icm:acc*pos"
