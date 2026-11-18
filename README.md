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

With the server running, paste any command below into a second terminal. Each request stands on its own. Send all answers collected so far, either as a JSON object or inside `cumulative_payload`.

A **stage** is a named list of fields that must be present and valid before validation can advance. Follow a request through three files:

1. FastAPI passes the answers to `evaluate_fafsa_payload()`. The engine looks up `STAGE_GRAPH["root_stage"]` to find the starting stage. [core/engine.py](core/engine.py)
2. Validation starts at **Stage 1 (root): `stage_statuses`**. Its two required fields are `dependencyStatus` and `maritalStatus`. Its transition function, `application_stage()`, uses the pattern `stage_{dependencyStatus}_{maritalStatus}` to select the next stage. [core/stages.py](core/stages.py)
3. For each supplied field, the catalog identifies which rule to run. A path such as `studentInfo.ssn` refers to the `ssn` key inside the request’s `studentInfo` object. [core/rule_field_catalog.yaml](core/rule_field_catalog.yaml)

The response field `status` gives the overall application result (`VALID`, `INCOMPLETE`, or `INVALID`). When the walk ends, the engine checks any remaining supplied fields. The response lists their results together with the earlier checks in `submitted`. Missing required fields from the stage reached appear in `outstanding`.

### Start a partial application

```sh
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{"dependencyStatus": "independent"}'
```

**Stage 1: `stage_statuses`** (only stage reached). The applicant has started the form. The engine knows their dependency status, but needs their marital status to choose a second stage.

1. **Stage 1 (root): `stage_statuses`.** This stage requires two answers. The first, `dependencyStatus = "independent"`, is an allowed choice and returns `VALID`. The second required field, `maritalStatus`, is missing.
2. **Stop at the root.** The engine adds `maritalStatus` to `outstanding`. It needs both answers to call `application_stage()`, so it stops before selecting the next stage.
3. **Return `INCOMPLETE`.** The only submitted answer passed. The client can send the cumulative answers again after collecting `maritalStatus`.

<details>
<summary>Expected output · HTTP 200 OK · INCOMPLETE</summary>

```json
{
  "status": "INCOMPLETE",
  "submitted": [
    {
      "field_name": "dependencyStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    }
  ],
  "outstanding": [
    "maritalStatus"
  ],
  "info": {
    "version": "1.0.0-alpha.1"
  }
}
```

</details>

---

### Complete an independent, single application

```sh
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{
    "dependencyStatus": "independent", "maritalStatus": "single",
    "studentInfo": {"firstName":"Jane","lastName":"Smith","dateOfBirth":"2003-05-15","ssn":"123456789"},
    "income": {"studentIncome":5000},
    "household": {"numberInHousehold":4,"numberInCollege":1},
    "stateOfResidence": "CA"
  }'
```

**Stage 1: `stage_statuses` → Stage 2: `stage_independent_single`.** The first stage uses two answers to choose a checklist. For a single, independent applicant, the second stage requires student, income, household, and residence information. Parent income and spouse details are optional on this path.

1. **Stage 1 (root): `stage_statuses`.** This stage requires `dependencyStatus` (allowed values: `dependent`, `independent`) and `maritalStatus` (allowed values: `single`, `married`). This request supplies `"independent"` and `"single"`, respectively. Both checks return `VALID`.
2. **Follow the transition.** Because both fields passed, the engine calls `application_stage(payload)` in `core/stages.py`. For this request, `"stage_" + "independent" + "_" + "single"` produces `"stage_independent_single"`. The engine looks up that exact stage in the graph. [Stage graph and transition function](core/stages.py)
3. **Stage 2: `stage_independent_single`.** The engine checks each field below in order and collects its result before returning the response.

| Required field | Value in this request | Check result |
| --- | --- | --- |
| `studentInfo.firstName` | `"Jane"` | `VALID` |
| `studentInfo.lastName` | `"Smith"` | `VALID` |
| `studentInfo.dateOfBirth` | `"2003-05-15"` | `VALID` |
| `studentInfo.ssn` | `"123456789"` | `VALID` |
| `income.studentIncome` | `5000` | `VALID` |
| `household.numberInHousehold` | `4` | `VALID` |
| `household.numberInCollege` | `1` | `VALID` |
| `stateOfResidence` | `"CA"` | `VALID` |

**Response.** All required fields in this final stage passed, so the application is `VALID` and `outstanding` is empty.

<details>
<summary>Expected output · HTTP 200 OK · VALID</summary>

```json
{
  "status": "VALID",
  "submitted": [
    {
      "field_name": "dependencyStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "maritalStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.firstName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.lastName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.dateOfBirth",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_student_age",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.ssn",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_ssn_format",
      "severity": "ERROR"
    },
    {
      "field_name": "income.studentIncome",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_non_negative_amount",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInHousehold",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInCollege",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "stateOfResidence",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_state_code",
      "severity": "ERROR"
    }
  ],
  "outstanding": [],
  "info": {
    "version": "1.0.0-alpha.1"
  }
}
```

</details>

---

### Change the applicant to dependent

```sh
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{
    "dependencyStatus": "dependent", "maritalStatus": "single",
    "studentInfo": {"firstName":"Jane","lastName":"Smith","dateOfBirth":"2003-05-15","ssn":"123456789"},
    "income": {"studentIncome":5000},
    "household": {"numberInHousehold":4,"numberInCollege":1},
    "stateOfResidence": "CA"
  }'
```

**Stage 1: `stage_statuses` → Stage 2: `stage_dependent_single`.** Compare this request with the independent, single example. Changing just `dependencyStatus` switches the second stage and adds one required field, `income.parentIncome`.

1. **Stage 1 (root): `stage_statuses`.** This stage requires `dependencyStatus` (allowed values: `dependent`, `independent`) and `maritalStatus` (allowed values: `single`, `married`). This request supplies `"dependent"` and `"single"`, respectively. Both checks return `VALID`.
2. **Follow the transition.** Because both fields passed, the engine calls `application_stage(payload)` in `core/stages.py`. For this request, `"stage_" + "dependent" + "_" + "single"` produces `"stage_dependent_single"`. The engine looks up that exact stage in the graph. [Stage graph and transition function](core/stages.py)
3. **Stage 2: `stage_dependent_single`.** The engine checks each field below in order and collects its result before returning the response.

| Required field | Value in this request | Check result |
| --- | --- | --- |
| `studentInfo.firstName` | `"Jane"` | `VALID` |
| `studentInfo.lastName` | `"Smith"` | `VALID` |
| `studentInfo.dateOfBirth` | `"2003-05-15"` | `VALID` |
| `studentInfo.ssn` | `"123456789"` | `VALID` |
| `income.studentIncome` | `5000` | `VALID` |
| `household.numberInHousehold` | `4` | `VALID` |
| `household.numberInCollege` | `1` | `VALID` |
| `stateOfResidence` | `"CA"` | `VALID` |
| `income.parentIncome` | Omitted | Added to `outstanding` |

**Response.** Every supplied field passed. The omitted fields in the table appear in `outstanding`, so the application is `INCOMPLETE`.

<details>
<summary>Expected output · HTTP 200 OK · INCOMPLETE</summary>

```json
{
  "status": "INCOMPLETE",
  "submitted": [
    {
      "field_name": "dependencyStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "maritalStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.firstName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.lastName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.dateOfBirth",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_student_age",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.ssn",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_ssn_format",
      "severity": "ERROR"
    },
    {
      "field_name": "income.studentIncome",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_non_negative_amount",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInHousehold",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInCollege",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "stateOfResidence",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_state_code",
      "severity": "ERROR"
    }
  ],
  "outstanding": [
    "income.parentIncome"
  ],
  "info": {
    "version": "1.0.0-alpha.1"
  }
}
```

</details>

---

### Change the applicant to married

```sh
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{
    "dependencyStatus": "independent", "maritalStatus": "married",
    "studentInfo": {"firstName":"Jane","lastName":"Smith","dateOfBirth":"2003-05-15","ssn":"123456789"},
    "income": {"studentIncome":5000},
    "household": {"numberInHousehold":4,"numberInCollege":1},
    "stateOfResidence": "CA"
  }'
```

**Stage 1: `stage_statuses` → Stage 2: `stage_independent_married`.** Compare this request with the independent, single example. Changing just `maritalStatus` switches the second stage and makes the spouse’s name and SSN required.

1. **Stage 1 (root): `stage_statuses`.** This stage requires `dependencyStatus` (allowed values: `dependent`, `independent`) and `maritalStatus` (allowed values: `single`, `married`). This request supplies `"independent"` and `"married"`, respectively. Both checks return `VALID`.
2. **Follow the transition.** Because both fields passed, the engine calls `application_stage(payload)` in `core/stages.py`. For this request, `"stage_" + "independent" + "_" + "married"` produces `"stage_independent_married"`. The engine looks up that exact stage in the graph. [Stage graph and transition function](core/stages.py)
3. **Stage 2: `stage_independent_married`.** The engine checks each field below in order and collects its result before returning the response.

| Required field | Value in this request | Check result |
| --- | --- | --- |
| `studentInfo.firstName` | `"Jane"` | `VALID` |
| `studentInfo.lastName` | `"Smith"` | `VALID` |
| `studentInfo.dateOfBirth` | `"2003-05-15"` | `VALID` |
| `studentInfo.ssn` | `"123456789"` | `VALID` |
| `income.studentIncome` | `5000` | `VALID` |
| `household.numberInHousehold` | `4` | `VALID` |
| `household.numberInCollege` | `1` | `VALID` |
| `stateOfResidence` | `"CA"` | `VALID` |
| `spouseInfo.firstName` | Omitted | Added to `outstanding` |
| `spouseInfo.lastName` | Omitted | Added to `outstanding` |
| `spouseInfo.ssn` | Omitted | Added to `outstanding` |

**Response.** Every supplied field passed. The omitted fields in the table appear in `outstanding`, so the application is `INCOMPLETE`.

<details>
<summary>Expected output · HTTP 200 OK · INCOMPLETE</summary>

```json
{
  "status": "INCOMPLETE",
  "submitted": [
    {
      "field_name": "dependencyStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "maritalStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.firstName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.lastName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.dateOfBirth",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_student_age",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.ssn",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_ssn_format",
      "severity": "ERROR"
    },
    {
      "field_name": "income.studentIncome",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_non_negative_amount",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInHousehold",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInCollege",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "stateOfResidence",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_state_code",
      "severity": "ERROR"
    }
  ],
  "outstanding": [
    "spouseInfo.firstName",
    "spouseInfo.lastName",
    "spouseInfo.ssn"
  ],
  "info": {
    "version": "1.0.0-alpha.1"
  }
}
```

</details>

---

### Complete a dependent, married application

```sh
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
```

**Stage 1: `stage_statuses` → Stage 2: `stage_dependent_married`.** Both answers affect the checklist. Being dependent adds parent income. Being married adds spouse details. This applicant supplies both.

1. **Stage 1 (root): `stage_statuses`.** This stage requires `dependencyStatus` (allowed values: `dependent`, `independent`) and `maritalStatus` (allowed values: `single`, `married`). This request supplies `"dependent"` and `"married"`, respectively. Both checks return `VALID`.
2. **Follow the transition.** Because both fields passed, the engine calls `application_stage(payload)` in `core/stages.py`. For this request, `"stage_" + "dependent" + "_" + "married"` produces `"stage_dependent_married"`. The engine looks up that exact stage in the graph. [Stage graph and transition function](core/stages.py)
3. **Stage 2: `stage_dependent_married`.** The engine checks each field below in order and collects its result before returning the response.

| Required field | Value in this request | Check result |
| --- | --- | --- |
| `studentInfo.firstName` | `"Jane"` | `VALID` |
| `studentInfo.lastName` | `"Smith"` | `VALID` |
| `studentInfo.dateOfBirth` | `"2003-05-15"` | `VALID` |
| `studentInfo.ssn` | `"123456789"` | `VALID` |
| `income.studentIncome` | `5000` | `VALID` |
| `household.numberInHousehold` | `4` | `VALID` |
| `household.numberInCollege` | `1` | `VALID` |
| `stateOfResidence` | `"CA"` | `VALID` |
| `income.parentIncome` | `65000` | `VALID` |
| `spouseInfo.firstName` | `"Sam"` | `VALID` |
| `spouseInfo.lastName` | `"Smith"` | `VALID` |
| `spouseInfo.ssn` | `"321456789"` | `VALID` |

**Response.** All required fields in this final stage passed, so the application is `VALID` and `outstanding` is empty.

<details>
<summary>Expected output · HTTP 200 OK · VALID</summary>

```json
{
  "status": "VALID",
  "submitted": [
    {
      "field_name": "dependencyStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "maritalStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.firstName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.lastName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.dateOfBirth",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_student_age",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.ssn",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_ssn_format",
      "severity": "ERROR"
    },
    {
      "field_name": "income.studentIncome",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_non_negative_amount",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInHousehold",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInCollege",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "stateOfResidence",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_state_code",
      "severity": "ERROR"
    },
    {
      "field_name": "income.parentIncome",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_non_negative_amount",
      "severity": "ERROR"
    },
    {
      "field_name": "spouseInfo.firstName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "spouseInfo.lastName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "spouseInfo.ssn",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_ssn_format",
      "severity": "ERROR"
    }
  ],
  "outstanding": [],
  "info": {
    "version": "1.0.0-alpha.1"
  }
}
```

</details>

---

### See failed checks and missing answers together

```sh
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
```

**Stage 1: `stage_statuses` → Stage 2: `stage_dependent_married`.** This applicant gives the same two routing answers as the previous applicant. They reach the same second stage, where several supplied values fail and four required answers are missing.

1. **Stage 1 (root): `stage_statuses`.** This stage requires `dependencyStatus` (allowed values: `dependent`, `independent`) and `maritalStatus` (allowed values: `single`, `married`). This request supplies `"dependent"` and `"married"`, respectively. Both checks return `VALID`.
2. **Follow the transition.** Because both fields passed, the engine calls `application_stage(payload)` in `core/stages.py`. For this request, `"stage_" + "dependent" + "_" + "married"` produces `"stage_dependent_married"`. The engine looks up that exact stage in the graph. [Stage graph and transition function](core/stages.py)
3. **Stage 2: `stage_dependent_married`.** The engine checks each field below in order and collects its result before returning the response.

| Required field | Value in this request | Check result |
| --- | --- | --- |
| `studentInfo.firstName` | `"John"` | `VALID` |
| `studentInfo.lastName` | `"Doe"` | `VALID` |
| `studentInfo.dateOfBirth` | `"2015-01-01"` | `INVALID` — Student must be at least 14 years old. |
| `studentInfo.ssn` | `"invalid"` | `INVALID` — Must be a valid 9-digit Social Security Number. |
| `income.studentIncome` | `-1000` | `INVALID` — Amount cannot be negative. |
| `household.numberInHousehold` | `2` | `VALID` |
| `household.numberInCollege` | `5` | `INVALID` — Number in college cannot exceed number in household. |
| `stateOfResidence` | `"XX"` | `INVALID` — Enter a two-letter US state abbreviation in uppercase. |
| `income.parentIncome` | Omitted | Added to `outstanding` |
| `spouseInfo.firstName` | Omitted | Added to `outstanding` |
| `spouseInfo.lastName` | Omitted | Added to `outstanding` |
| `spouseInfo.ssn` | Omitted | Added to `outstanding` |

**Response.** The engine returns `INVALID` because supplied values failed validation. Their messages appear in `submitted`, and the four omitted fields appear in `outstanding`.

<details>
<summary>Expected output · HTTP 200 OK · INVALID</summary>

```json
{
  "status": "INVALID",
  "submitted": [
    {
      "field_name": "dependencyStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "maritalStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.firstName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.lastName",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_name_length",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.dateOfBirth",
      "status": "INVALID",
      "violation_message": "Student must be at least 14 years old.",
      "rule_name": "validate_student_age",
      "severity": "ERROR"
    },
    {
      "field_name": "studentInfo.ssn",
      "status": "INVALID",
      "violation_message": "Must be a valid 9-digit Social Security Number.",
      "rule_name": "validate_ssn_format",
      "severity": "ERROR"
    },
    {
      "field_name": "income.studentIncome",
      "status": "INVALID",
      "violation_message": "Amount cannot be negative.",
      "rule_name": "validate_non_negative_amount",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInHousehold",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "household.numberInCollege",
      "status": "INVALID",
      "violation_message": "Number in college cannot exceed number in household.",
      "rule_name": "validate_household_count",
      "severity": "ERROR"
    },
    {
      "field_name": "stateOfResidence",
      "status": "INVALID",
      "violation_message": "Enter a two-letter US state abbreviation in uppercase.",
      "rule_name": "validate_state_code",
      "severity": "ERROR"
    }
  ],
  "outstanding": [
    "income.parentIncome",
    "spouseInfo.firstName",
    "spouseInfo.lastName",
    "spouseInfo.ssn"
  ],
  "info": {
    "version": "1.0.0-alpha.1"
  }
}
```

</details>

---

### Send fields before their stage is reached

```sh
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{"dependencyStatus":"independent","stateOfResidence":"CA","favoriteColor":"blue"}'
```

**Stage 1: `stage_statuses`** (only stage reached). The engine cannot select the second stage yet. It can still give the applicant feedback on the state and the unfamiliar field they already sent.

1. **Stage 1 (root): `stage_statuses`.** This stage requires two answers. The first, `dependencyStatus = "independent"`, is an allowed choice and returns `VALID`. The second required field, `maritalStatus`, is missing.
2. **Stop at the root.** The engine adds `maritalStatus` to `outstanding`. It needs both answers to call `application_stage()`, so it stops before selecting the next stage.
3. **Check the other supplied fields.** The catalog recognizes `stateOfResidence = "CA"` and returns `VALID`. It has no entry for `favoriteColor`, so the engine records an `INVALID` result for that field.
4. **Return `INVALID`.** All three supplied fields appear in `submitted`. Only `maritalStatus` appears in `outstanding`.

<details>
<summary>Expected output · HTTP 200 OK · INVALID</summary>

```json
{
  "status": "INVALID",
  "submitted": [
    {
      "field_name": "dependencyStatus",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_choice",
      "severity": "ERROR"
    },
    {
      "field_name": "stateOfResidence",
      "status": "VALID",
      "violation_message": null,
      "rule_name": "validate_state_code",
      "severity": "ERROR"
    },
    {
      "field_name": "favoriteColor",
      "status": "INVALID",
      "violation_message": "Unrecognized application field.",
      "rule_name": null,
      "severity": "ERROR"
    }
  ],
  "outstanding": [
    "maritalStatus"
  ],
  "info": {
    "version": "1.0.0-alpha.1"
  }
}
```

</details>

---

### Send an empty request object

```sh
curl -i http://127.0.0.1:8000/api/v1/fafsa/evaluate \
  -H 'Content-Type: application/json' -d '{}'
```

**Zero stages reached.** FastAPI checks the request body before passing an application to the stage engine. An empty JSON object fails that first check.

1. FastAPI checks the request against `EvaluationRequest`. The empty object supplies neither application fields nor a `cumulative_payload` dictionary. [api/schemas.py](api/schemas.py)
2. FastAPI returns HTTP 422 with a `detail` message before calling the engine. The root stage never runs.

<details>
<summary>Expected output · HTTP 422 Unprocessable Entity</summary>

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "body",
        "cumulative_payload"
      ],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

</details>

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
