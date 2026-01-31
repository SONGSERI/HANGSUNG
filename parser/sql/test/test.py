from pathlib import Path

from file_name_parser import parse_file_name
from utils import make_hash
from u01_parser import parse_machine_time_summary, parse_stop_information
from u01_lot_parser import parse_lot_time
from u03_parser import (
    parse_pickup_error_summary,
    parse_component_pickup,
)
from pipeline import run_pipeline


def read_lines(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.readlines()


def run_e2e(u01_path: str, u03_path: str):
    # ---------- u01 ----------
    u01_meta = parse_file_name(u01_path)
    u01_lines = read_lines(Path(u01_path))

    file_id = make_hash(u01_meta["file_name"])
    lot_id = make_hash(u01_meta["lot_name"])
    machine_id = make_hash(
        u01_meta["line_id"],
        u01_meta["stage_no"],
        u01_meta["machine_order"],
    )
    lot_machine_id = make_hash(lot_id, machine_id)

    file_row = {
        "file_id": file_id,
        **u01_meta,
    }

    lot_time = parse_lot_time(u01_lines)
    lot_row = {
        "lot_id": lot_id,
        "lot_name": u01_meta["lot_name"],
        **lot_time,
        "lane": None,
    }

    machine_row = {
        "machine_id": machine_id,
        "line_id": u01_meta["line_id"],
        "stage_no": u01_meta["stage_no"],
        "machine_order": u01_meta["machine_order"],
    }

    lot_machine_row = {
        "lot_machine_id": lot_machine_id,
        "lot_id": lot_id,
        "machine_id": machine_id,
    }

    mts_row = parse_machine_time_summary(u01_lines)
    stop_logs = parse_stop_information(
        u01_lines,
        file_id=file_id,
        lot_machine_id=lot_machine_id,
    )

    # ---------- u03 ----------
    u03_meta = parse_file_name(u03_path)
    u03_lines = read_lines(Path(u03_path))

    pickup_summary = parse_pickup_error_summary(u03_lines)
    pickup_summary["lot_machine_id"] = lot_machine_id

    components, component_summaries = parse_component_pickup(
        u03_lines,
        machine_id=machine_id,
        lot_machine_id=lot_machine_id,
        file_id=file_id,
    )

    # ---------- DB INSERT ----------
    run_pipeline(
        file_row=file_row,
        lot_row=lot_row,
        machine_row=machine_row,
        lot_machine_row=lot_machine_row,
        mts_row=mts_row,
        stop_logs=stop_logs,
        pickup_summary=pickup_summary,
        components=components,
        component_summaries=component_summaries,
    )


if __name__ == "__main__":
    run_e2e(
        "test/sample_u01.u01",
        "test/sample_u03.u03",
    )
