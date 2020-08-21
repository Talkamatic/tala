from tala.model.common import Modality
from tala.model.speaker import Speaker
from tala.model.semantic_object import SemanticObject, OntologySpecificSemanticObject, SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.equality import EqualityMixin
from tala.utils import float_comparison
from tala.utils.unicodify import unicodify


class MoveException(Exception):
    pass


class Move(SemanticObject, AsSemanticExpressionMixin, EqualityMixin):
    QUIT = "quit"
    GREET = "greet"
    NO_MOVE = "no_move"
    MUTE = "mute"
    UNMUTE = "unmute"

    ASK = "ask"
    ANSWER = "answer"
    REQUEST = "request"
    REPORT = "report"
    PREREPORT = "prereport"

    def __init__(
        self,
        type,
        understanding_confidence=None,
        speaker=None,
        modality=None,
        weighted_understanding_confidence=None,
        utterance=None,
        ddd_name=None,
        perception_confidence=None
    ):
        SemanticObject.__init__(self)
        self._type = type
        self._perception_confidence = None
        self._understanding_confidence = None
        self._weighted_understanding_confidence = None
        self._speaker = None
        self._modality = None
        self._ddd_name = None
        self._background = None
        self._utterance = None
        if (
            understanding_confidence is not None or speaker is not None or modality is not None or utterance is not None
            or ddd_name is not None or perception_confidence is not None
        ):
            self.set_realization_data(
                understanding_confidence=understanding_confidence,
                speaker=speaker,
                modality=modality,
                utterance=utterance,
                ddd_name=ddd_name,
                perception_confidence=perception_confidence
            )
            if weighted_understanding_confidence is not None:
                self.weighted_understanding_confidence = weighted_understanding_confidence

    def is_move(self):
        return True

    def get_type(self):
        return self._type

    @property
    def understanding_confidence(self):
        return self._understanding_confidence

    @property
    def weighted_understanding_confidence(self):
        return self._weighted_understanding_confidence

    @weighted_understanding_confidence.setter
    def weighted_understanding_confidence(self, confidence):
        self._weighted_understanding_confidence = confidence

    @property
    def perception_confidence(self):
        return self._perception_confidence

    @property
    def confidence(self):
        confidence_sources = [self.perception_confidence, self.weighted_understanding_confidence]
        if None in confidence_sources:
            return None
        return self.perception_confidence * self.understanding_confidence

    @property
    def weighted_confidence(self):
        confidence_sources = [self.perception_confidence, self.weighted_understanding_confidence]
        if None in confidence_sources:
            return None
        return self.perception_confidence * self.weighted_understanding_confidence

    def get_speaker(self):
        return self._speaker

    def get_modality(self):
        return self._modality

    def get_utterance(self):
        return self._utterance

    def set_ddd_name(self, ddd_name):
        self._ddd_name = ddd_name

    def get_ddd_name(self):
        return self._ddd_name

    def set_realization_data(
        self,
        understanding_confidence=None,
        speaker=None,
        modality=None,
        utterance=None,
        ddd_name=None,
        perception_confidence=None
    ):
        self._verify_realization_data(
            understanding_confidence=understanding_confidence, speaker=speaker, modality=modality, ddd_name=ddd_name
        )
        self._perception_confidence = perception_confidence
        if self._perception_confidence is None:
            self._perception_confidence = 1.0
        self._understanding_confidence = understanding_confidence
        if self._understanding_confidence is None:
            self._understanding_confidence = 1.0
        self._weighted_understanding_confidence = self._understanding_confidence
        self._speaker = speaker
        self._modality = modality or Modality.SPEECH
        self._utterance = utterance
        self._ddd_name = ddd_name

    def is_realized(self):
        return self._understanding_confidence is not None or self._speaker is not None or self._modality is not None \
               or (self._speaker == Speaker.USR and self._ddd_name is not None)

    def _verify_realization_data(self, understanding_confidence=None, speaker=None, modality=None, ddd_name=None):
        if self.is_realized():
            raise MoveException("realization data already set")
        if speaker is None:
            raise MoveException("speaker must be supplied")
        if speaker == Speaker.SYS:
            if understanding_confidence is not None and understanding_confidence != 1.0:
                raise MoveException("understanding confidence below 1.0 not allowed for system moves")
        if speaker == Speaker.USR:
            if understanding_confidence is None:
                raise MoveException("understanding confidence must be supplied for user moves")
            if ddd_name is None:
                raise MoveException("ddd_name must be supplied")
        if modality not in Modality.MODALITIES:
            raise MoveException("unsupported modality: '%s'" % modality)

    def __hash__(self):
        return hash((
            self.__class__.__name__, self._type, self._perception_confidence, self._understanding_confidence,
            self._weighted_understanding_confidence, self._speaker, self._utterance, self._ddd_name
        ))

    def __str__(self):
        return self._get_expression(True)

    def _get_expression(self, include_attributes):
        string = "Move("
        string += self._type
        if include_attributes:
            string += self._build_string_from_attributes()
        string += ")"
        return string

    def _build_string_from_attributes(self):
        string = ""
        if self._ddd_name:
            string += ", ddd_name=%r" % self._ddd_name
        if self._speaker:
            string += ", speaker=%s" % self._speaker
        if self._understanding_confidence is not None:
            string += ", understanding_confidence=%s" % self._understanding_confidence
        if self._weighted_understanding_confidence is not None:
            string += ", weighted_understanding_confidence=%s" % self._weighted_understanding_confidence
        if self.perception_confidence is not None:
            string += ", perception_confidence=%s" % self.perception_confidence
        if self._modality:
            string += ", modality=%s" % self._modality
        if self._utterance:
            string += ", utterance=%r" % self._utterance
        return string

    @staticmethod
    def _is_confidence_equal(this, other):
        if this is None:
            return other is None
        return float_comparison.isclose(this, other)

    def _are_understanding_confidences_equal(self, other):
        return self._is_confidence_equal(self.understanding_confidence,
                                         other.understanding_confidence) and self._is_confidence_equal(
                                             self.weighted_understanding_confidence,
                                             other.weighted_understanding_confidence
                                         )

    def _are_perception_confidences_equal(self, other):
        return self._is_confidence_equal(self.perception_confidence, other.perception_confidence)

    def class_internal_move_content_equals(self, other):
        return True

    def move_content_equals(self, other):
        try:
            return (self.get_type() == other.get_type() and self.class_internal_move_content_equals(other))
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def is_icm(self):
        return False

    def is_question_raising(self):
        return self.get_type() == Move.ASK

    def is_turn_yielding(self):
        return self.get_type() == Move.ANSWER

    def to_rich_string(self):
        return "%s:%s:%s" % (str(self), self._speaker, self._understanding_confidence)

    def uprank(self, amount):
        self._weighted_understanding_confidence *= (1 + amount)

    def downrank(self, amount):
        self._weighted_understanding_confidence *= (1 - amount)

    def set_background(self, background):
        self._background = background

    def as_dict(self):
        return {
            "ddd": self._ddd_name,
            "understanding_confidence": self._understanding_confidence,
            "perception_confidence": self.perception_confidence,
        }

    def as_semantic_expression(self):
        return self._type


class MoveWithSemanticContent(Move, SemanticObjectWithContent):
    def __init__(self, type, content, *args, **kwargs):
        Move.__init__(self, type, *args, **kwargs)
        SemanticObjectWithContent.__init__(self, content)
        self._content = content

    def get_content(self):
        return self._content

    def __hash__(self):
        return hash((
            self.__class__.__name__, self._type, self._perception_confidence, self._understanding_confidence,
            self._weighted_understanding_confidence, self._speaker, self._utterance, self._ddd_name
        ))

    def _get_expression(self, include_attributes):
        string = "Move("
        string += "%s(%s" % (self._type, str(self._content))
        if self._background:
            string += ", %s" % unicodify(self._background)
        string += ")"
        if include_attributes:
            string += self._build_string_from_attributes()
        string += ")"
        return string

    def class_internal_move_content_equals(self, other):
        return self._content == other._content


class ICMMove(Move):
    RERAISE = "reraise"
    PER = "per"
    ACC = "acc"
    SEM = "sem"
    UND = "und"
    ACCOMMODATE = "accommodate"
    LOADPLAN = "loadplan"
    RESUME = "resume"

    INT = "int"
    POS = "pos"
    NEG = "neg"

    def __init__(
        self,
        type,
        understanding_confidence=None,
        speaker=None,
        polarity=None,
        ddd_name=None,
        perception_confidence=None
    ):
        if polarity is None:
            polarity = ICMMove.POS
        self._polarity = polarity
        Move.__init__(
            self,
            type,
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            ddd_name=ddd_name,
            perception_confidence=perception_confidence
        )

    def class_internal_move_content_equals(self, other):
        return (self._polarity == other._polarity and self._type == other._type)

    def get_polarity(self):
        return self._polarity

    def is_icm(self):
        return True

    def is_issue_icm(self):
        return False

    def is_question_raising(self):
        return False

    def is_negative_perception_icm(self):
        if self.get_type() == ICMMove.PER:
            return self.get_polarity() == ICMMove.NEG
        else:
            return False

    def is_positive_acceptance_icm(self):
        if self.get_type() == ICMMove.ACC:
            return self.get_polarity() == ICMMove.POS
        else:
            return False

    def is_negative_acceptance_issue_icm(self):
        return False

    def is_negative_acceptance_icm(self):
        if (self.get_type() == ICMMove.ACC and self.get_polarity() == ICMMove.NEG):
            return True
        else:
            return False

    def get_semantic_expression(self):
        string = "ICMMove(%s" % self._icm_to_string()
        if self._speaker:
            string += ", speaker=%s" % self._speaker
        if self._understanding_confidence is not None:
            string += ", understanding_confidence=%s" % self._understanding_confidence
        if self.perception_confidence is not None:
            string += ", perception_confidence=%s" % self.perception_confidence
        string += ")"
        return string

    def is_negative_understanding_icm(self):
        return (self.get_type() == ICMMove.UND and self.get_polarity() == ICMMove.NEG)

    def is_positive_understanding_icm_with_non_neg_content(self):
        return False

    def is_interrogative_understanding_icm_with_non_neg_content(self):
        return False

    def is_grounding_proposition(self):
        return False

    def is_turn_yielding(self):
        return self.get_type() == ICMMove.ACC and self._polarity == ICMMove.NEG

    def __str__(self):
        string = "ICMMove(%s" % self._icm_to_string()
        if self._speaker:
            string += ", speaker=%s" % self._speaker
        if self._understanding_confidence is not None:
            string += ", understanding_confidence=%s" % self._understanding_confidence
        if self.perception_confidence is not None:
            string += ", perception_confidence=%s" % self.perception_confidence
        string += ")"
        return string

    def _icm_to_string(self):
        if self._type in [ICMMove.PER, ICMMove.ACC, ICMMove.UND, ICMMove.SEM]:
            return "icm:%s*%s" % (self._type, self._polarity)
        return "icm:%s" % self._type

    def as_semantic_expression(self):
        return self._icm_to_string()


class IssueICMMove(ICMMove):
    def is_issue_icm(self):
        return True

    def is_negative_acceptance_issue_icm(self):
        if (self.get_type() == ICMMove.ACC and self.get_polarity() == ICMMove.NEG):
            return True
        return False

    def _icm_to_string(self):
        return "%s:issue" % ICMMove._icm_to_string(self)


class ICMMoveWithContent(ICMMove):
    def __init__(self, type, content, content_speaker=None, *args, **kwargs):
        ICMMove.__init__(self, type, *args, **kwargs)
        self._content = content
        self._content_speaker = self._get_checked_content_speaker(content_speaker)

    def get_content(self):
        return self._content

    def _get_checked_content_speaker(self, speaker):
        if (speaker in [Speaker.USR, Speaker.SYS, Speaker.MODEL, None]):
            return speaker
        raise Exception("'%s' is not a valid value for content_speaker" % speaker)

    def get_content_speaker(self):
        return self._content_speaker

    def _icm_to_string(self):
        if self._content_speaker is not None:
            return "icm:%s*%s:%s*%s" % (self._type, self._polarity, self._content_speaker, self._content)

        if self._type == ICMMove.PER:
            return 'icm:%s*%s:"%s"' % (self._type, self._polarity, self._content)
        if self._type in [ICMMove.ACC, ICMMove.UND, ICMMove.SEM]:
            return "icm:%s*%s:%s" % (self._type, self._polarity, self._content)
        return "icm:%s:%s" % (self._type, self._content)

    def class_internal_move_content_equals(self, other):
        return (
            self._polarity == other._polarity and self._type == other._type and self._content == other._content
            and self._content_speaker == other._content_speaker
        )

    def is_question_raising(self):
        return (
            self.get_type() == ICMMove.UND and self.get_content() is not None
            and not (self.get_polarity() == ICMMove.POS and not self.get_content().is_positive())
        )

    def is_positive_understanding_icm_with_non_neg_content(self):
        return (
            self.get_type() == ICMMove.UND and self.get_polarity() == ICMMove.POS and self.get_content().is_positive()
        )

    def is_interrogative_understanding_icm_with_non_neg_content(self):
        return (
            self.get_type() == ICMMove.UND and self.get_polarity() == ICMMove.INT and self.get_content().is_positive()
        )

    def is_grounding_proposition(self):
        return self.get_type() == ICMMove.UND and self.get_polarity() in [ICMMove.POS, ICMMove.INT]


class ICMMoveWithStringContent(ICMMoveWithContent):
    pass


class ICMMoveWithSemanticContent(ICMMoveWithContent, MoveWithSemanticContent):
    def __init__(
        self,
        type,
        content,
        understanding_confidence=None,
        speaker=None,
        ddd_name=None,
        content_speaker=None,
        polarity=None,
        perception_confidence=None
    ):
        MoveWithSemanticContent.__init__(
            self,
            type,
            content,
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            ddd_name=ddd_name,
            perception_confidence=perception_confidence
        )
        ICMMoveWithContent.__init__(
            self,
            type,
            content,
            content_speaker=content_speaker,
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            polarity=polarity,
            ddd_name=ddd_name,
            perception_confidence=perception_confidence
        )


class ReportMove(MoveWithSemanticContent):
    def __init__(self, content):
        self._content = content
        MoveWithSemanticContent.__init__(self, Move.REPORT, content)

    @property
    def content(self):
        return self._content

    def as_semantic_expression(self):
        return f"report({self._content.as_semantic_expression()})"

    def is_turn_yielding(self):
        return True

    def _get_expression(self, include_attributes):
        string = "report(%s" % unicodify(self.content)
        if self._background:
            string += ", %s" % unicodify(self._background)
        if include_attributes:
            string += self._build_string_from_attributes()
        string += ")"
        return string

    def class_internal_move_content_equals(self, other):
        return (self.content == other.content)


class PrereportMove(Move, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, service_action, arguments):
        self.service_action = service_action
        self.arguments = arguments
        Move.__init__(self, Move.PREREPORT)
        OntologySpecificSemanticObject.__init__(self, ontology_name)

    def get_service_action(self):
        return self.service_action

    def get_arguments(self):
        return self.arguments

    def __str__(self):
        return "prereport(%s, %s%s)" % (
            self.service_action, unicodify(self.arguments), self._build_string_from_attributes()
        )

    def as_semantic_expression(self):
        return str(self)

    def class_internal_move_content_equals(self, other):
        return (self.service_action == other.service_action and self.arguments == other.arguments)


class NoMove(Move):
    def __init__(self, *args, **kwargs):
        super(NoMove, self).__init__(Move.NO_MOVE, *args, **kwargs)


class GreetMove(Move):
    def __init__(self, *args, **kwargs):
        super(GreetMove, self).__init__(Move.GREET, *args, **kwargs)


class MuteMove(Move):
    def __init__(self, *args, **kwargs):
        super(MuteMove, self).__init__(Move.MUTE, *args, **kwargs)


class UnmuteMove(Move):
    def __init__(self, *args, **kwargs):
        super(UnmuteMove, self).__init__(Move.UNMUTE, *args, **kwargs)


class QuitMove(Move):
    def __init__(self, *args, **kwargs):
        super(QuitMove, self).__init__(Move.QUIT, *args, **kwargs)


class AskMove(MoveWithSemanticContent):
    def __init__(self, question, *args, **kwargs):
        MoveWithSemanticContent.__init__(self, Move.ASK, question, *args, **kwargs)

    def as_semantic_expression(self):
        return f"ask({self._content.as_semantic_expression()})"


class AnswerMove(MoveWithSemanticContent):
    def __init__(self, answer, *args, **kwargs):
        MoveWithSemanticContent.__init__(self, Move.ANSWER, answer, *args, **kwargs)

    def as_semantic_expression(self):
        return f"answer({self._content.as_semantic_expression()})"


class RequestMove(MoveWithSemanticContent):
    def __init__(self, action, *args, **kwargs):
        MoveWithSemanticContent.__init__(self, Move.REQUEST, action, *args, **kwargs)

    def as_semantic_expression(self):
        return f"request({self._content.as_semantic_expression()})"
