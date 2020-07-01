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
    def is_user_moves_turn(self):
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


class UserMovesTurn(UserInputTurn):
    def __init__(self, moves, line_number):
        super(UserMovesTurn, self).__init__(line_number)
        self._moves = moves

    @property
    def is_user_moves_turn(self):
        return True

    @property
    def moves(self):
        return self._moves


class UserPassivityTurn(Turn):
    @property
    def is_user_passivity_turn(self):
        return True


class SystemOutputTurn(Turn):
    @property
    def is_system_output_turn(self):
        return True

    @property
    def is_system_utterance_turn(self):
        return False

    @property
    def is_gui_output_turn(self):
        return False


class SystemUtteranceTurn(SystemOutputTurn):
    def __init__(self, utterance, line_number):
        super(SystemOutputTurn, self).__init__(line_number)
        self._utterance = utterance

    @property
    def is_system_utterance_turn(self):
        return True

    @property
    def utterance(self):
        return self._utterance

    def __str__(self):
        return "S>"


class GuiOutputTurn(SystemOutputTurn):
    def __init__(self, pattern, line_number):
        super(SystemOutputTurn, self).__init__(line_number)
        self._pattern = pattern

    @property
    def is_gui_output_turn(self):
        return True

    @property
    def pattern(self):
        return self._pattern

    def __str__(self):
        return "G>"


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
