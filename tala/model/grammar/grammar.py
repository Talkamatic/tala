import warnings

from tala.model.grammar.intent import Question, Request, Answer
from tala.model.grammar.required_entity import RequiredPropositionalEntity, RequiredSortalEntity
from tala.model.sort import STRING
from tala.nl.gf import rgl_grammar_entry_types
from tala.nl.gf.grammar_entry_types import Constants
from tala.nl import selection_policy_names
from tala.utils.as_json import AsJSONMixin


class NoIndividualsFoundException(Exception):
    pass


class NoRequestsFoundException(Exception):
    pass


class NoQuestionsFoundException(Exception):
    pass


class UnexpectedIndividualsFoundException(Exception):
    pass


class UnexpectedRequestsFoundException(Exception):
    pass


class UnexpectedQuestionsFoundException(Exception):
    pass


class UnexpectedAnswersFoundException(Exception):
    pass


class UnexpectedAnswerFormatException(Exception):
    pass


class UnexpectedStringsFoundException(Exception):
    pass


class GrammarBase(AsJSONMixin):
    def __init__(self, grammar_root, grammar_path):
        super(GrammarBase, self).__init__()
        self._grammar_root = grammar_root
        self._grammar_path = grammar_path
        self._local_individual_identifier = None

    def as_dict(self):
        return {
            "answers": self.answers(),
        }

    def requests_of_action(self, action):
        raise NotImplementedError("%s.requests_of_action(...) need to be implemented." % self.__class__.__name__)

    def _find_individuals_of(self, name):
        raise NotImplementedError("%s._find_individual(...) need to be implemented." % self.__class__.__name__)

    def entries_of_individual(self, name):
        individuals = self._find_individuals_of(name)
        if len(individuals) < 1:
            all_names = [individual.get("name") for individual in self._grammar_root.findall(Constants.INDIVIDUAL)]
            raise NoIndividualsFoundException(
                "Expected at least one <%s ...> for individual '%s', but it was "
                "not found among %s in %s" % (Constants.INDIVIDUAL, name, all_names, self._grammar_path)
            )
        if len(individuals) > 1:
            raise UnexpectedIndividualsFoundException(
                "Expected a single <%s ...> for individual '%s' but found %d in %s" %
                (Constants.INDIVIDUAL, name, len(individuals), self._grammar_path)
            )
        return self._process_individual_entries(individuals[0])

    def _process_individual_entries(self, individual_element):
        if self._element_has_children(individual_element):
            return self._get_item_contents_for_individual_element(individual_element)
        else:
            return [individual_element.text]

    def _element_has_children(self, element):
        return len(list(element)) != 0

    def _get_item_contents_for_individual_element(self, element):
        one_of = element.find("one-of")
        return [e.text for e in list(one_of.iter(tag="item"))]

    def questions_of_predicate(self, predicate):
        questions = self._grammar_root.findall("question[@predicate='%s'][@speaker='user']" % (predicate))
        if len(questions) < 1:
            actual_questions = self._grammar_root.findall("question[@speaker='user']")
            actual_predicates = [question.get("predicate") for question in actual_questions]
            raise NoQuestionsFoundException(
                "Expected at least one <question speaker='user'...> for predicate '%s' but "
                "it was not found among %s in %s" % (predicate, actual_predicates, self._grammar_path)
            )
        if len(questions) > 1:
            raise UnexpectedQuestionsFoundException(
                "Expected a single <question speaker='user' ...> for predicate "
                "'%s' but found %d in %s" % (predicate, len(questions), self._grammar_path)
            )
        question = questions[0]
        items = self._plain_text_items_of(question)
        for item in items:
            text_chunks, required_entities = self._chunks_and_entities_of_item(item)
            yield Question(predicate, text_chunks, required_entities)

    def answers(self):
        answers = self._grammar_root.findall("answer[@speaker='user']")
        if not answers:
            return
        if len(answers) > 1:
            raise UnexpectedAnswersFoundException(
                "Expected a single <answer speaker='user'> but found %d in %s" % (len(answers), self._grammar_path)
            )
        answer = answers[0]
        items = self._plain_text_items_of(answer)
        for item in items:
            text_chunks, required_entities = self._chunks_and_entities_of_item(item)
            if not required_entities:
                raise UnexpectedAnswerFormatException(
                    "Expected at least one <%s .../> in every item in <answer speaker=\"user\"> "
                    "but found some without" % self._local_individual_identifier
                )
            yield Answer(text_chunks, required_entities)

    def strings_of_predicate(self, predicate):
        strings = self._grammar_root.findall("string[@predicate='%s']" % predicate)
        if len(strings) > 1:
            raise UnexpectedStringsFoundException(
                "Expected a single <string predicate='%s'> but found %d in %s" %
                (predicate, len(strings), self._grammar_path)
            )

        if len(strings) == 0:
            warnings.warn(
                "Expected training examples for predicate '{predicate}' of sort '{sort}' but found none. "
                "Add them with:\n"
                "\n"
                "<string predicate=\"{predicate}\">\n"
                "  <one-of>\n"
                "    <item>an example</item>\n"
                "    <item>another example</item>\n"
                "  </one-of>\n"
                "</string>".format(predicate=predicate, sort=STRING)
            )
            return

        string = strings[0]
        items = self._plain_text_items_of(string)
        for item in items:
            text_chunks, required_entities = self._chunks_and_entities_of_item(item)
            if any(required_entities):
                raise UnexpectedIndividualsFoundException(
                    "Expected no <%s ...> in <string predicate='%s'> but found some" %
                    (self._local_individual_identifier, predicate)
                )
            assert len(text_chunks) == 1, "Expected 1 text chunk but got %d" % len(text_chunks)
            yield text_chunks[0]

    def _chunks_and_entities_of_item(self, item):
        text_chunks = [item.text or ""]
        required_entities = []
        local_individuals = item.findall(self._local_individual_identifier)
        for individual_element in local_individuals:
            required_entity = self._required_entity_from_individual_element(individual_element)
            required_entities.append(required_entity)
            tail = individual_element.tail or ""
            text_chunks.append(tail)
        self._strip_chunks(text_chunks)
        return text_chunks, required_entities

    def _strip_chunks(self, chunks):
        chunks[0] = chunks[0].lstrip()
        chunks[-1] = chunks[-1].rstrip()

    def _required_entity_from_individual_element(self, element):
        predicate = element.attrib.get("predicate")
        if predicate:
            return RequiredPropositionalEntity(predicate)
        sort = element.attrib.get("sort")
        if sort:
            return RequiredSortalEntity(sort)
        raise UnexpectedIndividualsFoundException(
            "Expected either a 'sort' or 'predicate' attribute in "
            "<%s ...>: %s" % (self._local_individual_identifier, element)
        )

    def _plain_text_items_of(self, item):
        raise NotImplementedError("%s._plain_text_items_of(...) need to be implemented." % self.__class__.__name__)

    def selection_policy_of_report(self, action, status):
        return selection_policy_names.DISABLED


class Grammar(GrammarBase):
    def __init__(self, language_code, grammar_path):
        super(Grammar, self).__init__(language_code, grammar_path)
        self._local_individual_identifier = Constants.SLOT

    def requests_of_action(self, name):
        actions = self._grammar_root.findall("%s[@name='%s']" % (Constants.ACTION, name))
        if len(actions) < 1:
            all_actions = self._grammar_root.findall(Constants.ACTION)
            all_names = [action.get("name") for action in all_actions]
            raise NoRequestsFoundException(
                "Expected at least one <action ...> for action '%s' but it was not found "
                "among %s in %s" % (name, all_names, self._grammar_path)
            )
        if len(actions) > 1:
            raise UnexpectedRequestsFoundException(
                "Expected a single <action ...> for action '%s' but found %d in %s" %
                (name, len(actions), self._grammar_path)
            )
        action_item = actions[0]
        items = list(self._plain_text_items_of(action_item))
        for item in items:
            text_chunks, required_entities = self._chunks_and_entities_of_item(item)
            yield Request(name, text_chunks, required_entities)

    def _plain_text_items_of(self, root):
        def get_items(root):
            items = self._items_of(root)
            for item in items:
                if item.find(Constants.VP) is not None or item.find(Constants.NP) is not None:
                    continue
                yield item

        plain_text_items = list(get_items(root))
        if not plain_text_items:
            warnings.warn(
                "%s ignores element '%s' with attributes %s since there are no plain text items" %
                (self.__class__.__name__, root.tag, root.attrib)
            )
        return plain_text_items

    def _items_of(self, root):
        items = root.findall("./%s/%s" % (Constants.ONE_OF, Constants.ITEM))
        if not items:
            yield root
        for item in items:
            yield item

    def _find_individuals_of(self, name):
        return self._grammar_root.findall("%s[@name='%s']" % (Constants.INDIVIDUAL, name))

    def selection_policy_of_report(self, action, status):
        report_element = self._grammar_root.find(
            "report[@action='{action}'][@status='{status}']".format(action=action, status=status)
        )
        if report_element is not None:
            one_of_element = report_element.find(Constants.ONE_OF)
            if one_of_element is not None and Constants.SELECTION in one_of_element.attrib:
                return one_of_element.attrib[Constants.SELECTION]
        return super(Grammar, self).selection_policy_of_report(action, status)


class GrammarForRGL(GrammarBase):
    def __init__(self, grammar_root, grammar_path):
        super(GrammarForRGL, self).__init__(grammar_root, grammar_path)
        self._local_individual_identifier = Constants.INDIVIDUAL

    def requests_of_action(self, action):
        requests = self._grammar_root.findall("%s[@action='%s']" % (rgl_grammar_entry_types.REQUEST, action))
        if len(requests) < 1:
            actual_requests = self._grammar_root.findall(rgl_grammar_entry_types.REQUEST)
            actual_actions = [request.get("action") for request in actual_requests]
            raise NoRequestsFoundException(
                "Expected at least one <request ...> for action '%s' but it was not found "
                "among %s in %s" % (action, actual_actions, self._grammar_path)
            )
        if len(requests) > 1:
            raise UnexpectedRequestsFoundException(
                "Expected a single <request ...> for action '%s' but found %d in %s" %
                (action, len(requests), self._grammar_path)
            )
        request = requests[0]
        items = self._plain_text_items_of(request)
        for item in items:
            text_chunks, required_entities = self._chunks_and_entities_of_item(item)
            yield Request(action, text_chunks, required_entities)

    def _plain_text_items_of(self, item):
        utterances = item.findall(rgl_grammar_entry_types.UTTERANCE)
        if not utterances:
            warnings.warn(
                "%s ignores element '%s' with attributes %s since it has no <utterance>" %
                (self.__class__.__name__, item.tag, item.attrib)
            )
            return

        for utterance in utterances:
            items = utterance.findall("./%s/%s" % (Constants.ONE_OF, Constants.ITEM))
            if not items:
                yield utterance
            for item in items:
                yield item

    def _find_individuals_of(self, name):
        return self._grammar_root.findall(
            "%s[@name='%s']/%s" % (Constants.INDIVIDUAL, name, rgl_grammar_entry_types.PROPER_NOUN)
        )
