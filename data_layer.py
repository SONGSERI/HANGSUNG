import csv
import io
import os
import re
import tarfile
from datetime import datetime, timedelta
from collections import defaultdict
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
from sqlalchemy import create_engine, text


RAW_LOAD_SPECS = {
    "fa_26_34_mounter_hdr": {
        "cols": ["plant_cd", "wc_cd", "file_nm", "make_dt", "post_flag"],
        "date_cols": ["make_dt"],
        "order_cols": ["make_dt", "file_nm"],
    },
    "fa_26_34_mounter_dtl": {
        "cols": ["plant_cd", "wc_cd", "file_nm", "file_dt", "mach_cd", "stage", "lane", "output", "lot_nm", "section", "row_num", "item", "result", "make_dt"],
        "date_cols": ["file_dt", "make_dt"],
        "order_cols": ["file_dt", "make_dt", "file_nm"],
    },
}

BACKUP_ARCHIVE_PATH = os.path.join(os.path.dirname(__file__), "db", "nexedge")

BACKUP_TABLE_COLUMNS = {
    "machine": ["machine_hash", "machine_code", "line_no", "stage_no"],
    "lot": ["lot_hash", "lot_name", "col3", "col4", "lot_order"],
    "lot_machine": ["lot_machine_hash", "lot_hash", "machine_hash"],
    "file": ["file_hash", "file_name", "file_date", "file_time", "machine_code", "line_no", "stage_no", "machine_order", "lot_name", "workcode"],
    "file_lot_machine": ["file_hash", "lot_machine_hash"],
    "stop_reason": ["stop_reason_code", "stop_reason_name", "stop_reason_group"],
    "tag_category": ["category_hash", "category_name", "parent_hash", "description"],
    "tag_info": ["tag_hash", "tag_name", "category_hash", "parent_hash", "value_type", "unused", "scope", "active", "description"],
    "tag_spec": ["spec_hash", "spec_value_1", "spec_value_2", "spec_value_3"],
}

BACKUP_STOP_SUFFIXES = {
    "TotalStop",
    "Idle",
    "SCEStop",
    "CDErr",
    "CTErr",
    "TRSErr",
    "PRDStop",
    "JudgeStop",
    "BNDStop",
    "BRcgStop",
    "BNDRcgStop",
    "OthrStop",
    "OtherLStop",
    "PPIStop",
    "CnvStop",
    "SCStop",
    "MHRcgStop",
    "FBStop",
    "Trbl",
    "Bwait",
    "Cwait",
    "Fwait",
    "Pwait",
    "Rwait",
    "Swait",
    "McFwait",
    "McRwait",
    "JointPassWait",
}

BACKUP_INSPECTION_PREFIX = "InspectionData."

BACKUP_OUTPUT_TAGS = {
    "Information.Output",
    "Count.Board",
    "Count.Module",
    "Count.LotBoard",
    "Count.LotModule",
    "Count.OKParts",
    "Information.OKParts",
    "InspectionData.OKParts",
    "InspectionData.LotOKParts",
}


@lru_cache(maxsize=1)
def get_engine():
    user = os.getenv("PGUSER", "analysis")
    password = os.getenv("PGPASSWORD", "analysis1!")
    host = os.getenv("PGHOST", "192.168.200.105")
    port = os.getenv("PGPORT", "5432")
    db = os.getenv("PGDATABASE", "nexedge")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}?connect_timeout=5"
    return create_engine(url, pool_pre_ping=True)


def _table_exists(conn, name: str) -> bool:
    for candidate in (name, name.lower(), f'"{name}"'):
        if conn.execute(text("select to_regclass(:n)"), {"n": candidate}).scalar_one() is not None:
            return True
    return False


def _read_table(conn, name: str, cols: List[str] = None, date_cols: List[str] = None, start_ts=None, limit: int = None, order_cols: List[str] = None) -> pd.DataFrame:
    actual = None
    for candidate in (name, name.lower(), f'"{name}"'):
        resolved = conn.execute(text("select to_regclass(:n)"), {"n": candidate}).scalar_one()
        if resolved is not None:
            actual = str(resolved).strip('"')
            break
    if not actual:
        return pd.DataFrame()
    csql = text("""
        select attname
        from pg_attribute
        where attrelid = to_regclass(:t)
          and attnum > 0
          and not attisdropped
    """)
    available = {r[0].lower() for r in conn.execute(csql, {"t": actual}).fetchall()}
    if cols is None:
        use = [c for c in available]
    else:
        use = [c for c in cols if c.lower() in available]
    if not use:
        return pd.DataFrame()
    select_cols = ", ".join([f'"{c}"' for c in use])
    where_clause = ""
    params = {}
    if start_ts is not None and date_cols:
        usable_dates = [c for c in date_cols if c.lower() in available]
        if usable_dates:
            if len(usable_dates) == 1:
                where_clause = f' WHERE "{usable_dates[0]}" >= :start_ts'
            else:
                date_expr = ", ".join([f'"{c}"' for c in usable_dates])
                where_clause = f" WHERE COALESCE({date_expr}) >= :start_ts"
            params["start_ts"] = start_ts
    order_clause = ""
    if order_cols:
        usable_order = [c for c in order_cols if c.lower() in available]
        if usable_order:
            order_clause = " ORDER BY " + ", ".join([f'"{c}" DESC' for c in usable_order])
    limit_clause = f" LIMIT {int(limit)}" if limit else ""
    sql = text(f'SELECT {select_cols} FROM "{actual}"{where_clause}{order_clause}{limit_clause}')
    df = pd.read_sql(sql, conn, params=params)
    df.columns = [c.lower() for c in df.columns]
    return df


def _period_start(period: str):
    if period == "최근 7일":
        return pd.Timestamp.now().normalize() - pd.Timedelta(days=6)
    if period == "최근 30일":
        return pd.Timestamp.now().normalize() - pd.Timedelta(days=29)
    return None


def _period_limit(period: str) -> int:
    if period == "최근 7일":
        return 5000
    if period == "최근 30일":
        return 10000
    return 20000


def _backup_period_range(period: str):
    if period == "최근 7일":
        end = pd.Timestamp.now().normalize()
        return end - pd.Timedelta(days=6), end
    if period == "최근 30일":
        end = pd.Timestamp.now().normalize()
        return end - pd.Timedelta(days=29), end
    return None, None


def _parse_backup_row(line: str) -> List[str] | None:
    line = line.strip()
    if not line or "VALUES" not in line:
        return None
    m = re.search(r"VALUES\s*\((.*)\);\s*$", line)
    if not m:
        return None
    row = next(csv.reader(io.StringIO(m.group(1)), delimiter=",", quotechar="'", escapechar="\\", skipinitialspace=True))
    return [None if str(v) == "NULL" else v for v in row]


def _read_backup_table(tar: tarfile.TarFile, member_name: str, columns: List[str]) -> pd.DataFrame:
    try:
        member = tar.getmember(member_name)
    except KeyError:
        return pd.DataFrame(columns=columns)
    f = tar.extractfile(member)
    if f is None:
        return pd.DataFrame(columns=columns)
    rows: List[List[Any]] = []
    for raw_line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
        parsed = _parse_backup_row(raw_line)
        if parsed is None:
            continue
        rows.append(parsed)
    if not rows:
        return pd.DataFrame(columns=columns)
    max_cols = max(len(r) for r in rows)
    cols = columns[:max_cols] + [f"col_{idx}" for idx in range(len(columns) + 1, max_cols + 1)] if max_cols > len(columns) else columns[:max_cols]
    frame = pd.DataFrame(rows, columns=cols)
    frame.columns = [str(c).lower() for c in frame.columns]
    return frame


def _read_backup_rows(tar: tarfile.TarFile, member_name: str) -> Iterable[List[Any]]:
    try:
        member = tar.getmember(member_name)
    except KeyError:
        return []
    f = tar.extractfile(member)
    if f is None:
        return []
    for raw_line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
        parsed = _parse_backup_row(raw_line)
        if parsed is None:
            continue
        yield parsed


def _parse_backup_datetime(date_value: Any, time_value: Any = None) -> pd.Timestamp:
    date_text = "" if date_value is None else str(date_value).strip()
    time_text = "" if time_value is None else str(time_value).strip()
    if not date_text:
        return pd.NaT
    try:
        if time_text and re.fullmatch(r"\d{3,6}", time_text):
            padded = time_text.zfill(6)
            return pd.Timestamp(
                datetime(
                    int(date_text[0:4]),
                    int(date_text[5:7]),
                    int(date_text[8:10]),
                    int(padded[0:2]),
                    int(padded[2:4]),
                    int(padded[4:6]),
                )
            )
        try:
            return pd.Timestamp(datetime.fromisoformat(date_text))
        except Exception:
            return pd.Timestamp(datetime.strptime(date_text, "%Y-%m-%d"))
    except Exception:
        return pd.NaT


def _parse_backup_filename_datetime(file_name: Any) -> pd.Timestamp:
    text = str(file_name or "").strip()
    if not text:
        return pd.NaT
    m = re.match(r"^(\d{14})(\d{0,3})", text)
    if not m:
        return pd.NaT
    try:
        base = datetime.strptime(m.group(1), "%Y%m%d%H%M%S")
        ms = int(m.group(2) or 0)
        return pd.Timestamp(base) + pd.Timedelta(milliseconds=ms)
    except Exception:
        return pd.NaT


def _backup_machine_code(machine_hash: Any, machine_map: Dict[str, Dict[str, Any]]) -> str:
    row = machine_map.get(str(machine_hash), {})
    return str(row.get("machine_code") or row.get("machine_hash") or machine_hash or "-")


def _backup_lot_name(lot_hash: Any, lot_map: Dict[str, Dict[str, Any]]) -> str:
    row = lot_map.get(str(lot_hash), {})
    return str(row.get("lot_name") or row.get("lot_hash") or lot_hash or "-")


def _backup_line_label(value: Any) -> str:
    txt = str(value or "").strip()
    if not txt or txt.lower() == "nan":
        return "-"
    if txt.lower().startswith("line"):
        return txt
    if txt.isdigit():
        return f"Line-{txt}"
    return txt


def _backup_reason_code(tag_name: str) -> str:
    suffix = str(tag_name or "").split(".")[-1]
    if suffix.startswith("Time") and "." in str(tag_name or ""):
        return str(tag_name).split(".")[-1]
    return suffix or "UNKNOWN"


def _backup_stop_reason_from_tag(tag_name: str) -> bool:
    text = str(tag_name or "")
    suffix = text.split(".")[-1]
    return any(token in text for token in ["Stop", "WAIT", "Wait", "Err", "Error", "Idle"]) or suffix in BACKUP_STOP_SUFFIXES


def _backup_event_class(tag_name: str, category_name: str, value: Any) -> str:
    text = " ".join([str(tag_name or ""), str(category_name or ""), str(value or "")])
    if str(tag_name or "").startswith(BACKUP_INSPECTION_PREFIX):
        return "INSPECTION"
    if any(k in text.upper() for k in ["SETUP", "CHANGEOVER", "TEACH", "CALIB", "INITIAL"]):
        return "SETUP"
    if any(k in text.upper() for k in ["FEEDER", "FDR", "REEL", "SUPPLY", "FEED"]):
        return "FEEDER_ERROR"
    if any(k in text.upper() for k in ["PICKUP", "SUCTION", "NOZZLE", "VACUUM"]):
        return "PICKUP_ERROR"
    if any(k in text.upper() for k in ["RECOG", "RECOGN", "VISION", "MARK", "ALIGN", "CAMERA"]):
        return "RECOG_ERROR"
    if any(k in text.upper() for k in ["PLACE", "PLACEMENT", "INSERT", "POSITION"]):
        return "PLACE_ERROR"
    if any(k in text.upper() for k in ["TRANSFER", "CONVEYOR", "BUFFER", "INTERLOCK"]):
        return "TRANSFER_ERROR"
    if any(k in text.upper() for k in ["WAIT_PRE", "WAIT_POST", "WAIT BEFORE", "WAIT AFTER", "UPSTREAM WAIT", "DOWNSTREAM WAIT"]):
        return "WAIT"
    if any(k in text.upper() for k in ["STOP", "ERR", "ERROR", "ALARM", "FAIL", "NG"]):
        return "STOP"
    if str(category_name or "").lower() == "inspectiondata":
        return "INSPECTION"
    if str(category_name or "").lower() in {"time", "count"}:
        return "FLOW"
    if str(category_name or "").lower() == "information":
        return "META"
    return "OTHER"


def _build_backup_raw_data(period: str = "전체") -> Dict[str, pd.DataFrame]:
    if not os.path.exists(BACKUP_ARCHIVE_PATH):
        return {}

    start_ts, end_ts = _backup_period_range(period)
    with tarfile.open(BACKUP_ARCHIVE_PATH, "r") as tar:
        restore_sql = tar.extractfile("restore.sql")
        if restore_sql is None:
            return {}
        restore_text = restore_sql.read().decode("utf-8", errors="replace")
        member_map: Dict[str, str] = {}
        current_table = None
        for line in restore_text.splitlines():
            m = re.match(r"-- Data for Name: ([^;]+); Type: TABLE DATA; Schema: public; Owner: .*", line)
            if m:
                current_table = m.group(1).strip()
                continue
            m = re.match(r"\\i \$\$PATH\$\$/(\d+\.dat)", line.strip())
            if m and current_table:
                member_map[current_table] = m.group(1)
                current_table = None

        small_tables = {
            name: _read_backup_table(tar, member_map.get(name, ""), cols)
            for name, cols in {
                "machine": BACKUP_TABLE_COLUMNS["machine"],
                "lot": BACKUP_TABLE_COLUMNS["lot"],
                "lot_machine": BACKUP_TABLE_COLUMNS["lot_machine"],
                "file": BACKUP_TABLE_COLUMNS["file"],
                "file_lot_machine": BACKUP_TABLE_COLUMNS["file_lot_machine"],
            }.items()
        }

        machine = small_tables.get("machine", pd.DataFrame()).copy()
        lot = small_tables.get("lot", pd.DataFrame()).copy()
        lot_machine = small_tables.get("lot_machine", pd.DataFrame()).copy()
        file_df = small_tables.get("file", pd.DataFrame()).copy()
        file_lot_machine = small_tables.get("file_lot_machine", pd.DataFrame()).copy()

        for df in [machine, lot, lot_machine, file_df, file_lot_machine]:
            if not df.empty:
                df.columns = [c.lower() for c in df.columns]

        machine_map = {}
        if not machine.empty:
            for _, r in machine.iterrows():
                machine_map[str(r.get("machine_hash"))] = {
                    "machine_hash": r.get("machine_hash"),
                    "machine_code": r.get("machine_code"),
                    "line_no": r.get("line_no"),
                    "stage_no": r.get("stage_no"),
                }

        lot_map = {}
        if not lot.empty:
            for _, r in lot.iterrows():
                lot_map[str(r.get("lot_hash"))] = {
                    "lot_hash": r.get("lot_hash"),
                    "lot_name": r.get("lot_name"),
                    "lot_order": r.get("lot_order"),
                }

        lot_machine_id_map = {}
        if not lot_machine.empty:
            for _, r in lot_machine.iterrows():
                lot_hash = str(r.get("lot_hash"))
                machine_hash = str(r.get("machine_hash"))
                lot_machine_id = str(r.get("lot_machine_hash"))
                lot_name = _backup_lot_name(lot_hash, lot_map)
                machine_code = _backup_machine_code(machine_hash, machine_map)
                line_id = _backup_line_label(machine_map.get(machine_hash, {}).get("line_no"))
                stage_no = machine_map.get(machine_hash, {}).get("stage_no")
                lot_machine_id_map[lot_machine_id] = {
                    "lot_machine_id": lot_machine_id,
                    "lot_id": lot_name,
                    "machine_id": machine_code,
                    "line_id": line_id,
                    "stage_no": stage_no,
                    "machine_order": stage_no,
                }

        file_rows = []
        for r in file_df.itertuples(index=False):
            file_hash = str(getattr(r, "file_hash", ""))
            file_nm = getattr(r, "file_name", None)
            event_ts = _parse_backup_datetime(getattr(r, "file_date", None), getattr(r, "file_time", None))
            if pd.isna(event_ts):
                event_ts = _parse_backup_filename_datetime(file_nm)
            if pd.notna(event_ts) and start_ts is not None and end_ts is not None:
                event_day = pd.Timestamp(event_ts).normalize()
                if event_day < start_ts or event_day > end_ts:
                    continue
            machine_code = str(getattr(r, "machine_code", "-") or "-")
            line_id = _backup_line_label(getattr(r, "line_no", None))
            stage_no = pd.to_numeric(getattr(r, "stage_no", None), errors="coerce")
            lot_name = str(getattr(r, "lot_name", "-") or "-")
            workcode = str(getattr(r, "workcode", "u01") or "u01")
            file_rows.append({
                "file_id": file_hash,
                "file_nm": file_nm,
                "file_datetime": event_ts,
                "file_sequence": pd.to_numeric(getattr(r, "machine_order", None), errors="coerce"),
                "machine_code": machine_code,
                "line_id": line_id,
                "stage_no": stage_no,
                "machine_order": pd.to_numeric(getattr(r, "machine_order", None), errors="coerce"),
                "lot_id": lot_name,
                "workcode": workcode,
            })
        file_raw = pd.DataFrame(file_rows)
        file_map = {str(r["file_id"]): r.to_dict() for _, r in file_raw.iterrows()} if not file_raw.empty else {}

        mounter_hdr_rows = []
        mounter_dtl_rows = []
        for _, r in file_raw.iterrows():
            file_nm = r.get("file_nm")
            event_ts = pd.to_datetime(r.get("file_datetime"), errors="coerce")
            machine_code = str(r.get("machine_code") or "-")
            line_id = str(r.get("line_id") or "-")
            stage_no = r.get("stage_no")
            lot_name = str(r.get("lot_id") or "-")
            make_dt = event_ts
            mounter_hdr_rows.append({
                "plant_cd": "P01",
                "wc_cd": str(r.get("workcode") or "u01"),
                "file_nm": file_nm,
                "make_dt": make_dt,
                "post_flag": "Y",
            })
            mounter_dtl_rows.append({
                "plant_cd": "P01",
                "wc_cd": str(r.get("workcode") or "u01"),
                "file_nm": file_nm,
                "file_dt": event_ts,
                "mach_cd": machine_code,
                "stage": stage_no,
                "lane": line_id,
                "output": 1,
                "lot_nm": lot_name,
                "section": str(r.get("machine_order") or ""),
                "row_num": r.get("machine_order"),
                "item": "FILE",
                "result": "PASS",
                "make_dt": make_dt,
            })

        loaded_tables = sum(
            1
            for df in [file_raw, machine, lot, lot_machine, file_lot_machine, pd.DataFrame(mounter_hdr_rows), pd.DataFrame(mounter_dtl_rows)]
            if isinstance(df, pd.DataFrame) and not df.empty
        )

        raw = {
            "file": file_raw.rename(columns={"file_id": "file_id"}),
            "machine": pd.DataFrame([
                {
                    "machine_id": _backup_machine_code(r.get("machine_hash"), machine_map),
                    "machine_name": f"Machine { _backup_machine_code(r.get('machine_hash'), machine_map)}",
                    "line_id": _backup_line_label(r.get("line_no")),
                    "stage_no": pd.to_numeric(r.get("stage_no"), errors="coerce"),
                    "machine_order": pd.to_numeric(r.get("stage_no"), errors="coerce"),
                    "machine_hash": r.get("machine_hash"),
                }
                for _, r in machine.iterrows()
            ]) if not machine.empty else pd.DataFrame(columns=["machine_id", "machine_name", "line_id", "stage_no", "machine_order", "machine_hash"]),
            "lot": pd.DataFrame([
                {
                    "lot_id": _backup_lot_name(r.get("lot_hash"), lot_map),
                    "lot_name": _backup_lot_name(r.get("lot_hash"), lot_map),
                    "line_id": _backup_line_label(r.get("lot_order")),
                    "lot_hash": r.get("lot_hash"),
                    "lot_order": r.get("lot_order"),
                }
                for _, r in lot.iterrows()
            ]) if not lot.empty else pd.DataFrame(columns=["lot_id", "lot_name", "line_id", "lot_hash", "lot_order"]),
            "lot_machine": pd.DataFrame(list(lot_machine_id_map.values())),
            "file_lot_machine": file_lot_machine.copy(),
            "fa_26_34_mounter_hdr": pd.DataFrame(mounter_hdr_rows),
            "fa_26_34_mounter_dtl": pd.DataFrame(mounter_dtl_rows),
            "_meta": {
                "source": "backup",
                "is_sample": False,
                "archive_path": BACKUP_ARCHIVE_PATH,
                "loaded_tables": loaded_tables,
            },
        }

    for k, df in raw.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            df.columns = [c.lower() for c in df.columns]
    return raw


def load_raw_data(period: str = "전체") -> Dict[str, pd.DataFrame]:
    data = {}
    try:
        backup = _build_backup_raw_data(period)
        if backup and any(isinstance(v, pd.DataFrame) and not v.empty for k, v in backup.items() if not str(k).startswith("_")):
            return backup
    except Exception:
        pass
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("set statement_timeout = '60000ms'"))
            full_scan = period == "전체"
            start_ts = None if full_scan else _period_start(period)
            limit = None if full_scan else _period_limit(period)
            loaded = 0
            for table_name, spec in RAW_LOAD_SPECS.items():
                df = _read_table(
                    conn,
                    table_name,
                    None if full_scan else spec["cols"],
                    date_cols=spec.get("date_cols"),
                    start_ts=start_ts,
                    limit=limit,
                    order_cols=spec.get("order_cols"),
                )
                if not df.empty:
                    data[table_name] = df
                    loaded += 1
            data["_meta"] = {
                "source": "db",
                "is_sample": False,
                "scan_mode": "full_history" if full_scan else period,
                "live_table": "_mounter_tag" if "_mounter_tag" in data else None,
                "live_count": len(data.get("_mounter_tag", pd.DataFrame())),
                "loaded_tables": loaded,
            }
    except Exception:
        data = {}
    if "_meta" not in data:
        data["_meta"] = {"source": "db", "is_sample": False, "live_table": None, "live_count": 0}
    return data


def generate_sample_data() -> Dict[str, pd.DataFrame]:
    base = datetime.now()
    lines = ["Line-A", "Line-B", "Line-C"]
    machines = [f"M{idx:02d}" for idx in range(1, 10)]
    lots = [f"LOT{idx:03d}" for idx in range(1, 7)]
    stop_reasons = [("CHANGEOVER", "Changeover", "Process"), ("PICKUP_ERR", "Pickup Error", "Quality"), ("PLACE_ERR", "Placement Error", "Equipment"), ("RECOG_ERR", "Recognition Error", "Quality"), ("TRANSFER_ERR", "Transfer Error", "Equipment"), ("WAIT_PRE", "Wait Pre", "Waiting"), ("WAIT_POST", "Wait Post", "Waiting")]
    lot_machine_rows, machine_time_rows, stop_rows, pickup_rows, comp_rows, comp_pickup_rows = [], [], [], [], [], []
    file_rows = [{"file_id": i, "file_datetime": base - timedelta(days=i // 2, hours=i * 3), "file_sequence": i * 10} for i in range(1, 7)]
    for idx, machine_id in enumerate(machines):
        line_id = lines[idx % len(lines)]
        stage_no = (idx % 3) + 1
        lot_id = lots[idx % len(lots)]
        model_name = f"MODEL-{(idx % 4) + 1}"
        lot_machine_rows.append({"lot_machine_id": idx + 1, "lot_id": lot_id, "machine_id": machine_id, "line_id": line_id, "stage_no": stage_no, "machine_order": idx + 1, "model_name": model_name})
        machine_time_rows.append({"machine_id": machine_id, "lot_id": lot_id, "model_name": model_name, "line_id": line_id, "stage_no": stage_no, "machine_order": idx + 1, "running_time_sec": 3600 + idx * 90, "real_running_time_sec": 3200 + idx * 80, "power_on_time_sec": 4000 + idx * 70, "total_stop_time_sec": 200 + idx * 12, "stop_count": 4 + (idx % 4), "transfer_time_sec": 120 + idx * 5, "board_recognition_time_sec": 40 + idx * 2, "placement_time_sec": 60 + idx * 3, "recorded_at": base - timedelta(days=idx)})
    for idx in range(12):
        reason = stop_reasons[idx % len(stop_reasons)]
        lm = lot_machine_rows[idx % len(lot_machine_rows)]
        stop_rows.append({"stop_reason_code": reason[0], "lot_machine_id": lm["lot_machine_id"], "duration_sec": 45 + idx * 5, "stop_count": 1 if idx % 3 else 3, "recorded_at": base - timedelta(hours=idx * 2), "source_file_id": file_rows[idx % len(file_rows)]["file_id"]})
    for idx, machine in enumerate(machines[:6]):
        lot_id = lots[idx % len(lots)]
        pickup_rows.append({"machine_id": machine, "lot_id": lot_id, "line_id": lines[idx % len(lines)], "stage_no": (idx % 3) + 1, "pickup_count": 1000 + idx * 40, "error_count": 10 + idx * 2, "pickup_error_count": 7 + idx, "recognition_error_count": 3 + (idx % 3)})
        comp_id = f"C{idx:03d}"
        comp_rows.append({"component_id": comp_id, "part_number": f"PN-{idx:04d}", "library_name": f"LIB-{(idx % 3) + 1}", "feeder_id": f"FDR-{(idx % 5) + 1}", "feeder_serial": f"SN{idx + 100}", "nozzle_serial": f"NOZ{idx + 200}"})
        comp_pickup_rows.append({"component_id": comp_id, "machine_id": machine, "lot_id": lot_id, "pickup_count": 800 + idx * 5, "error_count": (idx % 5) + 1, "pickup_error_count": (idx % 3) + 1, "recognition_error_count": (idx % 2), "defect_type": f"Defect-{(idx % 4) + 1}", "recorded_at": base - timedelta(hours=idx)})
    hdr = pd.DataFrame([{"plant_cd": "P01", "wc_cd": "WC01", "file_nm": f"FILE_{i+1:03d}.csv", "make_dt": row["recorded_at"], "post_flag": "Y"} for i, row in enumerate(machine_time_rows)])

    def dtl(extra):
        return pd.DataFrame(extra)

    raw = {
        "fa_2_marking_hdr": hdr.copy(),
        "fa_2_marking_dtl": dtl([{"plant_cd": "P01", "wc_cd": "WC01", "file_nm": f"FILE_{i+1:03d}.csv", "file_dt": row["recorded_at"], "value": f"VALUE-{i:03d}", "make_dt": row["recorded_at"]} for i, row in enumerate(machine_time_rows)]),
        "fa_14_aoi_hdr": hdr.copy(),
        "fa_14_aoi_dtl": dtl([{"plant_cd": "P01", "wc_cd": "WC01", "file_nm": f"FILE_{i+1:03d}.csv", "file_dt": row["recorded_at"], "mach_cd": row["machine_id"], "lane": row["line_id"], "data_type": "AOI", "barcode": f"BC-{i:03d}", "panelbarcode": f"PB-{i:03d}", "enddatetime": row["recorded_at"].strftime("%Y-%m-%d %H:%M:%S"), "pcbmodel": row["model_name"]} for i, row in enumerate(machine_time_rows)]),
        "fa_24_spi_hdr": hdr.copy(),
        "fa_24_spi_dtl": dtl([{"plant_cd": "P01", "wc_cd": "WC01", "file_nm": f"FILE_{i+1:03d}.csv", "file_dt": row["recorded_at"], "mach_cd": row["machine_id"], "lane": row["line_id"], "data_type": "SPI", "panelbarcode": f"PB-{i:03d}", "model": row["model_name"], "machineresult": "PASS" if i % 4 else "FAIL", "reviewresult": "PASS" if i % 5 else "REWORK"} for i, row in enumerate(machine_time_rows)]),
        "fa_26_34_mounter_hdr": hdr.copy(),
        "fa_26_34_mounter_dtl": dtl([{"plant_cd": "P01", "wc_cd": "WC01", "file_nm": f"FILE_{i+1:03d}.csv", "file_dt": row["recorded_at"], "mach_cd": row["machine_id"], "stage": str(row["stage_no"]), "lane": row["line_id"], "output": 100 + i * 7, "lot_nm": row["lot_id"], "section": f"S{(i % 4) + 1}", "row_num": i + 1} for i, row in enumerate(machine_time_rows)]),
        "fa_35_moi_hdr": hdr.copy(),
        "fa_35_moi_dtl": dtl([{"plant_cd": "P01", "wc_cd": "WC01", "file_nm": f"FILE_{i+1:03d}.csv", "file_dt": row["recorded_at"], "mach_cd": row["machine_id"], "lane": row["line_id"], "data_type": "MOI", "barcode": f"MBC-{i:03d}", "panelbarcode": f"PB-{i:03d}", "enddatetime": row["recorded_at"].strftime("%Y-%m-%d %H:%M:%S"), "pcbmodel": row["model_name"]} for i, row in enumerate(machine_time_rows)]),
        "fa_42_aoi_hdr": hdr.copy(),
        "fa_42_aoi_dtl": dtl([{"plant_cd": "P01", "wc_cd": "WC01", "file_nm": f"FILE_{i+1:03d}.csv", "file_dt": row["recorded_at"], "mach_cd": row["machine_id"], "lane": row["line_id"], "data_type": "AOI", "barcode": f"BC42-{i:03d}", "panelbarcode": f"PB-{i:03d}", "enddatetime": row["recorded_at"].strftime("%Y-%m-%d %H:%M:%S"), "pcbmodel": row["model_name"]} for i, row in enumerate(machine_time_rows)]),
        "_mounter_tag": pd.DataFrame([{"_devicedate": row["recorded_at"], "_linecode": row["line_id"], "_workcode": f"WC{row['stage_no']:02d}", "_equipcode": row["machine_id"], "_type": "STATE", "_tagname": "RUN" if i % 3 else "WAIT_PRE", "_value": "1" if i % 2 else "0", "_insertdate": row["recorded_at"] + timedelta(seconds=5)} for i, row in enumerate(machine_time_rows)]),
        "machine_time_summary": pd.DataFrame(machine_time_rows),
        "stop_log": pd.DataFrame(stop_rows),
        "stop_reason": pd.DataFrame(stop_reasons, columns=["stop_reason_code", "stop_reason_name", "stop_reason_group"]),
        "lot_machine": pd.DataFrame(lot_machine_rows),
        "machine": pd.DataFrame([{"machine_id": r["machine_id"], "machine_name": f"Machine {r['machine_id']}", "line_id": r["line_id"], "stage_no": r["stage_no"], "machine_order": r["machine_order"]} for r in lot_machine_rows]),
        "lot": pd.DataFrame({"lot_id": lots, "lot_name": [f"LOT_NAME_{i}" for i in range(1, len(lots) + 1)], "model_name": [f"MODEL-{(i % 4) + 1}" for i in range(len(lots))], "line_id": [lines[i % len(lines)] for i in range(len(lots))]}),
        "file": pd.DataFrame(file_rows),
        "pickup_error_summary": pd.DataFrame(pickup_rows),
        "component_pickup_summary": pd.DataFrame(comp_pickup_rows),
        "component": pd.DataFrame(comp_rows),
        "_meta": {"source": "sample", "is_sample": True},
    }
    for k, df in raw.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            df.columns = [c.lower() for c in df.columns]
    return raw
