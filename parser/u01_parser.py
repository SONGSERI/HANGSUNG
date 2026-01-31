# u01_parser.py
from utils import time_to_seconds

def parse_machine_time_summary(lines: list[str]) -> dict:
    """
    u01 Machine Time Summary 영역 파싱
    """
    result = {}

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


def parse_stop_information(lines: list[str]) -> list[dict]:
    """
    Stop information per machine
    """
    stops = []

    for line in lines:
        if "Stop Time/Count" not in line:
            continue

        name, values = line.split("Stop Time/Count")
        time_str, count = values.strip().split()

        stops.append({
            "stop_reason_name": name.strip(),
            "duration_sec": time_to_seconds(time_str),
            "stop_count": int(count),
        })

    return stops
