"""Published videos and concepts already chosen but not yet rendered."""

import json
from pathlib import Path


EMPTY = {"videos": [], "unpublished_selections": []}


def load(path: Path) -> dict:
    if not path.exists():
        return {"videos": [], "unpublished_selections": []}
    data = json.loads(path.read_text())
    data.setdefault("videos", [])
    data.setdefault("unpublished_selections", [])
    return data


def save(path: Path, catalog: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2) + "\n")


def active_hold(catalog: dict) -> dict | None:
    holds = [item for item in catalog["unpublished_selections"] if item.get("status") != "abandoned"]
    if not holds:
        return None
    return holds[-1]


def hold_concept(catalog: dict, concept_id: str, date: str, title: str, status: str) -> None:
    catalog["unpublished_selections"] = [
        item for item in catalog["unpublished_selections"] if item.get("concept_id") != concept_id
    ]
    catalog["unpublished_selections"].append(
        {
            "concept_id": concept_id,
            "date_selected": date,
            "title": title,
            "status": status,
        }
    )
