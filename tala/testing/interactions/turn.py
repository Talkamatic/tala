class Turn(object):
    def __init__(self, line_number):
        self._line_number = line_number

    @property
    def is_user_input_turn(self):
        return False

    @property
    def is_system_output_turn(self):
        return False

    @property
    def is_user_passivity_turn(self):
        return False

    @property
    def is_event_turn(self):
        return False

    @property
    def line_number(self):
        return self._line_number


class UserInputTurn(Turn):
    def __init__(self, line_number):
        super(UserInputTurn, self).__init__(line_number)

    @property
    def is_user_input_turn(self):
        return True

    @property
    def is_recognition_hypotheses_turn(self):
        return False

    @property
    def is_user_interpretation_turn(self):
        return False

    @property
    def is_user_semantic_input_turn(self):
        return False

    @property
    def is_user_passivity_turn(self):
        return False


class RecognitionHypothesesTurn(UserInputTurn):
    def __init__(self, hypotheses, line_number):
        super(RecognitionHypothesesTurn, self).__init__(line_number)
        self._hypotheses = hypotheses

    @property
    def is_recognition_hypotheses_turn(self):
        return True

    @property
    def hypotheses(self):
        return self._hypotheses


class UserInterpretationTurn(UserInputTurn):
    def __init__(self, moves, line_number, modality=None, utterance=None):
        super(UserInterpretationTurn, self).__init__(line_number)
        self._moves = moves
        self._modality = modality
        self._utterance = utterance

    @property
    def is_user_interpretation_turn(self):
        return True

    @property
    def moves(self):
        return self._moves

    @property
    def modality(self):
        return self._modality

    @property
    def utterance(self):
        return self._utterance


class UserSemanticInputTurn(UserInputTurn):
    def __init__(self, semantic_input, line_number):
        super().__init__(line_number)
        self._semantic_input = semantic_input

    @property
    def is_user_semantic_input_turn(self):
        return True

    @property
    def semantic_input(self):
        return self._semantic_input


class UserPassivityTurn(Turn):
    @property
    def is_user_passivity_turn(self):
        return True


class SystemOutputTurn(Turn):
    @property
    def output(self):
        raise NotImplementedError()

    @property
    def is_system_output_turn(self):
        return True

    @property
    def is_system_utterance_turn(self):
        return False

    @property
    def is_system_moves_turn(self):
        return False


class SystemUtteranceTurn(SystemOutputTurn):
    def __init__(self, utterance, line_number):
        super(SystemOutputTurn, self).__init__(line_number)
        self._utterance = utterance

    @property
    def output(self):
        return self.utterance

    @property
    def is_system_utterance_turn(self):
        return True

    @property
    def utterance(self):
        return self._utterance

    def __str__(self):
        return "S>"


class SystemMovesTurn(SystemOutputTurn):
    def __init__(self, moves, line_number):
        super(SystemOutputTurn, self).__init__(line_number)
        self._moves = moves

    @property
    def output(self):
        return self.moves

    @property
    def is_system_moves_turn(self):
        return True

    @property
    def moves(self):
        return self._moves


class EventTurn(Turn):
    @property
    def is_event_turn(self):
        return True

    @property
    def is_notify_started_turn(self):
        return False


class NotifyStartedTurn(EventTurn):
    def __init__(self, action, parameters, line_number):
        super(NotifyStartedTurn, self).__init__(line_number)
        self._action = action
        self._parameters = parameters

    @property
    def is_notify_started_turn(self):
        return True

    @property
    def action(self):
        return self._action

    @property
    def parameters(self):
        return self._parameters
