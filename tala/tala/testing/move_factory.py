from tala.model.speaker import Speaker
from tala.model.move import MoveWithSemanticContent, Move, ICMMove, IssueICMMove, ICMMoveWithStringContent, \
    ICMMoveWithSemanticContent, ReportMove, PrereportMove, AnswerMove, RequestMove, AskMove


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

    def createMove(
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
                Move.ANSWER: AnswerMove,
                Move.REQUEST: RequestMove,
                Move.ASK: AskMove,
            }
            if type_ in classes:
                Class = classes[type_]
                return Class(content, **kwargs)
            return MoveWithSemanticContent(type_, content, **kwargs)

        return Move(type_, **kwargs)

    def create_ask_move(self, question, speaker=None):
        return self.createMove(Move.ASK, question, speaker=speaker)

    def createAnswerMove(self, answer, speaker=None):
        return self.createMove(Move.ANSWER, answer, speaker=speaker)

    def createRequestMove(self, action):
        return self.createMove(Move.REQUEST, action, speaker=Speaker.USR, understanding_confidence=1.0)

    def createIcmMove(
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
                return IssueICMMove(
                    icm_type,
                    understanding_confidence=understanding_confidence,
                    speaker=speaker,
                    polarity=polarity,
                    ddd_name=ddd_name,
                    perception_confidence=perception_confidence
                )
            if isinstance(content, str):
                return ICMMoveWithStringContent(
                    icm_type,
                    content,
                    understanding_confidence=understanding_confidence,
                    speaker=speaker,
                    content_speaker=content_speaker,
                    polarity=polarity,
                    ddd_name=ddd_name,
                    perception_confidence=perception_confidence
                )
            return ICMMoveWithSemanticContent(
                icm_type,
                content,
                understanding_confidence=understanding_confidence,
                speaker=speaker,
                content_speaker=content_speaker,
                polarity=polarity,
                ddd_name=ddd_name,
                perception_confidence=perception_confidence
            )
        return ICMMove(
            icm_type,
            understanding_confidence=understanding_confidence,
            speaker=speaker,
            polarity=polarity,
            ddd_name=ddd_name,
            perception_confidence=perception_confidence
        )

    def create_report_move(self, report_proposition):
        return ReportMove(report_proposition)

    def create_prereport_move(self, service_action, arguments):
        return PrereportMove(self._ontology_name, service_action, arguments)
