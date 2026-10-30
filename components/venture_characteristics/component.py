"""Plan task 5.1: the ventures' characteristics from the applications sheet
(design, A5), as indicators. Only the form's fixed choices are used; the one
free-text answer used, the type of legal entity, is reduced to a few
categories, and its text is not kept."""

import re

import pandas as pd


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def options(value) -> list[str]:
    return [p.strip() for p in re.split(r"\s*\|\s*", value) if p.strip()] if isinstance(value, str) else []


def present(value) -> bool:
    return value is not None and not (isinstance(value, float) and value != value)


def entity(value) -> str:
    if not isinstance(value, str) or not value.strip():
        return "none_stated"
    text = value.lower()
    if re.search(r"\bllc\b", text):
        return "llc"
    if re.search(r"\bs[- ]?corp", text):
        return "s_corporation"
    if re.search(r"c[- ]?corp|corporation|\binc\b", text):
        return "c_corporation"
    return "other"


def run(inputs: dict, settings: dict) -> dict:
    e = pd.DataFrame(inputs["entries"])
    fields_count = pd.Series([f for v in e["fields"] for f in options(v)]).value_counts()
    common_fields = sorted(fields_count[fields_count >= settings["min_entries_per_field"]].index)
    rows = []
    for r in e.itertuples():
        products, fields, milestones = options(r.product_type), options(r.fields), options(r.milestones)
        row = {"entry": r.entry,
               "internet_consumer_tech": r.company_type == settings["internet_company_type"] if isinstance(r.company_type, str) else None,
               "entity_formed": bool(r.entity_formed) if present(r.entity_formed) else None,
               "entity_category": entity(r.entity_type), "has_website": bool(r.has_website) if present(r.has_website) else None,
               "product_types": len(products), "fields_tagged": len(fields), "milestones_reached": len(milestones)}
        row |= {f"product_{slug(p)}": p in products for p in settings["product_types"]}
        row |= {f"milestone_{slug(m)}": m in milestones for m in settings["milestones"]}
        row |= {f"field_{slug(f)}": f in fields for f in common_fields}
        rows.append(row)
    return {"characteristics": sorted(rows, key=lambda x: x["entry"]), "common_fields": common_fields}
