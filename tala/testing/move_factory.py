from tala.model.speaker import USR
from tala.model.move import (
    MoveWithSemanticContent, Move, ICM, IssueICM, ICMWithStringContent, ICMWithSemanticContent, Report, Prereport,
    Answer, Request, Ask
)


class MoveFactoryWithPredefinedBoilerplate(object):
    def __init__(
        self,
        ontology_name,
        understanding_confidence=None,
        speaker=None,
        utterance=None,
        ddd_name=None,
        perception_confidence=None
    ):
        self._ontology_name = ontology_name
        self._understanding_confidence = understanding_confidence
        self._perception_confidence = perception_confidence
        self._speaker = speaker
        self._utterance = utterance
        self._ddd_name = ddd_name

    def create_move(
        self,
        type_,
        content=None,
        understanding_confidence=None,
        speaker=None,
        utterance=None,
        modality=None,
        ddd_name=None,
        perception_confidence=None
    ):
        if understanding_confidence is None:
            understanding_confidence = self._understanding_confidence
        if perception_confidence is None:
            perception_confidence = self._perception_confidence
        if speaker is None:
            speaker = self._speaker
        if utterance is None:
            utterance = self._utterance
        if ddd_name is None:
            ddd_name = self._ddd_name

        kwargs = {
            "understanding_confidence": understanding_confidence,
            "speaker": speaker,
            "utterance": utterance,
            "modality": modality,
            "ddd_name": ddd_name,
            "perception_confidence": perception_confidence
        }

        if content is not None:
            classes = {
                Move.ANSWER: Answer,
                Move.REQUEST: Request,
                Move.ASK: Ask,
            }
            if type_ in classes:
                Class = classes[type_]
                return Class(content, **kwargs)
            return MoveWithSemanticContent(type_, content, **kwargs)

        return Move(type_, **kwargs)

    def create_ask_move(self, question, speaker=None):
        return self.create_move(Move.ASK, question, speaker=speaker)

    def create_answer_move(self, answer, speaker=None):
        return self.create_move(Move.ANSWER, answer, speaker=speaker)

    def create_request_move(self, action):
        return self.create_move(Move.REQUEST, action, speaker=USR, understanding_confidence=1.0)

    def create_icm_move(
        self,
        icm_type,
        content=None,
        content_speaker=None,
        polarity=None,
        understanding_confidence=None,
        speaker=None,
        ddd_name=None,
        perception_confidence=None
    ):
        if understanding_confidence is None:
            understanding_confidence = self._understanding_confidence
        if speaker is None:
            speaker = self._speaker

        if content is not None:
            if content == "issue":
                return IssueICM(
                    icm_type,
                    understanding_confidence=understanding_confidence,
                    speaker=speaker,
                    polarity=polarity,
                    ddd_name=ddd_name,
                    perception_confidence=perception_confidence
                )
            if isinstance(content, str):
                return ICMWithStringContent(
                    icm_type,
                    content,
                    understanding_confidence=understanding_confidence,
                    speaker=speaker,
                    content_speaker=content_speaker,
                    polarity=polarity,
                    ddd_name=ddd_name,
                    perception_confidence=perception_confidence
                )
            return ICMWithSemanticContent(
                icm_type,
                content,
                understanding_confidence=understanding_confidence,
                speaker=speaker,
                content_speaker=content_speaker,
                polarity=polarity,
                ddd_name=ddd_name,
                perception_confidence=perception_confidence
            )
        return ICM(
            icm_type,
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            polarity=polarity,
            ddd_name=ddd_name,
            perception_confidence=perception_confidence
        )

    def create_report_move(self, report_proposition):
        return Report(report_proposition)

    def create_prereport_move(self, service_action, arguments):
        return Prereport(self._ontology_name, service_action, arguments)
