import pytest

from tala.model.ontology import Ontology, OntologyError, InvalidIndividualName, AmbiguousNamesException, IndividualExistsException, SortDoesNotExistException
from tala.model.predicate import Predicate
from tala.model.sort import RealSort, IntegerSort, ImageSort, DomainSort, CustomSort, BooleanSort, DateTimeSort, WebviewSort, StringSort, PersonNameSort, REAL, INTEGER, IMAGE, BOOLEAN, DATETIME, WEBVIEW, STRING
from tala.model.image import Image
from tala.model.webview import Webview
from tala.model.date_time import DateTime
from tala.model.person_name import PersonName
from tala.ddd.json_parser import JSONOntologyParser


class TestOntology(object):
    DEFAULT_NAME = "mockup_ontology"

    def _given_ontology(self, **kwargs):
        self._create_ontology(**kwargs)
        ontology_as_json = self._ontology.as_json()
        json_parser = JSONOntologyParser()
        self._ontology = json_parser.parse_ontology(ontology_as_json)

    def _when_creating_ontology(self, **kwargs):
        self._create_ontology(**kwargs)

    def _create_ontology(self, name=None, sorts=None, predicates=None, individuals=None, actions=None):
        if name is None:
            name = "mockup_ontology"
        if sorts is None:
            sorts = set()
        if predicates is None:
            predicates = set()
        if individuals is None:
            individuals = {}
        if actions is None:
            actions = []
        self._ontology = Ontology(name, sorts, predicates, individuals, actions)

    def _create_predicate(self, name, sort, *args, **kwargs):
        ontology_name = sort.ontology_name if sort.is_ontology_specific() else self.DEFAULT_NAME
        return Predicate(ontology_name, name, sort, *args, **kwargs)


class TestOntologyBasic(TestOntology):
    def test_get_name(self):
        self._given_ontology(name="mockup_ontology")
        assert "mockup_ontology" == self._ontology.get_name()

    def test_sorts_base_case(self):
        self._given_ontology(name=self.DEFAULT_NAME, sorts={CustomSort(self.DEFAULT_NAME, "city")})
        self._when_get_sorts_is_called()
        self._then_result_contains_key("city", CustomSort(self._ontology.name, "city"))

    def _when_get_sorts_is_called(self):
        self._result = self._ontology.get_sorts()

    def _then_result_contains_key(self, key, value):
        assert value == self._result[key]

    def test_predicates_base_case(self):
        self._given_ontology(
            name=self.DEFAULT_NAME,
            predicates={self._create_predicate("dest_city", CustomSort(self.DEFAULT_NAME, "city"))},
            sorts={CustomSort(self.DEFAULT_NAME, "city")}
        )
        self._when_get_predicates_is_called()
        self._then_result_is({
            "dest_city": self._create_predicate("dest_city", CustomSort(self._ontology.name, "city"))
        })

    def _when_get_predicates_is_called(self):
        self._result = self._ontology.get_predicates()

    def test_individuals_base_case(self):
        self._given_ontology(
            name=self.DEFAULT_NAME,
            individuals={"paris": CustomSort(self.DEFAULT_NAME, "city")},
            sorts={CustomSort(self.DEFAULT_NAME, "city")}
        )
        self._when_get_individuals_is_called()
        self._then_result_is({"paris": CustomSort(self.DEFAULT_NAME, "city")})

    def _when_get_individuals_is_called(self):
        self._result = self._ontology.get_individuals()

    def test_actions_with_additional_action(self):
        self._given_ontology(actions={"buy"})
        self._when_get_actions_is_called()
        self._then_result_is({"buy", "top", "up", "how"})

    def _when_get_actions_is_called(self):
        self._result = self._ontology.get_actions()

    def _then_result_contains(self, obj):
        assert obj in self._result

    def test_get_ddd_specific_actions_with_additional_action(self):
        self._given_ontology(actions={"buy"})
        self._when_get_ddd_specific_actions_is_called()
        self._then_result_is({"buy"})

    def test_default_sorts(self):
        self._given_ontology()
        self._when_get_sorts_is_called()
        self._then_result_contains_key("domain", DomainSort())

    def test_builtin_sorts_added_for_predicates(self):
        self._given_ontology(name=self.DEFAULT_NAME, predicates={self._create_predicate("price", RealSort())})
        self._when_get_sorts_is_called()
        self._then_result_contains_key("real", RealSort())

    def test_default_actions_included_in_get_actions(self):
        self._given_ontology()
        self._when_get_actions_is_called()
        self._then_result_is({"top", "up", "how"})

    def test_default_actions_missing_from_get_ddd_specific_actions(self):
        self._given_ontology()
        self._when_get_ddd_specific_actions_is_called()
        self._then_result_is(set())

    def _when_get_ddd_specific_actions_is_called(self):
        self._result = self._ontology.get_ddd_specific_actions()

    def test_individual_sort_for_custom_sort(self):
        self._given_ontology(
            name=self.DEFAULT_NAME,
            sorts={CustomSort(self.DEFAULT_NAME, "city")},
            predicates={self._create_predicate("selected_city", CustomSort(self.DEFAULT_NAME, "city"))},
            individuals={"paris": CustomSort(self.DEFAULT_NAME, "city")}
        )
        self._when_individual_sort_is_called("paris")
        self._then_result_is(CustomSort(self.DEFAULT_NAME, "city"))

    def _when_individual_sort_is_called(self, name):
        self._result = self._ontology.individual_sort(name)

    def _then_result_is(self, expected_result):
        assert expected_result == self._result

    def test_individual_sort_for_builtin_sort(self):
        self._given_ontology(predicates={self._create_predicate("price", RealSort())})
        self._when_individual_sort_is_called(123.50)
        self._then_result_is(RealSort())

    def test_individual_sort_for_undefined_sort_raises_exception(self):
        self._given_ontology()
        with pytest.raises(OntologyError):
            self._when_individual_sort_is_called("kalle")

    def test_individual_sort_for_boolean_supported_by_ontology(self):
        self._given_ontology(predicates={self._create_predicate("needs_visa", BooleanSort())})
        self._when_individual_sort_is_called(True)
        self._then_result_is(BooleanSort())

    def test_individual_sort_for_boolean_unsupported_by_ontology(self):
        self._given_ontology()
        self._when_individual_sort_is_called_then_exception_is_raised_matching(
            True, OntologyError, "Expected one of the predicate sorts [] in ontology '{}', "
            "but got value 'True' of sort 'boolean'".format(self.DEFAULT_NAME)
        )

    def _when_individual_sort_is_called_then_exception_is_raised_matching(
        self, value, expected_exception, expected_message
    ):
        with pytest.raises(expected_exception) as exception_information:
            self._ontology.individual_sort(value)
        assert expected_message == str(exception_information.value)

    def test_individual_sort_for_datetime_supported_by_ontology(self):
        self._given_ontology(predicates={self._create_predicate("departure_time", DateTimeSort())})
        self._when_individual_sort_is_called(DateTime("2018-03-20T22:00:00.000Z"))
        self._then_result_is(DateTimeSort())

    def test_individual_sort_for_datetime_unsupported_by_ontology(self):
        self._given_ontology()
        self._when_individual_sort_is_called_then_exception_is_raised_matching(
            DateTime("2018-03-20T22:00:00.000Z"), OntologyError,
            "Expected one of the predicate sorts [] in ontology '{}', "
            "but got value 'datetime(2018-03-20T22:00:00.000Z)' of sort 'datetime'".format(self.DEFAULT_NAME)
        )

    def test_is_action_true(self):
        self._given_ontology(actions={"buy"})
        self._when_is_action_is_called("buy")
        self._then_result_is(True)

    def _when_is_action_is_called(self, obj):
        self._result = self._ontology.is_action(obj)

    def test_is_action_false(self):
        self._given_ontology(actions={"buy"})
        self._when_is_action_is_called("destination")
        self._then_result_is(False)

    def test_predicate_declaration_with_unknown_sort_yields_exception(self):
        with pytest.raises(OntologyError):
            self._when_creating_ontology(
                sorts=set(),
                predicates={self._create_predicate("some_predicate", CustomSort(self.DEFAULT_NAME, "unknown_sort"))},
                individuals={},
                actions=set(),
                name="InvalidOntology"
            )

    def test_individual_declaration_with_unknown_sort_yields_exception(self):
        with pytest.raises(OntologyError):
            self._when_creating_ontology(
                sorts=set(),
                predicates=set(),
                individuals={"some_individual": CustomSort(self.DEFAULT_NAME, "unknown_sort")},
                actions=set(),
                name="InvalidOntology"
            )

    def test_has_predicate_true(self):
        self._given_ontology(
            predicates={self._create_predicate("dest_city", CustomSort(self.DEFAULT_NAME, "city"))},
            sorts={CustomSort(self.DEFAULT_NAME, "city")}
        )
        self._when_has_predicate_is_called("dest_city")
        self._then_result_is(True)

    def _when_has_predicate_is_called(self, obj):
        self._result = self._ontology.has_predicate(obj)

    def test_has_predicate_false(self):
        self._given_ontology()
        self._when_has_predicate_is_called("dest_city")
        self._then_result_is(False)

    def test_has_sort_true(self):
        self._given_ontology(sorts={CustomSort(self.DEFAULT_NAME, "city")})
        self._when_has_sort_is_called("city")
        self._then_result_is(True)

    def _when_has_sort_is_called(self, obj):
        self._result = self._ontology.has_sort(obj)

    def test_has_sort_false(self):
        self._given_ontology()
        self._when_has_sort_is_called("city")
        self._then_result_is(False)

    def test_invalid_individual_name_in_constructor_yields_exception(self):
        with pytest.raises(InvalidIndividualName):
            self._when_creating_ontology(individuals={"name with whitespace": IntegerSort()})

    def test_action_shares_name_with_predicate_raises_error(self):
        with pytest.raises(AmbiguousNamesException):
            self._when_creating_ontology(
                sorts=set(),
                predicates={self._create_predicate("price", RealSort())},
                individuals={},
                actions={"price"}
            )

    @pytest.mark.parametrize(
        "sort,name", [(RealSort(), REAL), (BooleanSort(), BOOLEAN), (IntegerSort(), INTEGER), (ImageSort(), IMAGE),
                      (WebviewSort(), WEBVIEW), (StringSort(), STRING), (DateTimeSort(), DATETIME)]
    )
    def test_predicates_contain_builtin_sort_base_case(self, sort, name):
        self._given_ontology(predicates={self._create_predicate("predicate", sort)}, )
        self._when_predicates_contain_sort_is_called_with(name)
        self._then_result_is(True)

    @pytest.mark.parametrize(
        "sort,name", [(RealSort(), REAL), (BooleanSort(), BOOLEAN), (IntegerSort(), INTEGER), (ImageSort(), IMAGE),
                      (WebviewSort(), WEBVIEW), (StringSort(), STRING), (DateTimeSort(), DATETIME)]
    )
    def test_predicates_contain_builtin_sort_when_ontology_has_predicates_of_custom_sorts(self, sort, name):
        self._given_ontology(
            sorts={CustomSort(self.DEFAULT_NAME, "sort"),
                   CustomSort(self.DEFAULT_NAME, "another sort")},
            predicates={
                self._create_predicate("first predicate", CustomSort(self.DEFAULT_NAME, "sort")),
                self._create_predicate("second predicate", sort),
                self._create_predicate("third predicate", CustomSort(self.DEFAULT_NAME, "another sort"))
            },
        )
        self._when_predicates_contain_sort_is_called_with(name)
        self._then_result_is(True)

    def _when_predicates_contain_sort_is_called_with(self, sort):
        self._result = self._ontology.predicates_contain_sort(sort)

    @pytest.mark.parametrize("name", [REAL, BOOLEAN, INTEGER, IMAGE, WEBVIEW, STRING, DATETIME])
    def test_predicates_do_not_contain_builtin_sort_base_case(self, name):
        self._given_ontology(name=self.DEFAULT_NAME)
        self._when_predicates_contain_sort_is_called_with(name)
        self._then_result_is(False)

    @pytest.mark.parametrize("name", [REAL, BOOLEAN, INTEGER, IMAGE, WEBVIEW, STRING, DATETIME])
    def test_predicates_do_not_contain_builtin_sort_when_ontology_only_contains_predicate_of_custom_sort(self, name):
        self._given_ontology(
            name=self.DEFAULT_NAME,
            sorts={CustomSort(self.DEFAULT_NAME, "city")},
            predicates={self._create_predicate("selected_city", CustomSort(self.DEFAULT_NAME, "city"))},
            individuals={"paris": CustomSort(self.DEFAULT_NAME, "city")}
        )
        self._when_predicates_contain_sort_is_called_with(name)
        self._then_result_is(False)

    @pytest.mark.parametrize(
        "value,sort", [(25.5, REAL), (True, BOOLEAN), (14, INTEGER), (Image("image-url"), IMAGE),
                       (Webview("webview-url"), WEBVIEW), ("a string", STRING),
                       (DateTime("2018-03-20T22:00:00.000Z"), DATETIME)]
    )
    def test_individual_sort_for_builtin_sort_unsupported_by_ontology_base_case(self, value, sort):
        self._given_ontology(name=self.DEFAULT_NAME)
        self._when_individual_sort_is_called_then_exception_is_raised_matching(
            value, OntologyError, "Expected one of the predicate sorts [] in ontology '{}', "
            "but got value '{}' of sort '{}'".format(self.DEFAULT_NAME, value, sort)
        )

    @pytest.mark.parametrize(
        "value,sort", [(25.5, REAL), (True, BOOLEAN), (14, INTEGER), (Image("image-url"), IMAGE),
                       (Webview("webview-url"), WEBVIEW), ("a string", STRING),
                       (DateTime("2018-03-20T22:00:00.000Z"), DATETIME)]
    )
    def test_individual_sort_for_builtin_sort_unsupported_by_ontology_when_ontology_has_custom_sorts(self, value, sort):
        self._given_ontology(
            name=self.DEFAULT_NAME,
            sorts={CustomSort(self.DEFAULT_NAME, "a sort"),
                   CustomSort(self.DEFAULT_NAME, "another sort")},
            predicates={
                self._create_predicate("a predicate 1", CustomSort(self.DEFAULT_NAME, "a sort")),
                self._create_predicate("a predicate 2", CustomSort(self.DEFAULT_NAME, "a sort")),
                self._create_predicate("another predicate 1", CustomSort(self.DEFAULT_NAME, "another sort")),
                self._create_predicate("another predicate 2", CustomSort(self.DEFAULT_NAME, "another sort"))
            },
            individuals={"individual": CustomSort(self.DEFAULT_NAME, "a sort")}
        )
        self._when_individual_sort_is_called_then_exception_is_raised_matching(
            value, OntologyError, "Expected one of the predicate sorts ['a sort', 'another sort'] in ontology '{}', "
            "but got value '{}' of sort '{}'".format(self.DEFAULT_NAME, value, sort)
        )

    def test_identical_sort_and_predicate_name_raises_exception(self):
        self._when_creating_ontology_then_exception_is_raised(
            sorts={CustomSort(self.DEFAULT_NAME, "mock-name")},
            predicates={self._create_predicate("mock-name", CustomSort(self.DEFAULT_NAME, "mock-name"))},
            expected_exception=AmbiguousNamesException,
            expected_message="Expected predicate and sort names to be unique but there is both a predicate and sort "
                             f"named 'mock-name' in ontology '{self.DEFAULT_NAME}'"
        )  # yapf: disable

    def _when_creating_ontology_then_exception_is_raised(self, expected_exception, expected_message, *args, **kwargs):
        with pytest.raises(expected_exception, match=expected_message):
            self._create_ontology(*args, **kwargs)


class TestDynamicOntology(TestOntology):
    def test_add_dynamic_individual(self):
        self._given_ontology(sorts={CustomSort(self.DEFAULT_NAME, "city")})
        self._when_individual_is_added("paris", "city")
        self._then_individual_is_in_the_ontology("paris", "city")

    def _when_individual_is_added(self, name, sort):
        self._ontology.add_individual(name, sort)

    def _then_individual_is_in_the_ontology(self, name, sort):
        sort_as_instance = self._ontology.get_sort(sort)
        assert (name, sort_as_instance) in list(self._ontology.get_individuals().items())

    def test_adding_existing_individual_yields_exception(self):
        self._given_ontology(
            sorts={CustomSort(self.DEFAULT_NAME, "city")}, individuals={"paris": CustomSort(self.DEFAULT_NAME, "city")}
        )
        with pytest.raises(IndividualExistsException):
            self._when_individual_is_added("paris", "city")

    def test_add_individual_with_non_existing_sort_yields_exception(self):
        self._given_ontology()
        with pytest.raises(SortDoesNotExistException):
            self._when_individual_is_added("athens", "river")

    def test_ensure_individual_exists_non_existing_individual(self):
        self._given_ontology(sorts={CustomSort(self.DEFAULT_NAME, "city")})
        self._when_ensure_individual_exists_is_called("paris", "city")
        self._then_individual_is_in_the_ontology("paris", "city")

    def _when_ensure_individual_exists_is_called(self, name, sort):
        self._ontology.ensure_individual_exists(name, sort)

    def test_ensure_individual_exists_existing_individual(self):
        self._given_ontology(
            sorts={CustomSort(self.DEFAULT_NAME, "city")}, individuals={"paris": CustomSort(self.DEFAULT_NAME, "city")}
        )
        self._when_ensure_individual_exists_is_called("paris", "city")
        self._then_no_exception_is_read()

    def _then_no_exception_is_read(self):
        pass

    def test_add_individual_checks_name(self):
        self._given_ontology()
        with pytest.raises(InvalidIndividualName):
            self._when_individual_is_added("name with whitespace", "integer")

    def test_ensure_individual_exists_checks_name(self):
        self._given_ontology()
        with pytest.raises(InvalidIndividualName):
            self._when_ensure_individual_exists_is_called("name with whitespace", "integer")

    def test_create_person_name_individual(self):
        self._given_ontology(sorts={})
        self._when_individual_is_created("Anna Kronlid", PersonNameSort())
        self._then_individual_is_of_right_type()

    def _when_individual_is_created(self, individual_string, sort):
        self._individual = self._ontology.create_individual(individual_string, sort)

    def _then_individual_is_of_right_type(self):
        assert self._individual.sort == PersonNameSort()
        assert self._individual.value == PersonName("Anna Kronlid")
