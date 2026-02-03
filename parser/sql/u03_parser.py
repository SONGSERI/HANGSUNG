# u03_parser.py
# 픽업 / 에러 / 부품 단위 요약

from typing import List, Dict, Tuple

from utils import make_hash


def parse_pickup_error_summary(lines: List[str]) -> Dict[str, int]:
    result: Dict[str, int] = {}

    for line in lines:
        line = line.strip()

        if line.startswith("Total Pickup Count"):
            result["total_pickup_count"] = int(line.split()[-1])

        elif line.startswith("Total Error Count"):
            result["total_error_count"] = int(line.split()[-1])

        elif line.startswith("Pickup Error Count"):
            result["pickup_error_count"] = int(line.split()[-1])

        elif line.startswith("Recognition Error Count"):
            result["recognition_error_count"] = int(line.split()[-1])

    return result


def parse_component_pickup(
    lines: List[str],
    machine_id: str,
    lot_machine_id: str,
    file_id: str
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    components: Dict[str, Dict[str, object]] = {}
    summaries: List[Dict[str, object]] = []

    for line in lines:
        if not line.startswith("COMPONENT"):
            continue

        parts = line.split()

        table_id, feeder_id, feeder_serial = parts[1], parts[2], parts[3]
        nozzle_changer, nozzle_holder, nozzle_serial = parts[4], parts[5], parts[6]
        part_number, library_name = parts[7], parts[8]
        pickup_count, error_count = int(parts[9]), int(parts[10])

        component_id = make_hash(
            machine_id,
            table_id,
            feeder_id,
            feeder_serial,
            nozzle_changer,
            nozzle_holder,
            nozzle_serial,
        )

        if component_id not in components:
            components[component_id] = {
                "component_id": component_id,
                "machine_id": machine_id,
                "table_id": table_id,
                "feeder_id": feeder_id,
                "feeder_serial": feeder_serial,
                "nozzle_changer": nozzle_changer,
                "nozzle_holder": nozzle_holder,
                "nozzle_serial": nozzle_serial,
                "part_number": part_number,
                "library_name": library_name,
            }

        summaries.append({
            "lot_machine_id": lot_machine_id,
            "component_id": component_id,
            "pickup_count": pickup_count,
            "error_count": error_count,
            "pickup_error_count": error_count,
            "recognition_error_count": 0,
            "source_file_id": file_id,
        })

    return list(components.values()), summaries
