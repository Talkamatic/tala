from tala.log.extractor import LogExtractor, REQUEST_EVENT, RESPONSE_EVENT, SELECTED_INTERPRETATION_EVENT
from tala.testing.interactions.compiler import InteractionTestCompiler


class FailedException(Exception):
    pass


class UnexpectedInputException(Exception):
    pass


class InteractionTestExtractor:
    def __init__(self, log_file, print_mixin, verbose=False):
        self._log_file = log_file
        self._print_mixin = print_mixin
        self._verbose = verbose
        self._log_extractor = LogExtractor(self._log_file)

    @staticmethod
    def from_args(log, verbose=False, full=False, semantic=False):
        def create_mixin():
            if full:
                if semantic:
                    return FullSemanticMixin()
                return FullNaturalLanguageMixin()
            if semantic:
                return ReadableSemanticMixin()
            return ReadableNaturalLanguageMixin()

        args = (log, create_mixin(), verbose)
        return InteractionTestExtractor(*args)

    def run(self):
        if self._verbose:
            self._print_header()
        entries = list(self._log_extractor.get_backend_communication_entries())
        for index, entry in enumerate(entries):
            self._print_mixin.handle_entry(entries, entry, index)

    def _print_header(self):
        self._print_tdm_version()
        self._print_language()
        self._print_working_dir()
        self._print_config()
        print()

    def _print_tdm_version(self):
        logged_version = self._log_extractor.get_backend_tdm_version()
        self._print_header_entry("Originally run by TDM", logged_version)

    def _print_working_dir(self):
        logged_dir = self._log_extractor.get_backend_working_directory()
        self._print_header_entry("with working directory", logged_dir)

    def _print_language(self):
        logged_language = self._log_extractor.get_backend_language()
        self._print_header_entry("in language", logged_language)

    def _print_config(self):
        logged_backend_config = self._log_extractor.get_backend_config()
        self._print_header_entry("using backend config", logged_backend_config)

    def _print_header_entry(self, name, logged_value):
        if logged_value is None:
            logged_value = "Unknown"

        print(f"# {name} {logged_value}")


class PrintMixin:
    @classmethod
    def handle_entry(cls, entries, entry, index):
        raise NotImplementedError()


class FullSemanticMixin(PrintMixin):
    @classmethod
    def handle_entry(cls, entries, entry, index):
        if entry["event"] == REQUEST_EVENT:
            request = entry["frontend_request"]["request"]
            if "semantic_input" in request:
                print(InteractionTestCompiler.pretty_semantic_input(request["semantic_input"]))
            elif "natural_language_input" in request:
                FullNaturalLanguageMixin.handle_entry(entries, entry, index)
            elif "passivity" in request:
                print(InteractionTestCompiler.pretty_passivity())
            elif "event" in request:
                print(InteractionTestCompiler.pretty_event(request["event"]))
        if entry["event"] == RESPONSE_EVENT:
            if "output" in entry["frontend_response"]:
                moves = entry["frontend_response"]["output"]["moves"]
                print(InteractionTestCompiler.pretty_system_moves(moves))
        if entry["event"] == SELECTED_INTERPRETATION_EVENT:
            pass


class ReadableSemanticMixin(FullSemanticMixin):
    @classmethod
    def handle_entry(cls, entries, entry, index):
        def is_next_entry_more_informed():
            next_index = index + 1
            if len(entries) <= next_index:
                return False
            next_entry = entries[next_index]
            if next_entry["event"] == SELECTED_INTERPRETATION_EVENT:
                return next_entry["selected_interpretation"] is not None
            return False

        def average(elements):
            if not elements:
                return 0.0
            return sum(elements) / len(elements)

        def interpretation_confidence(interpretation):
            moves = interpretation["moves"]
            return average([move["perception_confidence"] * move["understanding_confidence"] for move in moves])

        if entry["event"] == REQUEST_EVENT:
            if is_next_entry_more_informed():
                return
            request = entry["frontend_request"]["request"]
            if "semantic_input" in request:
                interpretations = request["semantic_input"]["interpretations"]
                best_interpretation = max(interpretations, key=interpretation_confidence)
                semantic_expressions = [move["semantic_expression"] for move in best_interpretation["moves"]]
                print(InteractionTestCompiler.pretty_semantic_expressions(semantic_expressions))
            elif "natural_language_input" in request:
                ReadableNaturalLanguageMixin.handle_entry(entries, entry, index)
            elif "passivity" in request:
                print(InteractionTestCompiler.pretty_passivity())
            elif "event" in request:
                print(InteractionTestCompiler.pretty_event(request["event"]))
        if entry["event"] == RESPONSE_EVENT:
            if "output" in entry["frontend_response"]:
                moves = entry["frontend_response"]["output"]["moves"]
                print(InteractionTestCompiler.pretty_system_moves(moves))
        if entry["event"] == SELECTED_INTERPRETATION_EVENT:
            interpretation = entry["selected_interpretation"]
            if interpretation is not None:
                moves = interpretation["openqueue"]
                semantic_expressions = [move["semantic_expression"] for move in moves]
                print(InteractionTestCompiler.pretty_semantic_expressions(semantic_expressions))


class FullNaturalLanguageMixin(PrintMixin):
    @classmethod
    def handle_entry(cls, entries, entry, index):
        if entry["event"] == REQUEST_EVENT:
            request = entry["frontend_request"]["request"]
            if "natural_language_input" in request:
                hypotheses = request["natural_language_input"]["hypotheses"]
                interactiontesting_hypotheses = [(hypothesis["utterance"], hypothesis["confidence"])
                                                 for hypothesis in hypotheses]
                print(InteractionTestCompiler.pretty_hypotheses(interactiontesting_hypotheses))
            elif "semantic_input" in request:
                print(InteractionTestCompiler.pretty_semantic_input(request["semantic_input"]))
            elif "passivity" in request:
                print(InteractionTestCompiler.pretty_passivity())
            elif "event" in request:
                print(InteractionTestCompiler.pretty_event(request["event"]))
        if entry["event"] == RESPONSE_EVENT:
            if "output" in entry["frontend_response"]:
                utterance = entry["frontend_response"]["output"]["utterance"]
                print(InteractionTestCompiler.pretty_system_utterance(utterance))
        if entry["event"] == SELECTED_INTERPRETATION_EVENT:
            pass


class ReadableNaturalLanguageMixin(FullNaturalLanguageMixin):
    @classmethod
    def handle_entry(cls, entries, entry, index):
        def is_next_entry_more_informed():
            next_index = index + 1
            if len(entries) <= next_index:
                return False
            next_entry = entries[next_index]
            if next_entry["event"] == SELECTED_INTERPRETATION_EVENT:
                return next_entry["selected_hypothesis"] is not None
            return False

        if entry["event"] == REQUEST_EVENT:
            if is_next_entry_more_informed():
                return
            request = entry["frontend_request"]["request"]
            if "natural_language_input" in request:
                hypotheses = request["natural_language_input"]["hypotheses"]
                best_hypothesis = max(hypotheses, key=lambda hypothesis: hypothesis["confidence"])
                print(
                    InteractionTestCompiler.pretty_hypotheses([
                        (best_hypothesis["utterance"], best_hypothesis["confidence"])
                    ])
                )
            elif "semantic_input" in request:
                print(InteractionTestCompiler.pretty_semantic_input(request["semantic_input"]))
            elif "passivity" in request:
                print(InteractionTestCompiler.pretty_passivity())
            elif "event" in request:
                print(InteractionTestCompiler.pretty_event(request["event"]))
        if entry["event"] == RESPONSE_EVENT:
            if "output" in entry["frontend_response"]:
                utterance = entry["frontend_response"]["output"]["utterance"]
                print(InteractionTestCompiler.pretty_system_utterance(utterance))
        if entry["event"] == SELECTED_INTERPRETATION_EVENT:
            hypothesis = entry["selected_hypothesis"]
            interpretation = entry["selected_interpretation"]
            if hypothesis is not None and hypothesis["utterance"] is not None:
                hypotheses = [(hypothesis["utterance"], hypothesis["confidence"])]
                print(InteractionTestCompiler.pretty_hypotheses(hypotheses))
            elif interpretation is not None:
                ReadableSemanticMixin.handle_entry(entries, entry, index)
