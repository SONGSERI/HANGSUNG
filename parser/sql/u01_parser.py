# u01_parser.py
# 시간 / 정지 로그 파싱

from typing import List, Dict

from utils import time_to_seconds
from stop_reason_master import STOP_REASON_MASTER


def parse_machine_time_summary(lines: List[str]) -> Dict[str, int]:
    """
    설비 시간 요약 파싱
    """
    result: Dict[str, int] = {}

    for line in lines:
        line = line.strip()

        if line.startswith("Power ON Time"):
            result["power_on_time_sec"] = time_to_seconds(line.split()[-1])

        elif line.startswith("Running Time"):
            result["running_time_sec"] = time_to_seconds(line.split()[-1])

        elif line.startswith("Real Running Time"):
            result["real_running_time_sec"] = time_to_seconds(line.split()[-1])

        elif line.startswith("Total Stop Time"):
            result["total_stop_time_sec"] = time_to_seconds(line.split()[-1])

        elif line.startswith("Transfer Time"):
            result["transfer_time_sec"] = time_to_seconds(line.split()[-1])

        elif line.startswith("Board Recognition Time"):
            result["board_recognition_time_sec"] = time_to_seconds(line.split()[-1])

        elif line.startswith("Placement Time"):
            result["placement_time_sec"] = time_to_seconds(line.split()[-1])

    return result


def parse_stop_information(
    lines: List[str],
    file_id: str,
    lot_machine_id: str
) -> List[Dict[str, object]]:
    """
    설비 정지 로그 파싱
    """
    stop_logs: List[Dict[str, object]] = []

    for line in lines:
        if "Stop Time/Count" not in line:
            continue

        name, values = line.split("Stop Time/Count")
        stop_name = name.strip().upper()

        time_str, count = values.strip().split()
        duration = time_to_seconds(time_str)

        reason = STOP_REASON_MASTER.get(
            stop_name,
            {
                "code": "UNKNOWN",
                "group": "UNKNOWN",
            }
        )

        stop_logs.append({
            "stop_log_id": None,
            "lot_machine_id": lot_machine_id,
            "stop_reason_code": reason["code"],
            "duration_sec": duration,
            "stop_count": int(count),
            "source_file_id": file_id,
        })

    return stop_logs
