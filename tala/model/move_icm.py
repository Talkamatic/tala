from tala.model.speaker import USR, SYS, MODEL
from tala.model.move_base import Move


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
            polarity = ICM.POS
        self._polarity = polarity
        Move.__init__(
            self,
            type_,
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            ddd_name=ddd_name,
            perception_confidence=perception_confidence
        )

    @classmethod
    def create(
        cls,
        type_,
        content=None,
        content_speaker=None,
        polarity=None,
        understanding_confidence=None,
        speaker=None,
        ddd_name=None,
        perception_confidence=None
    ):
        if content is None:
            return cls(
                type_,
                understanding_confidence=understanding_confidence,
                speaker=speaker,
                polarity=polarity,
                ddd_name=ddd_name,
                perception_confidence=perception_confidence
            )
        if content == "issue":
            return IssueICM(
                type_,
                understanding_confidence=understanding_confidence,
                speaker=speaker,
                polarity=polarity,
                ddd_name=ddd_name,
                perception_confidence=perception_confidence
            )
        return ICMWithContent(
            type_,
            content,
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            content_speaker=content_speaker,
            polarity=polarity,
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
        if self.type_ == ICM.PER:
            return self.polarity == ICM.NEG
        else:
            return False

    def is_positive_acceptance_icm(self):
        if self.type_ == ICM.ACC:
            return self.polarity == ICM.POS
        else:
            return False

    def is_negative_acceptance_issue_icm(self):
        return False

    def is_negative_acceptance_icm(self):
        if (self.type_ == ICM.ACC and self.polarity == ICM.NEG):
            return True
        else:
            return False

    def is_negative_understanding_icm(self):
        return (self.type_ == ICM.UND and self.polarity == ICM.NEG)

    def is_positive_understanding_icm_with_non_neg_content(self):
        return False

    def is_interrogative_understanding_icm_with_non_neg_content(self):
        return False

    def is_grounding_proposition(self):
        return False

    def __str__(self):
        return self.get_semantic_expression(include_attributes=True)

    def get_semantic_expression(self, include_attributes=True):
        string = f"ICM({self._icm_to_string()}"
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
        if self._type in [ICM.PER, ICM.ACC, ICM.UND, ICM.SEM]:
            return f"icm:{self._type}*{self._polarity}"
        return f"icm:{self._type}"

    def as_semantic_expression(self):
        return self._icm_to_string()

    def as_dict(self):
        result = {"polarity": self.polarity}

        return super().as_dict() | result


class ICMAccPos(ICM):
    def __init__(self, *args, **kwargs):
        super().__init__(ICM.ACC, polarity=ICM.POS)


class IssueICM(ICM):
    def is_issue_icm(self):
        return True

    def is_negative_acceptance_issue_icm(self):
        if (self.type_ == ICM.ACC and self.polarity == ICM.NEG):
            return True
        return False

    def _icm_to_string(self):
        return f"{ICM._icm_to_string(self)}:issue"


class ICMWithContent(ICM):
    def __init__(self, type_, content, content_speaker=None, *args, **kwargs):
        ICM.__init__(self, type_, *args, **kwargs)
        self._content = content
        self._content_speaker = self._get_checked_content_speaker(content_speaker)

    def __eq__(self, other):
        try:
            if super().__eq__(other):
                return self.content == other.content \
                    and self.content_speaker == other.content_speaker
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

    @property
    def content_speaker(self):
        return self._content_speaker

    def has_semantic_content(self):
        try:
            return self._content.is_ontology_specific() or self._content.has_semantic_content()
        except AttributeError:
            return False

    @property
    def ontology_name(self):
        return self._content.ontology_name

    def is_ontology_specific(self):
        try:
            return self._content.is_ontology_specific()
        except AttributeError:
            return False

    def _icm_to_string(self):
        if self._content_speaker is not None:
            return f"icm:{self._type}*{self._polarity}:{self._content_speaker}*{self._content}"

        if self._type == ICM.PER:
            return f'icm:{self._type}*{self._polarity}:"{self._content}"'
        if self._type in [ICM.ACC, ICM.UND, ICM.SEM]:
            return f"icm:{self._type}*{self._polarity}:{self._content}"
        return f"icm:{self._type}:{self._content}"

    def class_internal_move_content_equals(self, other):
        return (
            self._polarity == other._polarity and self.type_ == other.type_ and self.content == other.content
            and self._content_speaker == other._content_speaker
        )

    def is_question_raising(self):
        return (
            self.type_ == ICM.UND and self.content is not None
            and not (self.polarity == ICM.POS and not self.content.is_positive())
        )

    def is_positive_understanding_icm_with_non_neg_content(self):
        return (self.type_ == ICM.UND and self.polarity == ICM.POS and self.content.is_positive())

    def is_interrogative_understanding_icm_with_non_neg_content(self):
        return (self.type_ == ICM.UND and self.polarity == ICM.INT and self.content.is_positive())

    def is_grounding_proposition(self):
        return self.type_ == ICM.UND and self.polarity in [ICM.POS, ICM.INT]

    def as_dict(self):
        return super().as_dict() | {"content": self.content, "content_speaker": self.content_speaker}


class CardinalSequencingICM(ICMWithContent):
    def __init__(self, step):
        super().__init__(ICM.CARDINAL_SEQUENCING, step)

    def __eq__(self, other):
        try:
            return self.type_ == other.type_ and self._content == other._content
        except AttributeError:
            return False
