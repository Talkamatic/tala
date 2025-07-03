import warnings

from tala.model.common import Modality
from tala.model.confidence_estimate import ConfidenceEstimates
from tala.model.speaker import USR, SYS, MODEL
from tala.model.semantic_object import SemanticObject, OntologySpecificSemanticObject, SemanticObjectWithContent
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils import float_comparison
from tala.utils.unicodify import unicodify


class MoveException(Exception):
    pass


QUIT = "quit"
GREET = "greet"
THANK_YOU = "thanks"
THANK_YOU_RESPONSE = "thank_you_response"
INSULT_RESPONSE = "insult_response"
INSULT = "insult"
NO_MOVE = "no_move"
MUTE = "mute"
UNMUTE = "unmute"

ASK = "ask"
ANSWER = "answer"
REQUEST = "request"
REPORT = "report"
PREREPORT = "prereport"


class Move(SemanticObject, AsSemanticExpressionMixin):
    QUIT = QUIT
    GREET = GREET
    THANK_YOU = THANK_YOU
    THANK_YOU_RESPONSE = THANK_YOU_RESPONSE
    INSULT_RESPONSE = INSULT_RESPONSE
    INSULT = INSULT
    NO_MOVE = NO_MOVE
    MUTE = MUTE
    UNMUTE = UNMUTE

    ASK = ASK
    ANSWER = ANSWER
    REQUEST = REQUEST
    REPORT = REPORT
    PREREPORT = PREREPORT

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
        self._speaker = None
        self._modality = None
        self._ddd_name = None
        self._background = None
        self._utterance = None
        self._confidence_estimates = ConfidenceEstimates()
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

    def __eq__(self, other):
        try:
            if self._type == other._type \
               and self._speaker == other._speaker \
               and self._modality == other._modality \
               and self._utterance == other._utterance \
               and self._ddd_name == other._ddd_name \
               and self._background == other._background \
               and self._confidence_estimates == other._confidence_estimates:
                if hasattr(self, "weighted_understanding_confidence"):
                    return self.weighted_understanding_confidence == other.weighted_understanding_confidence
                else:
                    return True
        except AttributeError:
            pass
        return False

    def is_move(self):
        return True

    def get_type(self):
        warnings.warn("Move.get_type() is deprecated. Use Move.type_ instead.", DeprecationWarning, stacklevel=2)
        return self._type

    @property
    def type(self):
        warnings.warn("Move.type is deprecated. Use Move.type_ instead.", DeprecationWarning, stacklevel=2)
        return self._type

    @property
    def type_(self):
        return self._type

    @property
    def confidence_estimates(self):
        return self._confidence_estimates

    @property
    def perception_confidence(self):
        return self._confidence_estimates.perception_confidence

    @property
    def understanding_confidence(self):
        return self._confidence_estimates.understanding_confidence

    @property
    def weighted_understanding_confidence(self):
        return self._confidence_estimates.weighted_understanding_confidence

    @weighted_understanding_confidence.setter
    def weighted_understanding_confidence(self, confidence):
        self._confidence_estimates.weighted_understanding_confidence = confidence

    @property
    def confidence(self):
        return self._confidence_estimates.confidence

    @property
    def weighted_confidence(self):
        return self._confidence_estimates.weighted_confidence

    def get_speaker(self):
        return self._speaker

    def get_modality(self):
        return self._modality

    @property
    def modality(self):
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
        self._confidence_estimates.set_realization_data(
            perception_confidence=perception_confidence, understanding_confidence=understanding_confidence
        )
        self._speaker = speaker
        self._modality = modality or Modality.SPEECH
        self._utterance = utterance
        self._ddd_name = ddd_name

    def is_realized(self):
        return self.understanding_confidence is not None or self._speaker is not None or self._modality is not None \
               or (self._speaker == USR and self._ddd_name is not None)

    def _verify_realization_data(self, understanding_confidence=None, speaker=None, modality=None, ddd_name=None):
        if self.is_realized():
            raise MoveException("realization data already set")
        if speaker is None:
            raise MoveException("speaker must be supplied")
        if speaker == SYS:
            if understanding_confidence is not None and understanding_confidence != 1.0:
                raise MoveException("understanding confidence below 1.0 not allowed for system moves")
        if speaker == USR:
            if understanding_confidence is None:
                raise MoveException("understanding confidence must be supplied for user moves")
            if ddd_name is None:
                raise MoveException("ddd_name must be supplied")
        if modality not in Modality.MODALITIES:
            raise MoveException(f"unsupported modality: '{modality}'")

    def __hash__(self):
        return hash((
            self.__class__.__name__, self._type, self.perception_confidence, self.understanding_confidence,
            self.weighted_understanding_confidence, self._speaker, self._utterance, self._ddd_name
        ))

    def __str__(self):
        return self._get_semantic_expression(include_attributes=True)

    def _get_semantic_expression(self, include_attributes):
        string = "Move("
        string += self._type
        if include_attributes:
            string += self._build_string_from_attributes()
        string += ")"
        return string

    def _build_string_from_attributes(self):
        string = ""
        if self._ddd_name:
            string += f", ddd_name={self._ddd_name!r}"
        if self._speaker:
            string += f", speaker={self._speaker}"
        string += self._confidence_estimates.build_string_from_attributes()
        if self._modality:
            string += f", modality={self._modality}"
        if self._utterance:
            string += f", utterance={self._utterance!r}"
        return string

    def semantic_expression_without_realization_data(self):
        return self._get_semantic_expression(include_attributes=False)

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
            return (self.type_ == other.type_ and self.class_internal_move_content_equals(other))
        except AttributeError:
            return False

    def __ne__(self, other):
        return not (self == other)

    def is_icm(self):
        return False

    def is_question_raising(self):
        return False

    def is_yes_no_answer(self):
        return self.type_ == Move.ANSWER and (self.content.is_yes() or self.content.is_no())

    def is_turn_yielding(self):
        return self.is_question_raising()

    def to_rich_string(self):
        return f"{str(self)}:{self._speaker}:{self.understanding_confidence}"

    def uprank(self, amount):
        self._confidence_estimates.uprank(amount)

    def downrank(self, amount):
        self._confidence_estimates.downrank(amount)

    def set_background(self, background):
        self._background = background

    def as_dict(self):
        return {
            "ddd": self._ddd_name,
            "speaker": self._speaker,
            "modality": self._modality,
            "utterance": self._utterance,
            "understanding_confidence": self.understanding_confidence,
            "perception_confidence": self.perception_confidence,
            "move_type": self._type
        }

    def as_semantic_expression(self):
        return self._type


class MoveWithSemanticContent(Move, SemanticObjectWithContent):
    def __init__(self, type, content, *args, **kwargs):
        Move.__init__(self, type, *args, **kwargs)
        SemanticObjectWithContent.__init__(self, content)
        self._content = content

    @property
    def content(self):
        return self._content

    def __eq__(self, other):
        try:
            if super().__eq__(other):
                return self.content == other.content
        except AttributeError:
            pass
        return False

    def __hash__(self):
        return hash((
            self.__class__.__name__, self._type, self.perception_confidence, self.understanding_confidence,
            self.weighted_understanding_confidence, self._speaker, self._utterance, self._ddd_name
        ))

    def _get_semantic_expression(self, include_attributes):
        string = "Move("
        string += f"{self._type}({str(self._content)}"
        if self._background:
            string += f", {unicodify(self._background)}"
        string += ")"
        if include_attributes:
            string += self._build_string_from_attributes()
        string += ")"
        return string

    def as_dict(self):
        result = {
            "content": self.content.as_dict() if self.content else None,
        }
        return super().as_dict() | result

    def class_internal_move_content_equals(self, other):
        return self._content == other._content


class ICM(Move):
    RERAISE = "reraise"
    PER = "per"
    ACC = "acc"
    SEM = "sem"
    UND = "und"
    ACCOMMODATE = "accommodate"
    LOADPLAN = "loadplan"
    RESUME = "resume"
    REPORT_INFERENCE = "report_inference"
    CARDINAL_SEQUENCING = "cardinal_sequencing"

    INT = "int"
    POS = "pos"
    NEG = "neg"

    def __init__(
        self,
        type_,
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
            type_,
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            ddd_name=ddd_name,
            perception_confidence=perception_confidence
        )

    def __eq__(self, other):
        try:
            if super().__eq__(other):
                return self.class_internal_move_content_equals(other)
        except AttributeError:
            pass
        return False

    def class_internal_move_content_equals(self, other):
        return (self._polarity == other._polarity and self._type == other._type)

    @property
    def polarity(self):
        return self._polarity

    def get_polarity(self):
        return self.polarity

    def is_icm(self):
        return True

    def is_issue_icm(self):
        return False

    def is_question_raising(self):
        return False

    @property
    def content(self):
        return None

    def is_negative_perception_icm(self):
        if self.type_ == ICMMove.PER:
            return self.get_polarity() == ICMMove.NEG
        else:
            return False

    def is_positive_acceptance_icm(self):
        if self.type_ == ICMMove.ACC:
            return self.get_polarity() == ICMMove.POS
        else:
            return False

    def is_negative_acceptance_issue_icm(self):
        return False

    def is_negative_acceptance_icm(self):
        if (self.type_ == ICMMove.ACC and self.get_polarity() == ICMMove.NEG):
            return True
        else:
            return False

    def is_negative_understanding_icm(self):
        return (self.type_ == ICMMove.UND and self.get_polarity() == ICMMove.NEG)

    def is_positive_understanding_icm_with_non_neg_content(self):
        return False

    def is_interrogative_understanding_icm_with_non_neg_content(self):
        return False

    def is_grounding_proposition(self):
        return False

    def __str__(self):
        return self.get_semantic_expression(include_attributes=True)

    def get_semantic_expression(self, include_attributes=True):
        string = f"ICMMove({self._icm_to_string()}"
        if include_attributes:
            if self._speaker:
                string += f", speaker={self._speaker}"
            if self.understanding_confidence is not None:
                string += f", understanding_confidence={self.understanding_confidence}"
            if self.perception_confidence is not None:
                string += f", perception_confidence={self.perception_confidence}"
        string += ")"
        return string

    def semantic_expression_without_realization_data(self):
        return self.get_semantic_expression(include_attributes=False)

    def _icm_to_string(self):
        if self._type in [ICMMove.PER, ICMMove.ACC, ICMMove.UND, ICMMove.SEM]:
            return f"icm:{self._type}*{self._polarity}"
        return f"icm:{self._type}"

    def as_semantic_expression(self):
        return self._icm_to_string()

    def as_dict(self):
        result = {"polarity": self.get_polarity()}

        return super().as_dict() | result


class ICMMove(ICM):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class ICMAccPos(ICM):
    def __init__(self, *args, **kwargs):
        super().__init__(ICM.ACC, polarity=ICM.POS)


class IssueICM(ICM):
    def is_issue_icm(self):
        return True

    def is_negative_acceptance_issue_icm(self):
        if (self.type_ == ICM.ACC and self.get_polarity() == ICM.NEG):
            return True
        return False

    def _icm_to_string(self):
        return f"{ICM._icm_to_string(self)}:issue"


class IssueICMMove(IssueICM):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class ICMWithContent(ICM):
    def __init__(self, type_, content, content_speaker=None, *args, **kwargs):
        ICM.__init__(self, type_, *args, **kwargs)
        self._content = content
        self._content_speaker = self._get_checked_content_speaker(content_speaker)

    def __eq__(self, other):
        try:
            if super().__eq__(other):
                return self.content == other.content \
                    and self.get_content_speaker() == other.get_content_speaker()
        except AttributeError:
            pass
        return False

    @property
    def content(self):
        return self._content

    def _get_checked_content_speaker(self, speaker):
        if (speaker in [USR, SYS, MODEL, None]):
            return speaker
        raise Exception(f"'{speaker}' is not a valid value for content_speaker")

    def get_content_speaker(self):
        return self._content_speaker

    def _icm_to_string(self):
        if self._content_speaker is not None:
            return f"icm:{self._type}*{self._polarity}:{self._content_speaker}*{self._content}"

        if self._type == ICMMove.PER:
            return f'icm:{self._type}*{self._polarity}:"{self._content}"'
        if self._type in [ICMMove.ACC, ICMMove.UND, ICMMove.SEM]:
            return f"icm:{self._type}*{self._polarity}:{self._content}"
        return f"icm:{self._type}:{self._content}"

    def class_internal_move_content_equals(self, other):
        return (
            self._polarity == other._polarity and self.type_ == other.type_ and self.content == other.content
            and self._content_speaker == other._content_speaker
        )

    def is_question_raising(self):
        return (
            self.type_ == ICMMove.UND and self.content is not None
            and not (self.get_polarity() == ICMMove.POS and not self.content.is_positive())
        )

    def is_positive_understanding_icm_with_non_neg_content(self):
        return (self.type_ == ICMMove.UND and self.get_polarity() == ICMMove.POS and self.content.is_positive())

    def is_interrogative_understanding_icm_with_non_neg_content(self):
        return (self.type_ == ICMMove.UND and self.get_polarity() == ICMMove.INT and self.content.is_positive())

    def is_grounding_proposition(self):
        return self.type_ == ICMMove.UND and self.get_polarity() in [ICMMove.POS, ICMMove.INT]

    def as_dict(self):
        return super().as_dict() | {"content": self.content, "content_speaker": self.get_content_speaker()}


class ICMMoveWithContent(ICMWithContent):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class CardinalSequencingICM(ICMWithContent):
    def __init__(self, step):
        super().__init__(ICMMove.CARDINAL_SEQUENCING, step)

    def __eq__(self, other):
        try:
            return self.type_ == other.type_ and self._content == other._content
        except AttributeError:
            return False


class ICMWithStringContent(ICMWithContent):
    pass


class ICMMoveWithStringContent(ICMWithStringContent):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class ICMWithSemanticContent(ICMWithContent, MoveWithSemanticContent):
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
        ICMWithContent.__init__(
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


class ICMMoveWithSemanticContent(ICMWithSemanticContent):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class Report(MoveWithSemanticContent):
    def __init__(self, content, *args, **kwargs):
        MoveWithSemanticContent.__init__(self, Move.REPORT, content, *args, **kwargs)

    def as_semantic_expression(self):
        return f"report({self.content.as_semantic_expression()})"

    def is_turn_yielding(self):
        return True

    def _get_semantic_expression(self, include_attributes):
        string = f"report({unicodify(self.content)}"
        if self._background:
            string += f", {unicodify(self._background)}"
        if include_attributes:
            string += self._build_string_from_attributes()
        string += ")"
        return string

    def class_internal_move_content_equals(self, other):
        return self.content == other.content


class ReportMove(Report):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class Prereport(Move, OntologySpecificSemanticObject):
    def __init__(self, ontology_name, service_action, arguments):
        self.service_action = service_action
        self.arguments = arguments
        Move.__init__(self, Move.PREREPORT)
        OntologySpecificSemanticObject.__init__(self, ontology_name)

    def __eq__(self, other):
        try:
            if super().__eq__(other):
                return self.class_internal_move_content_equals(other)
        except AttributeError:
            pass
        return False

    def get_service_action(self):
        return self.service_action

    def get_arguments(self):
        return self.arguments

    def __str__(self):
        return self.get_semantic_expression(include_attributes=True)

    def get_semantic_expression(self, include_attributes=True):
        string = f"prereport({self.service_action}, {unicodify(self.arguments)}"
        if include_attributes:
            string += self._build_string_from_attributes()
        string += ")"
        return string

    def semantic_expression_without_realization_data(self):
        return self.get_semantic_expression(include_attributes=False)

    def as_semantic_expression(self):
        return str(self)

    def class_internal_move_content_equals(self, other):
        return (self.service_action == other.service_action and self.arguments == other.arguments)

    def as_dict(self):
        return super().as_dict() | {
            "arguments": self.arguments,
            "service_action": self.service_action,
            "ontology_name": self.ontology_name
        }


class PrereportMove(Prereport):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class NoMove(Move):
    def __init__(self, *args, **kwargs):
        super(NoMove, self).__init__(Move.NO_MOVE, *args, **kwargs)


class Greet(Move):
    def __init__(self, *args, **kwargs):
        super(Greet, self).__init__(Move.GREET, *args, **kwargs)

    def is_turn_yielding(self):
        return True


class GreetMove(Greet):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class ThankYou(Move):
    def __init__(self, *args, **kwargs):
        super(ThankYou, self).__init__(Move.THANK_YOU, *args, **kwargs)


class ThankYouMove(ThankYou):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class ThankYouResponse(Move):
    def __init__(self, *args, **kwargs):
        super(ThankYouResponse, self).__init__(Move.THANK_YOU_RESPONSE, *args, **kwargs)


class ThankYouResponseMove(ThankYouResponse):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class InsultResponse(Move):
    def __init__(self, *args, **kwargs):
        super(InsultResponse, self).__init__(Move.INSULT_RESPONSE, *args, **kwargs)


class InsultResponseMove(InsultResponse):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class Insult(Move):
    def __init__(self, *args, **kwargs):
        super(Insult, self).__init__(Move.INSULT, *args, **kwargs)


class InsultMove(Insult):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class Mute(Move):
    def __init__(self, *args, **kwargs):
        super(Mute, self).__init__(Move.MUTE, *args, **kwargs)


class MuteMove(Mute):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class Unmute(Move):
    def __init__(self, *args, **kwargs):
        super(Unmute, self).__init__(Move.UNMUTE, *args, **kwargs)


class UnmuteMove(Unmute):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class Quit(Move):
    def __init__(self, *args, **kwargs):
        super(Quit, self).__init__(Move.QUIT, *args, **kwargs)


class QuitMove(Quit):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class Ask(MoveWithSemanticContent):
    def __init__(self, question, *args, **kwargs):
        MoveWithSemanticContent.__init__(self, Move.ASK, question, *args, **kwargs)

    def as_semantic_expression(self):
        return f"ask({self.question.as_semantic_expression()})"

    @property
    def question(self):
        return self.content

    def is_question_raising(self):
        return True


class AskMove(Ask):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class Answer(MoveWithSemanticContent):
    def __init__(self, answer, *args, **kwargs):
        MoveWithSemanticContent.__init__(self, Move.ANSWER, answer, *args, **kwargs)

    def as_semantic_expression(self):
        return f"answer({self._content.as_semantic_expression()})"

    @property
    def answer_content(self):
        return self.content


class AnswerMove(Answer):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class Request(MoveWithSemanticContent):
    def __init__(self, action, *args, **kwargs):
        MoveWithSemanticContent.__init__(self, Move.REQUEST, action, *args, **kwargs)

    def as_semantic_expression(self):
        return f"request({self.action.as_semantic_expression()})"

    @property
    def action(self):
        return self.content

    def is_turn_yielding(self):
        return True


class RequestMove(Request):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            f'{self.__class__.__name__} is deprecated in tala 26.3. Use class name removing  "Move"',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
