from tala.model.proposition import ImplicationProposition
from tala.model.query import ImplicationQuery, EnumerationQuery, IteratorQuery, create_query_from_json_api_data
from tala.testing.lib_test_case import LibTestCase
from tala.utils.json_api import IncludedObject


class QuerySerializationTests(LibTestCase):
    def setUp(self):
        self.setUpLibTestCase()
        self.question = self.dest_city_question
        self.propositions = [self.proposition_dest_city_paris, self.proposition_dest_city_london]
        self.implication = ImplicationProposition(
            self.proposition_dest_city_paris,
            self.proposition_dest_city_london,
        )

    def test_implication_query_roundtrip(self):
        query = ImplicationQuery(self.question, [self.implication])
        query_as_json = query.as_json_api_dict()

        included = IncludedObject(query_as_json["included"])
        loaded = ImplicationQuery.create_from_json_api_data(query_as_json["data"], included)

        self.assertEqual(query, loaded)

    def test_enumeration_query_roundtrip(self):
        query = EnumerationQuery(self.question, "for_enumeration", self.propositions)
        query_as_json = query.as_json_api_dict()

        included = IncludedObject(query_as_json["included"])
        loaded = EnumerationQuery.create_from_json_api_data(query_as_json["data"], included)

        self.assertEqual(query, loaded)

    def test_iterator_query_roundtrip(self):
        query = IteratorQuery("?X.dest_city(X)", 5, "for_random_enumeration", self.propositions)
        query_as_json = query.as_json_api_dict()

        included = IncludedObject(query_as_json["included"])
        loaded = IteratorQuery.create_from_json_api_data(query_as_json["data"], included)

        self.assertEqual(query, loaded)

    def test_create_query_factory(self):
        query = EnumerationQuery(self.question, "for_enumeration", self.propositions)
        query_as_json = query.as_json_api_dict()

        included = IncludedObject(query_as_json["included"])
        loaded = create_query_from_json_api_data(query_as_json["data"], included)

        self.assertEqual(query, loaded)
