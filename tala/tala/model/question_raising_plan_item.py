import copy

from tala.model.error import DomainError
from tala.model.plan_item import PlanItemWithSemanticContent, PlanItem


class QuestionRaisingPlanItem(PlanItemWithSemanticContent):
    GRAPHICAL_TYPE_TEXT = "text"
    GRAPHICAL_TYPE_LIST = "list"
    SOURCE_SERVICE = "service"
    SOURCE_DOMAIN = "domain"
    ALPHABETIC = "alphabetic"

    def __init__(self, domain_name, type, content, allow_pcom_answer=False):
        if not content.is_question():
            raise DomainError("cannot create QuestionRaisingPlanItem " + "from non-question %s" % content)
        self._domain_name = domain_name
        self._allow_answer_from_pcom = allow_pcom_answer
        PlanItemWithSemanticContent.__init__(self, type, content)

    @property
    def domain_name(self):
        return self._domain_name

    @property
    def allow_answer_from_pcom(self):
        return self._allow_answer_from_pcom

    def is_question_raising_item(self):
        return True

    def get_question(self):
        return self.getContent()

    def clone_as_type(self, type):
        clone = copy.deepcopy(self)
        clone._type = type
        return clone

    def __str__(self):
        if self._content is None:
            content_string = ""
        else:
            content_string = str(self._content)
        return "%s(%s)" % (str(self._type), content_string)


class FindoutPlanItem(QuestionRaisingPlanItem):
    def __init__(self, domain_name, content, allow_answer_from_pcom=False):
        QuestionRaisingPlanItem.__init__(self, domain_name, PlanItem.TYPE_FINDOUT, content, allow_answer_from_pcom)


class RaisePlanItem(QuestionRaisingPlanItem):
    def __init__(self, domain_name, content):
        QuestionRaisingPlanItem.__init__(self, domain_name, PlanItem.TYPE_RAISE, content)


class UnexpectedDomainException(Exception):
    pass


class QuestionRaisingPlanItemOfDomain(object):
    def __init__(self, domain, plan_item):
        if domain.name != plan_item.domain_name:
            raise UnexpectedDomainException(
                "Expected domain '%s' to match domain of plan item %s but it was '%s'" %
                (plan_item.domain_name, plan_item, domain)
            )
        self._domain = domain
        self._plan_item = plan_item

    def get_alternatives(self):
        return self._domain.get_alternatives(self._plan_item.get_question())

    def get_graphical_type(self):
        return self._domain.get_graphical_type(self._plan_item.get_question())

    def get_incremental(self):
        return self._domain.get_incremental(self._plan_item.get_question())

    def get_source(self):
        return self._domain.get_source(self._plan_item.get_question())

    def get_format(self):
        return self._domain.get_format(self._plan_item.get_question())

    def get_default(self):
        return self._domain.get_default(self._plan_item.get_question())

    def get_service_query(self):
        return self._domain.get_service_query(self._plan_item.get_question())

    def get_label_questions(self):
        return self._domain.get_label_questions(self._plan_item.get_question())

    def has_parameters(self):
        return (
            self.get_alternatives() or self.get_graphical_type() or self.get_incremental() or self.get_source()
            or self.get_format() or self.get_default() or self.get_service_query() or self.get_label_questions()
        )
