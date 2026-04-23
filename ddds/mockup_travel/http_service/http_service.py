import json

from flask import Flask, request
from jinja2 import Environment

app = Flask(__name__)
environment = Environment()

CITY_TYPE = {"paris": "city_type_capital", "lyon": "non_capital"}


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1"
      }
    }
    """)  # yapf: disable
    payload = response_template.render()
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


def action_fail_response(failure_reason):
    response_template = environment.from_string("""
    {
      "status": "fail",
      "data": {
        "version": "1.1",
        "reason": {{ failure_reason|json }}
      }
    }
    """)  # yapf: disable
    payload = response_template.render(failure_reason=failure_reason)
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


def error_response(message):
    response_template = environment.from_string(
        """
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """
    )
    payload = response_template.render(message=message)
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)  # yapf: disable
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
    """)  # yapf: disable
    payload = response_template.render()
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


def empty_query_response():
    response_template = environment.from_string("""
        {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": []
      }
    }
    """)  # yapf: disable
    payload = response_template.render()
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
    """)  # yapf: disable
    payload = response_template.render(results=results)
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)  # yapf: disable
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


@app.route("/available_means_of_transport", methods=['POST'])
def available_means_of_transport():
    try:
        return multiple_query_response([{
            "value": "plane",
            "confidence": 1.0,
            "grammar_entry": "plane"
        }, {
            "value": "train",
            "confidence": 1.0,
            "grammar_entry": "train"
        }])
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/passenger_quantity_to_add", methods=['POST'])
def passenger_quantity_to_add():
    try:
        return query_response(value=1, grammar_entry=None)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/dept_city", methods=['POST'])
def dept_city():
    try:
        return empty_query_response()
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/num_available_dept_cities", methods=['POST'])
def num_available_dept_cities():
    try:
        payload = request.get_json()
        dest_city_value = payload["request"]["parameters"]["dest_city"]["value"]
        available_dept_cities = get_available_dept_cities(dest_city_value)
        return query_response(value=len(available_dept_cities), grammar_entry=None)
    except BaseException as exception:
        return error_response(message=str(exception))


def get_available_dept_cities(dest_city_value):
    results = [{"value": "city_madrid", "grammar_entry": "Madrid"}]
    if dest_city_value not in ["Athens", "آتن"]:
        results.append({"value": "city_helsinki", "grammar_entry": "Helsinki"})
        results.append({"value": None, "grammar_entry": "New York"})
    return results


@app.route("/available_dept_city", methods=['POST'])
def available_dept_city():
    try:
        payload = request.get_json()
        dest_city_value = payload["request"]["parameters"]["dest_city"]["value"]
        available_dept_cities = get_available_dept_cities(dest_city_value)
        return multiple_query_response(available_dept_cities)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/selected_train_type", methods=['POST'])
def seleted_train_type():
    try:
        return query_response(value="electrical", grammar_entry=None)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/selected_housing_for_pets", methods=['POST'])
@app.route("/available_member_type", methods=['POST'])
def available_member_type():
    try:
        return empty_query_response()
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/next_membership_points", methods=['POST'])
def next_membership_points():
    try:
        return query_response(value="50", grammar_entry=None)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/attraction_information", methods=['POST'])
def attraction_information():
    try:
        payload = request.get_json()
        string = payload["request"]["parameters"]["attraction"]["value"]
        if "Eiffel tower" in string:
            return query_response(
                value="the eiffel tower is a wrought iron lattice tower on the champ de mars in paris, france",
                grammar_entry=None
            )
        else:
            return query_response(value="no information was found", grammar_entry=None)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/next_membership_level", methods=['POST'])
def next_membership_level():
    try:
        return query_response(value="silver", grammar_entry=None)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/frequent_flyer_points", methods=['POST'])
def frequent_flyer_points():
    try:
        return query_response(value="50", grammar_entry=None)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/current_position", methods=['POST'])
def current_position():
    try:
        return query_response(value="London", grammar_entry="london")
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/flight_departure", methods=['POST'])
def flight_departure():
    try:
        return query_response(value="2018-04-11T22:00:00.000Z", grammar_entry="2018-04-11T22:00:00.000Z")
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/flight_on_time", methods=['POST'])
def flight_on_time():
    try:
        return query_response(value="on time", grammar_entry="on time")
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/flight_exists", methods=['POST'])
def flight_exists():
    try:
        return query_response(value="a connection", grammar_entry="a connection")
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/selected_housing", methods=['POST'])
@app.route("/selected_housing_for_contact", methods=['POST'])
@app.route("/selected_housing_for_moomins", methods=['POST'])
def selected_housing():
    try:
        return multiple_query_response([{
            "value": "sheraton",
            "grammar_entry": "Sheraton"
        }, {
            "value": "novotel",
            "grammar_entry": "Novotel"
        }])
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/qualified_for_membership", methods=['POST'])
def qualified_for_membership():
    try:
        payload = request.get_json()
        if "dest_city" in payload["request"]["parameters"] \
           and payload["request"]["parameters"]["dest_city"]:
            dest_city_value = payload["request"]["parameters"]["dest_city"]["value"]
        else:
            dest_city_value = None
        if dest_city_value == "pyongyang":
            return empty_query_response()
        return boolean_response(True)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/need_visa", methods=['POST'])
def need_visa():
    try:
        payload = request.get_json()
        if "dest_city" in payload["request"]["parameters"] \
           and payload["request"]["parameters"]["dest_city"]:
            dest_city_value = payload["request"]["parameters"]["dest_city"]["value"]
        else:
            dest_city_value = None

        if "dept_city" in payload["request"]["parameters"] \
           and payload["request"]["parameters"]["dept_city"]:
            dept_city_value = payload["request"]["parameters"]["dept_city"]["value"]
        else:
            dept_city_value = None

        cities_outside_eu = ["pyongyang", "city_teheran"]
        if dest_city_value not in cities_outside_eu and dept_city_value not in cities_outside_eu:
            return boolean_response(False)
        return boolean_response(True)
    except BaseException as exception:
        return error_response(message=str(exception))


def boolean_response(value):
    response_template = environment.from_string(
        """
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
          {
            "value": {{ value|json }},
            "confidence": 1.0,
            "grammar_entry": {{ None|json }}
          }
        ]
      }
    }
    """
    )
    payload = response_template.render(value=value)
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


@app.route("/room_availability", methods=['POST'])
def room_availability():
    try:
        return boolean_response(True)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/AddPassengers", methods=['POST'])
@app.route("/BookHousing", methods=['POST'])
@app.route("/CancelReservation", methods=['POST'])
@app.route("/MakeRandomReservation", methods=['POST'])
@app.route("/ShowOnMap", methods=['POST'])
def add_passengers():
    try:
        return action_success_response()
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/city_validity", methods=['POST'])
def city_validity():
    def _is_dest_city_valid():
        return dest_city["value"] not in invalid_values and \
            dest_city["grammar_entry"] not in invalid_values

    try:
        payload = request.get_json()
        dest_city = payload["request"]["parameters"]["dest_city"]
        invalid_values = ["pyongyang", "lisbon", "لیزبون"]
        return validator_response(_is_dest_city_valid())
    except BaseException as exception:
        return error_response(message=exception)


@app.route("/city_type_validity", methods=['POST'])
def city_type_validity():
    try:
        payload = request.get_json()
        dest_city = payload["request"]["parameters"]["dest_city"]["value"]
        dest_city_type = payload["request"]["parameters"]["dest_city_type"]["value"]
        return validator_response(CITY_TYPE[dest_city] == dest_city_type)
    except BaseException as exception:
        return error_response(message=exception)


def format_entries(entries):
    try:
        return [{"grammar_entry": None, "value": number} for number in entries]
    except BaseException as exception:
        return error_response(message=exception)


@app.route("/available_payment_method", methods=['POST'])
def available_payment_method():
    try:
        return multiple_query_response(format_entries(["visa", "mastercard", "points"]))
    except BaseException as exception:
        return error_response(message=exception)


@app.route("/frequent_flyer_number", methods=['POST'])
def frequent_flyer_number():
    try:
        return query_response(value="123-456", grammar_entry=None)
    except BaseException as exception:
        return error_response(message=exception)


@app.route("/code", methods=['POST'])
def code():
    try:
        return query_response(value="XL34", grammar_entry=None)
    except BaseException as exception:
        return error_response(message=exception)


@app.route("/make_reservation", methods=['POST'])
def make_reservation():
    try:
        payload = request.get_json()
        dept_city = payload["request"]["parameters"]["dept_city"]["value"]
        dest_city = payload["request"]["parameters"]["dest_city"]["value"]
        if dest_city == dept_city:
            failure_reason = "dest_city_same_as_dept_city"
            return action_fail_response(failure_reason)
        return action_success_response()
    except BaseException as exception:
        return error_response(message=exception)


@app.route("/price", methods=['POST'])
def price():
    try:
        payload = request.get_json()
        dept_city = payload["request"]["parameters"]["dept_city"]["value"]
        dest_city = payload["request"]["parameters"]["dest_city"]["value"]
        if dest_city is not None and dept_city is not None:
            return query_response(value=1234.0, grammar_entry=None)
        return empty_query_response()
    except BaseException as exception:
        return error_response(message=exception)
