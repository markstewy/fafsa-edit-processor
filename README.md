# FAFSA Rule Processor

The FastAPI service evaluates a cumulative form submission from the first stage on every request. Send all answers collected so far, using dotted field names or nested JSON objects.

## Install and run

From the project root, using Python 3.9 or newer on macOS or Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

## Try the API

Send the application object directly or inside `cumulative_payload`. The same endpoint accepts partial and complete applications. Run these commands in a second terminal.

```sh
# Invalid request body (HTTP 422)
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{}'

# Invalid application
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{
  "studentInfo": {
    "firstName": "John",
    "lastName": "Doe",
    "dateOfBirth": "2015-01-01",
    "ssn": "invalid"
  },
  "dependencyStatus": "dependent",
  "maritalStatus": "married",
  "income": {
    "studentIncome": -1000
  },
  "household": {
    "numberInHousehold": 2,
    "numberInCollege": 5
  },
  "stateOfResidence": "XX"
}'

# Valid answers, incomplete application
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{"dependencyStatus": "independent"}'

# Complete dependent, married application
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{
  "studentInfo": {
    "firstName": "Jane",
    "lastName": "Smith",
    "dateOfBirth": "2003-05-15",
    "ssn": "123456789"
  },
  "dependencyStatus": "dependent",
  "maritalStatus": "married",
  "income": {
    "studentIncome": 5000,
    "parentIncome": 65000
  },
  "household": {
    "numberInHousehold": 4,
    "numberInCollege": 1
  },
  "stateOfResidence": "CA",
  "spouseInfo": {
    "firstName": "Sam",
    "lastName": "Smith",
    "ssn": "321456789"
  }
}'

# Any INVALID submitted result gives INVALID. Otherwise outstanding fields give INCOMPLETE.
# When all submitted checks pass and outstanding is empty, status is VALID.
```

## Run tests

With the virtual environment active:

```sh
python -m pip install '.[test]'
python -m coverage run -m unittest discover
python -m coverage report
```

## Assessment requirements

- Application data, seven required edits, and results — decisions 4, 5, and 8.
- Rule representation, extensibility, priority, error handling, conflicts, and severity — decisions 4, 5, and 8.
- Performance across applications — decisions 1 and 2.
- Test strategy and examples — decisions 7 and 8.

[Requirements and answers](DECISIONS.md#requirements)

## Example response

For the incomplete example above:

```sh
# {
#   "status": "INCOMPLETE",
#   "submitted": [
#     {
#       "field_name": "dependencyStatus",
#       "status": "VALID",
#       "violation_message": null,
#       "rule_name": "validate_choice",
#       "severity": "ERROR"
#     }
#   ],
#   "outstanding": [
#     "maritalStatus"
#   ],
#   "info": {
#     "version": "1.0.0-alpha.1"
#   }
# }
```
