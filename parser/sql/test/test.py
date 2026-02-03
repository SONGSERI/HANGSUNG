import sys
from pathlib import Path
from typing import List

# --------------------------------------------------
# 경로 설정
# main.py 기준 → parser
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

DATA_DIR = BASE_DIR / "test/log"
print("BASE_DIR =", BASE_DIR)
print("DATA_DIR =", DATA_DIR)

# --------------------------------------------------
# import
# --------------------------------------------------
from file_name_parser import parse_file_name
from utils import make_hash

from u01_parser import parse_machine_time_summary, parse_stop_information
from u01_lot_parser import parse_lot_time
from u03_parser import (
    parse_pickup_error_summary,
    parse_component_pickup,
)
from pipeline import run_pipeline


# --------------------------------------------------
# 공통 유틸
# --------------------------------------------------
def read_lines(path: Path) -> List[str]:
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.readlines()


def extract_ebr_key(path: Path) -> str:
    """
    파일명에서 EBR 키 추출
    예:
    20260116000000391-05-1-1-3-NAD_H_T_EBR37416101.u01
    → EBR37416101
    """
    for part in path.stem.split("_"):
        if part.startswith("EBR"):
            return part
    return ""


# --------------------------------------------------
# u01 + u03 단일 세트 처리
# --------------------------------------------------
def run_e2e(u01_path: str, u03_path: str):
    print(f"[RUN] {Path(u01_path).name} / {Path(u03_path).name}")

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


# --------------------------------------------------
# test 폴더 전체 실행 (EBR 기준 매칭)
# --------------------------------------------------
def run_all_in_test_dir():
    if not DATA_DIR.exists():
        raise RuntimeError(f"DATA_DIR not found: {DATA_DIR}")

    u01_files = list(DATA_DIR.glob("*.u01"))
    u03_files = list(DATA_DIR.glob("*.u03"))

    if not u01_files:
        print("[INFO] no u01 files found")
        return

    # u03 를 EBR 키로 맵핑
    u03_map = {}
    for p in u03_files:
        key = extract_ebr_key(p)
        if key:
            u03_map[key] = p

    for u01_path in u01_files:
        key = extract_ebr_key(u01_path)

        if not key:
            print(f"[SKIP] EBR key not found in {u01_path.name}")
            continue

        u03_path = u03_map.get(key)

        if not u03_path:
            print(f"[SKIP] u03 not found for EBR={key} ({u01_path.name})")
            continue

        try:
            run_e2e(str(u01_path), str(u03_path))
        except Exception as e:
            # 한 파일 실패해도 전체 중단 안 함
            print(f"[ERROR] EBR={key} : {e}")


# --------------------------------------------------
# entry point
# --------------------------------------------------
if __name__ == "__main__":
    run_all_in_test_dir()
