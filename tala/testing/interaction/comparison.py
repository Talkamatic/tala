import re
import json


def content_matches_pattern(actual, expected):
    pattern_content = re.escape(expected).replace(r'\*', '.*')
    re_pattern = f"^{pattern_content}$"
    return re.search(re_pattern, actual, re.MULTILINE | re.DOTALL)


class StringComparison:
    def __init__(self, actual, expected):
        self._actual = actual
        self._expected = expected

    def match(self):
        self._match = self._content_matches_pattern(self._actual, self._expected)
        return self._match

    def _content_matches_pattern(self, actual, expected):
        try:
            return content_matches_pattern(actual, expected)
        except TypeError:
            pass
        for expected_alt in expected:
            match = content_matches_pattern(actual, expected_alt)
            if match:
                self._match = match
                break
        self._expected = expected_alt
        return match

    def mismatch_description(self):
        return f"""
expected: "{self._expected}"
           {self._mismatch_position_description_for_pattern()}
but got:  "{self._actual}"
           {self._mismatch_position_description_for_actual()}"""

    def _mismatch_position_description_for_pattern(self):
        position = self._get_mismatch_position()
        return " " * position + "^"

    def _get_mismatch_position(self):
        length = len(self._expected) - 1
        while length > 0:
            if self._content_matches_pattern(self._actual, self._expected[0:length] + "*"):
                return length
            length = length - 1
        return 0

    def _mismatch_position_description_for_actual(self):
        position = self._get_mismatch_position()
        return " " * position + "^"


class MoveComparison:
    def __init__(self, actual, expected):
        self._actual = actual
        self._expected = expected
        self._match = self._content_matches_pattern(actual, expected)

    def match(self):
        return self._match

    def mismatch_description(self):
        return f"""
expected: {json.dumps(self._expected)}
          {self._mismatch_position_description(self._expected, self._actual)}
but got:  {json.dumps(self._actual)}
          {self._mismatch_position_description(self._actual, self._expected)}"""

    def _content_matches_pattern(self, actual, expected):
        if len(actual) == len(expected):
            for actual_move, expected_move in zip(actual, expected):
                if not self._move_matches_expectation(actual_move, expected_move):
                    return False
            return True
        return False

    def _move_matches_expectation(self, actual_move, expected_move):
        return content_matches_pattern(actual_move, expected_move)

    def _mismatch_position_description(self, target, pattern):
        list_position = self._get_mismatch_list_position(target, pattern)
        string_position = self._get_mismatch_string_position(target, list_position)
        length = self._get_mismatch_length(target, list_position)
        if string_position > 0:
            return " " * string_position + "^" * length
        else:
            return "^" * length

    def _get_mismatch_list_position(self, one_list, other_list):
        if len(one_list) == len(other_list):
            return self._get_mismatch_list_position_for_equal_length_move_lists(one_list, other_list)
        else:
            return self._get_mismatch_list_position_for_one_move_list_longer(one_list, other_list)

    def _get_mismatch_list_position_for_equal_length_move_lists(self, one_list, other_list):
        index = 0
        for one, other in zip(one_list, other_list):
            if not one == other:
                return index
            index += 1

    def _get_mismatch_list_position_for_one_move_list_longer(self, one_list, other_list):
        shortest_list_length = min(len(one_list), len(other_list))
        for index in range(0, shortest_list_length):
            if not one_list[index] == other_list[index]:
                return index
        return shortest_list_length

    def _get_mismatch_string_position(self, target_list, list_position):
        if list_position > len(target_list):
            return len(str(target_list))
        position = 1
        for index in range(0, list_position):
            position += len(target_list[index]) + 4
        return position

    def _get_mismatch_length(self, target, position):
        if position >= len(target):
            return 1
        else:
            return len(target[position]) + 2
