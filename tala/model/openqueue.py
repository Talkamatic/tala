import copy

from tala.utils.as_json import AsJSONMixin
from tala.utils.as_semantic_expression import AsSemanticExpressionMixin
from tala.utils.unicodify import unicodify
from tala.utils.equality import EqualityMixin


class OpenQueueError(Exception):
    pass


class Interpretation(AsJSONMixin, EqualityMixin):
    def __init__(self, moves, utterance, default_perception_confidence):
        self._moves = moves
        self._utterance = utterance
        self._default_perception_confidence = default_perception_confidence

    def as_dict(self):
        return self._moves.as_dict()

    def enqueue(self, element):
        self._moves.enqueue(element)

    def enqueue_first(self, element):
        self._moves.enqueue_first(element)

    def first(self, element):
        self._moves.first(element)

    def is_first(self, element):
        self._moves.is_first(element)

    def last(self, element):
        self._moves.last(element)

    def dequeue(self):
        self._moves.dequeue()

    def remove(self, element):
        self._moves.remove(element)

    def remove_if_exists(self, element):
        self._moves.remove_if_exists(element)

    def clear(self):
        self._moves.clear()

    def shift(self):
        self._moves.shift()

    def init_shift(self):
        self._moves.init_shift()

    def cancel_shift(self):
        self._moves.cancel_shift()

    def fully_shifted(self):
        self._moves.fully_shifted()

    def is_shift_initialised(self):
        self._moves.is_shifted_initiated()

    def __len__(self):
        return len(self._moves)

    def __iter__(self):
        return iter(self._moves)

    def __getitem__(self, index):
        return self._moves[index]

    def __str__(self):
        string = f'Interpretation({unicodify(self._moves)}, {unicodify(self.average_perception_confidence)})'
        return string

    def __repr__(self):
        string = f'Interpretation({self._moves}, {self.average_perception_confidence})'
        return string

    @property
    def utterance(self):
        return self._utterance

    @property
    def average_weighted_confidence(self):
        return sum([move.weighted_confidence for move in self._moves]) / len(self._moves)

    @property
    def average_perception_confidence(self):
        if self._moves:
            return sum([move.perception_confidence for move in self._moves]) / len(self._moves)
        return self._default_perception_confidence

    @property
    def average_confidence(self):
        return sum([move.confidence for move in self._moves]) / len(self._moves)


class OpenQueue(AsJSONMixin, AsSemanticExpressionMixin):
    def __init__(self, front_content=None, back_content=None, unshifted_content=None):
        if front_content is None:
            front_content = []
        if back_content is None:
            back_content = []
        super(OpenQueue, self).__init__()
        self.front_content = []
        self.back_content = []
        for item in front_content:
            self.front_content.append(item)
        for item in back_content:
            self.back_content.append(item)
        self._unshifted_content = unshifted_content

    def as_dict(self):
        return {
            "openqueue": {
                "front_content": self.front_content if self.front_content else [],
                "back_content": self.back_content if self.back_content else [],
                "unshifted_content": self._unshifted_content if self._unshifted_content else []
            }
        }

    def enqueue(self, element):
        if element not in self:
            self.back_content.append(element)

    def enqueue_first(self, element):
        if element not in self:
            self.front_content[0:0] = [element]

    def first(self):
        if self.is_empty():
            raise OpenQueueError("tried to get first item from empty queue")
        if len(self.front_content) > 0:
            return self.front_content[0]
        else:
            return self.back_content[0]

    def is_first(self, element):
        if self.is_empty():
            return False
        return self.first() == element

    def last(self):
        if len(self.back_content) > 0:
            return self.back_content[-1]
        else:
            return self.front_content[-1]

    def __len__(self):
        return len(self.front_content) + len(self.back_content)

    def dequeue(self):
        if self.is_empty():
            raise OpenQueueError("tried to dequeue empty queue")
        current_list = self.front_content
        if len(self.front_content) < 1:
            current_list = self.back_content
        dequeued = current_list[0]
        del current_list[0]
        return dequeued

    def remove(self, element):
        if element in self.front_content:
            self.front_content.remove(element)
        else:
            self.back_content.remove(element)

    def remove_if_exists(self, element):
        if element in self:
            self.remove(element)

    def clear(self):
        self.front_content = []
        self.back_content = []

    def is_empty(self):
        return len(self) == 0

    def shift(self):
        self.back_content.append(self.front_content[0])
        del self.front_content[0]

    def init_shift(self):
        self.front_content.extend(self.back_content)
        self.back_content = []
        self._unshifted_content = copy.copy(self.front_content)

    def cancel_shift(self):
        if self._unshifted_content is None:
            raise OpenQueueError("tried to cancel_shift queue without init_shift")
        result = []
        for element in self._unshifted_content:
            if element in self:
                result.append(element)
        self.front_content = result
        self.back_content = []

    def fully_shifted(self):
        return self.front_content == []

    def is_shift_initialised(self):
        return self.back_content == []

    def __iter__(self):
        tmp_list = []
        tmp_list.extend(self.front_content)
        tmp_list.extend(self.back_content)
        return tmp_list.__iter__()

    def __str__(self):
        tmp_list = self._create_concatenated_list_of_contents_with_delimiter()
        string = "OpenQueue(%s)" % unicodify(tmp_list)
        return string

    def _create_concatenated_list_of_contents_with_delimiter(self):
        tmp_list = []
        tmp_list.extend(self.front_content)
        tmp_list.append('#')
        tmp_list.extend(self.back_content)
        return tmp_list

    def __repr__(self):
        tmp_list = self._create_concatenated_list_of_contents_with_delimiter()
        string = "OpenQueue(%s)" % tmp_list
        return string

    def __eq__(self, other):
        try:
            if len(self) != len(other):
                return False

            if self.is_empty() and other.is_empty():
                return True

            if len(self) == 1 and len(other) == 1:
                return self._check_single_element_equality(other)

            return self.front_content == other.front_content and self.back_content == other.back_content

        except (AttributeError, TypeError):
            return False

    def _check_single_element_equality(self, other):
        return self.first() == other.first()

    def __hash__(self):
        return hash(self.front_content) + 17 * hash(self.back_content)

    def __ne__(self, other):
        return not (self == other)

    def __getitem__(self, index):
        return list(self)[index]
