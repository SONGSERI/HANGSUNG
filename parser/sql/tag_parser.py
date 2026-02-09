# tag_parser.py
# 태그 관련 데이터 파싱/정규화

from typing import Dict, Iterable, List, Optional

from utils import make_hash, parse_bool


def _require(value: Optional[str], label: str) -> str:
    if value is None or str(value).strip() == "":
        raise ValueError(f"{label} is required for tag parsing.")
    return str(value).strip()


def normalize_tag_categories(rows: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    normalized: List[Dict[str, object]] = []

    for row in rows:
        name = row.get("tag_category_name") or row.get("category_name")
        name = _require(name, "tag_category_name")
        parent_id = row.get("parent_category_id")

        tag_category_id = row.get("tag_category_id") or make_hash(name, parent_id or "")
        normalized.append(
            {
                "tag_category_id": tag_category_id,
                "tag_category_name": name,
                "parent_category_id": parent_id,
                "description": row.get("description"),
            }
        )

    return normalized


def normalize_tag_infos(rows: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    normalized: List[Dict[str, object]] = []

    for row in rows:
        tag_name = _require(row.get("tag_name"), "tag_name")
        tag_category_id = _require(row.get("tag_category_id"), "tag_category_id")
        machine_id = row.get("machine_id")

        tag_id = row.get("tag_id") or make_hash(tag_name, tag_category_id, machine_id or "")
        normalized.append(
            {
                "tag_id": tag_id,
                "tag_name": tag_name,
                "tag_category_id": tag_category_id,
                "machine_id": machine_id,
                "data_type": row.get("data_type"),
                "unit": row.get("unit"),
                "source_system": row.get("source_system"),
                "is_active": parse_bool(row.get("is_active"), default=True),
                "description": row.get("description"),
            }
        )

    return normalized


def normalize_tag_specs(rows: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    normalized: List[Dict[str, object]] = []

    for row in rows:
        tag_id = _require(row.get("tag_id"), "tag_id")
        spec_type = _require(row.get("spec_type"), "spec_type")
        effective_from = row.get("effective_from")
        effective_to = row.get("effective_to")

        tag_spec_id = row.get("tag_spec_id") or make_hash(
            tag_id, spec_type, effective_from or "", effective_to or ""
        )

        spec_value = row.get("spec_value")
        if spec_value is not None:
            spec_value = float(spec_value)

        normalized.append(
            {
                "tag_spec_id": tag_spec_id,
                "tag_id": tag_id,
                "spec_type": spec_type,
                "spec_value": spec_value,
                "effective_from": effective_from,
                "effective_to": effective_to,
            }
        )

    return normalized


def normalize_tag_realtime(rows: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    normalized: List[Dict[str, object]] = []

    for row in rows:
        tag_id = _require(row.get("tag_id"), "tag_id")
        recorded_at = _require(row.get("recorded_at"), "recorded_at")
        tag_value = row.get("tag_value")
        if tag_value is not None:
            tag_value = float(tag_value)

        machine_id = row.get("machine_id")
        tag_data_id = row.get("tag_data_id") or make_hash(tag_id, machine_id or "", recorded_at)

        normalized.append(
            {
                "tag_data_id": tag_data_id,
                "tag_id": tag_id,
                "machine_id": machine_id,
                "recorded_at": recorded_at,
                "tag_value": tag_value,
                "quality_flag": row.get("quality_flag"),
                "source_file_id": row.get("source_file_id"),
            }
        )

    return normalized
