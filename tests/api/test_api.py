import unittest

from fastapi.testclient import TestClient

from api.main import app


def application():
    return {
        "studentInfo": {"firstName": "Jane", "lastName": "Smith", "ssn": "123456789",
                        "dateOfBirth": "2003-05-15"},
        "dependencyStatus": "dependent", "maritalStatus": "single",
        "household": {"numberInHousehold": 4, "numberInCollege": 1},
        "income": {"studentIncome": 5000, "parentIncome": 65000}, "stateOfResidence": "CA",
    }


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def post(self, body):
        return self.client.post("/api/v1/fafsa/evaluate", json=body)

    def evaluate(self, body):
        response = self.post(body)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_valid_sample(self):
        result = self.evaluate(application())
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["outstanding"], [])
        self.assertTrue(all(r["status"] == "VALID" and r["rule_name"] for r in result["submitted"]))

    def test_invalid_sample(self):
        body = application()
        body.update(maritalStatus="married", stateOfResidence="XX",
                    income={"studentIncome": -1000}, household={"numberInHousehold": 2, "numberInCollege": 5})
        body["studentInfo"].update(dateOfBirth="2015-01-01", ssn="invalid")
        result = self.evaluate(body)
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["outstanding"], ["income.parentIncome", "spouseInfo.firstName",
                                                "spouseInfo.lastName", "spouseInfo.ssn"])
        failures = [r for r in result["submitted"] if r["status"] == "INVALID"]
        self.assertEqual({r["field_name"] for r in failures}, {
            "studentInfo.dateOfBirth", "studentInfo.ssn", "income.studentIncome",
            "household.numberInCollege", "stateOfResidence"})
        self.assertTrue(all(r["severity"] == "ERROR" and r["violation_message"] for r in failures))

    def test_conditional_paths(self):
        for dependency in ["independent", "dependent"]:
            for marital in ["single", "married"]:
                with self.subTest(dependency=dependency, marital=marital):
                    body = application()
                    body.update(dependencyStatus=dependency, maritalStatus=marital)
                    if dependency == "independent":
                        del body["income"]["parentIncome"]
                    if marital == "married":
                        body["spouseInfo"] = {"firstName": "Sam", "lastName": "Smith", "ssn": "321456789"}
                    self.assertEqual(self.evaluate(body)["status"], "VALID")

    def test_early_validation_and_priority(self):
        result = self.evaluate({"cumulative_payload": {"student.ssn": "bad"}})
        self.assertEqual(result["outstanding"], ["dependencyStatus", "maritalStatus"])
        self.assertEqual(result["submitted"][0]["rule_name"], "validate_ssn_format")
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(self.evaluate({"cumulative_payload": {}})["status"], "INCOMPLETE")

    def test_invalid_status_and_unknown_field(self):
        result = self.evaluate({"maritalStatus": "other", "unknown": 1})
        self.assertEqual([r["status"] for r in result["submitted"]], ["INVALID", "INVALID"])

    def test_bad_requests(self):
        for body in [{}, {"cumulative_payload": []}, {"parent.income": 0, "income": {"parentIncome": 10}}]:
            self.assertEqual(self.post(body).status_code, 422)
