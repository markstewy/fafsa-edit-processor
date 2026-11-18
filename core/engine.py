"""Evaluate a cumulative application with the configured stages and rules."""

from functools import lru_cache
from importlib import import_module
from pathlib import Path

import yaml

from core.stages import STAGE_GRAPH


# Rules stay fixed for a release, so parse the YAML once per worker.
@lru_cache(maxsize=1)
def _load_rules_catalog():
    with Path(__file__).with_name("rule_field_catalog.yaml").open() as stream:
        catalog = yaml.safe_load(stream)
    for rule in catalog["rules"].values():
        module, name = rule["module"].split(":")
        rule["function"] = getattr(import_module(module), name)
    return catalog


def _evaluate_field(field, payload, catalog):
    results = []
    for binding in catalog["fields"].get(field, []):
        rule_name = binding["rule"]
        rule = catalog["rules"][rule_name]
        params = {**rule.get("params", {}), **binding.get("params", {})}
        for param, source in binding.get("inputs", {}).items():
            params[param] = payload.get(source)
        valid, message = rule["function"](payload[field], params)
        results.append({
            "field_name": field,
            "status": "VALID" if valid else "INVALID",
            "violation_message": None if valid else message,
            "rule_name": rule_name,
            "severity": rule["severity"],
        })
    if not results:
        results.append({
            "field_name": field, "status": "INVALID", "rule_name": None,
            "severity": "ERROR", "violation_message": "Unrecognized application field.",
        })
    return results


def evaluate_fafsa_payload(cumulative_payload: dict) -> dict:
    catalog = _load_rules_catalog()
    evaluated = {}
    outstanding = []
    stage_id = STAGE_GRAPH["root_stage"]
    while stage_id:
        stage = STAGE_GRAPH["stages"][stage_id]
        blocked = False
        for field in stage["required_fields"]:
            if field not in cumulative_payload:
                outstanding.append(field)
                blocked = True
                continue
            evaluated[field] = _evaluate_field(field, cumulative_payload, catalog)
            if any(result["status"] == "INVALID" for result in evaluated[field]):
                blocked = True
        transition = stage.get("transition")
        if blocked or transition is None:
            break
        stage_id = transition(cumulative_payload)

    # Validate submitted fields even before their stage is reached.
    for field in cumulative_payload:
        if field not in evaluated:
            evaluated[field] = _evaluate_field(field, cumulative_payload, catalog)
    submitted = [result for results in evaluated.values() for result in results]
    status = "INCOMPLETE" if outstanding else "VALID"
    if any(result["status"] == "INVALID" for result in submitted):
        status = "INVALID"
    return {"status": status, "submitted": submitted, "outstanding": outstanding,
            "info": {"version": "1.0.0-alpha.1"}}
