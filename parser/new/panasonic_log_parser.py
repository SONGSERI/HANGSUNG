#!/usr/bin/env python3
"""Parse Panasonic SMT log files and emit PostgreSQL INSERT statements.

Usage examples:
  python panasonic_log_parser.py --input log/20260115 --limit-files 5 --sql-out out.sql
  python panasonic_log_parser.py --input log/20260115/20260115000002631-10-1-1-3-NAD_H_T_EBR44653201.u01 --sql-out out.sql
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import sys
from typing import Dict, List, Tuple, Any, Iterable

SECTION_HEADER_RE = re.compile(r"^\[(.+)\]\s*$")
FILE_TS_RE = re.compile(r"^(\d{17})-")
INDEX_DATE_RE = re.compile(r"^(\d{4})/(\d{2})/(\d{2}),(\d{2}):(\d{2}):(\d{2})$")

# Known sections we treat as KV for convenient mapping (others are still stored generically)
KNOWN_KV_SECTIONS = {
    "Index",
    "Information",
    "Time",
    "CycleTime",
    "Count",
    "InspectionData",
    "BRecg",
    "BRecgCalc",
    "ElapseTimeRecog",
    "SBoard",
    "HeightCorrect",
}

REPORT_INFO_COLUMNS = {
    "stage",
    "lane",
    "serial",
    "serialstatus",
    "code",
    "bcrstatus",
    "productid",
    "rev",
    "planid",
    "output",
    "lotname",
    "lotnumber",
    "masterwo",
    "subwo",
}


def parse_index_datetime(value: str) -> dt.datetime | None:
    m = INDEX_DATE_RE.match(value)
    if not m:
        return None
    y, mo, d, hh, mm, ss = map(int, m.groups())
    return dt.datetime(y, mo, d, hh, mm, ss)


def parse_file_timestamp_from_name(file_name: str) -> dt.datetime | None:
    m = FILE_TS_RE.match(file_name)
    if not m:
        return None
    raw = m.group(1)  # yyyymmddHHMMSSmmm
    try:
        y = int(raw[0:4])
        mo = int(raw[4:6])
        d = int(raw[6:8])
        hh = int(raw[8:10])
        mm = int(raw[10:12])
        ss = int(raw[12:14])
        ms = int(raw[14:17])
        return dt.datetime(y, mo, d, hh, mm, ss, ms * 1000)
    except ValueError:
        return None


def normalize_key(key: str) -> str:
    key = key.strip()
    key = re.sub(r"[^A-Za-z0-9]+", "_", key)
    key = re.sub(r"_+", "_", key)
    return key.strip("_").lower()


def shlex_split(line: str) -> List[str]:
    # Use shlex to preserve quoted strings and handle empty strings
    try:
        return shlex.split(line, posix=True)
    except ValueError:
        # Fallback: split on whitespace
        return line.split()


def clean_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def parse_log_file(path: str) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, Any]]]:
    """Return (kv_sections, table_sections).

    kv_sections: section -> {key: value}
    table_sections: section -> {"columns": [...], "rows": [[...], ...]}
    """
    kv_sections: Dict[str, Dict[str, str]] = {}
    table_sections: Dict[str, Dict[str, Any]] = {}

    current_section: str | None = None
    mode: str | None = None  # "kv" or "table"
    table_columns: List[str] | None = None
    table_rows: List[List[str]] | None = None

    def finalize_section() -> None:
        nonlocal current_section, mode, table_columns, table_rows
        if current_section and mode == "table" and table_columns is not None:
            table_sections[current_section] = {
                "columns": table_columns,
                "rows": table_rows or [],
            }
        current_section = None
        mode = None
        table_columns = None
        table_rows = None

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            m = SECTION_HEADER_RE.match(line)
            if m:
                finalize_section()
                current_section = m.group(1)
                # Pre-create kv store for known sections for stable order
                if current_section in KNOWN_KV_SECTIONS:
                    kv_sections[current_section] = {}
                continue

            if current_section is None:
                # Skip any leading garbage
                continue

            if mode is None:
                if "=" in line:
                    mode = "kv"
                else:
                    mode = "table"

            if mode == "kv":
                if "=" not in line:
                    # Defensive: treat as header-less table line
                    cols = shlex_split(line)
                    if cols:
                        table_columns = cols
                        table_rows = []
                        mode = "table"
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = clean_value(value)
                kv_sections.setdefault(current_section, {})[key] = value
            else:
                if table_columns is None:
                    table_columns = [clean_value(v) for v in shlex_split(line)]
                    table_rows = []
                else:
                    row = [clean_value(v) for v in shlex_split(line)]
                    table_rows.append(row)

    finalize_section()
    return kv_sections, table_sections


def report_id_for_path(path: str) -> str:
    h = hashlib.sha1(os.path.abspath(path).encode("utf-8")).hexdigest()
    # represent as UUID-like string for readability
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dt.datetime):
        return "'" + value.isoformat(sep=" ") + "'"
    if isinstance(value, dt.date):
        return "'" + value.isoformat() + "'"
    if isinstance(value, (dict, list)):
        return "'" + json.dumps(value, ensure_ascii=False) .replace("'", "''") + "'::jsonb"
    s = str(value)
    return "'" + s.replace("'", "''") + "'"


def build_inserts_for_file(path: str) -> List[str]:
    kv_sections, table_sections = parse_log_file(path)
    report_id = report_id_for_path(path)

    file_path = os.path.abspath(path)
    file_name = os.path.basename(path)
    file_dir = os.path.basename(os.path.dirname(path))
    file_ext = os.path.splitext(file_name)[1].lstrip(".")
    file_ts = parse_file_timestamp_from_name(file_name)

    index = kv_sections.get("Index", {})
    info = kv_sections.get("Information", {})

    index_date = parse_index_datetime(index.get("Date", ""))

    inserts: List[str] = []

    # report
    report_cols = [
        "report_id",
        "file_path",
        "file_name",
        "file_dir",
        "file_ext",
        "file_ts",
        "format",
        "version",
        "machine",
        "report_dt",
        "author_type",
        "author",
        "diff",
        "mjsid",
        "comment",
    ]
    report_vals = [
        report_id,
        file_path,
        file_name,
        file_dir,
        file_ext,
        file_ts,
        index.get("Format"),
        index.get("Version"),
        index.get("Machine"),
        index_date,
        index.get("AuthorType"),
        index.get("Author"),
        index.get("Diff"),
        index.get("MJSID"),
        index.get("Comment"),
    ]
    inserts.append(
        "INSERT INTO report (" + ",".join(report_cols) + ") VALUES (" + ",".join(sql_literal(v) for v in report_vals) + ");"
    )

    # report_info (only if present)
    if info:
        info_cols = ["report_id"]
        info_vals = [report_id]
        for k, v in info.items():
            nk = normalize_key(k)
            if nk not in REPORT_INFO_COLUMNS:
                continue
            info_cols.append(nk)
            info_vals.append(v)
        inserts.append(
            "INSERT INTO report_info (" + ",".join(info_cols) + ") VALUES (" + ",".join(sql_literal(v) for v in info_vals) + ");"
        )

    # kv sections (generic)
    for section_name, data in kv_sections.items():
        inserts.append(
            "INSERT INTO report_kv_sections (report_id, section_name, data) VALUES ("
            + ",".join(
                [
                    sql_literal(report_id),
                    sql_literal(section_name),
                    sql_literal(data),
                ]
            )
            + ");"
        )

    # table sections
    for section_name, table in table_sections.items():
        columns = table.get("columns") or []
        rows = table.get("rows") or []

        inserts.append(
            "INSERT INTO report_table_sections (report_id, section_name, columns) VALUES ("
            + ",".join(
                [
                    sql_literal(report_id),
                    sql_literal(section_name),
                    sql_literal(columns),
                ]
            )
            + ");"
        )

        for idx, row in enumerate(rows):
            row_obj = {}
            for i, col in enumerate(columns):
                key = col
                row_obj[key] = row[i] if i < len(row) else None
            inserts.append(
                "INSERT INTO report_table_rows (report_id, section_name, row_index, data) VALUES ("
                + ",".join(
                    [
                        sql_literal(report_id),
                        sql_literal(section_name),
                        sql_literal(idx),
                        sql_literal(row_obj),
                    ]
                )
                + ");"
            )

    return inserts


def iter_files(input_path: str, limit_files: int | None) -> Iterable[str]:
    if os.path.isdir(input_path):
        files = []
        for root, _, names in os.walk(input_path):
            for n in names:
                if n.startswith("."):
                    continue
                files.append(os.path.join(root, n))
        files.sort()
        if limit_files is not None:
            files = files[:limit_files]
        for p in files:
            yield p
    else:
        yield input_path


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="File or directory")
    parser.add_argument("--limit-files", type=int, default=None, help="Limit number of files when input is a directory")
    parser.add_argument("--sql-out", required=True, help="Output .sql file path")
    args = parser.parse_args(argv)

    out_lines: List[str] = []
    for path in iter_files(args.input, args.limit_files):
        out_lines.extend(build_inserts_for_file(path))

    with open(args.sql_out, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
        f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
