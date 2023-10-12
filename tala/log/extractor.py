import json

REQUEST_EVENT = "incoming request on frontend HTTP API"
RESPONSE_EVENT = "outgoing response on frontend HTTP API"
SELECTED_INTERPRETATION_EVENT = "DmeModule selected interpretation to act on"

BACKEND_VERSION_PREFIX = "Backend uses TDM version "
BACKEND_DIRECTORY_PREFIX = "Backend started in directory "
BACKEND_CONFIG_PREFIX = "Backend uses backend config "
BACKEND_LANGUAGE_PREFIX = "Backend uses language "


class UnexpectedPrefixException(Exception):
    pass


class LogExtractor:
    def __init__(self, logfile):
        self._logfile = logfile

    @property
    def _entries(self):
        with open(self._logfile) as file_:
            for line in file_:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue

    def get_backend_communication_entries(self):
        for entry in self._entries:
            message = entry["event"]
            if message in [REQUEST_EVENT, RESPONSE_EVENT, SELECTED_INTERPRETATION_EVENT]:
                yield entry

    def get_backend_tdm_version(self):
        return self._get_first_suffix([BACKEND_VERSION_PREFIX])

    def get_backend_working_directory(self):
        return self._get_first_suffix([BACKEND_DIRECTORY_PREFIX])

    def get_backend_config(self):
        return self._get_first_suffix([BACKEND_CONFIG_PREFIX])

    def get_backend_language(self):
        return self._get_first_suffix([BACKEND_LANGUAGE_PREFIX])

    def _get_first_suffix(self, prefixes):
        suffixes = self._get_suffixes(prefixes)
        if suffixes:
            return suffixes[0]

    def _get_suffixes(self, prefixes):
        entries = self._entries_that_match(prefixes)
        suffixes = [self._extract_suffix_from_message(entry["event"], prefixes) for entry in entries]
        return suffixes

    def _entries_that_match(self, prefixes):
        def is_match(entry):
            return any([prefix in entry["event"] for prefix in prefixes])

        return [entry for entry in self._entries if is_match(entry)]

    def _extract_suffix_from_message(self, message, prefixes):
        start_of_prefix, prefix = self._find_start_of_a_prefix(message, prefixes)
        start_of_entry = start_of_prefix + len(prefix)
        suffix = message[start_of_entry:]
        return suffix

    def _find_start_of_a_prefix(self, message, prefixes):
        for prefix in prefixes:
            if prefix in message:
                start_of_entry = message.find(prefix)
                return start_of_entry, prefix
        raise UnexpectedPrefixException("Expected to find one of %s in %s but didn't" % (prefixes, message))

    @staticmethod
    def string_without_prefix(string, prefix):
        length_of_bytearray_prefix = len("b")
        start_of_content = len(prefix) + length_of_bytearray_prefix
        return string[start_of_content:]
