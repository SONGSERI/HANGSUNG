from datetime import datetime
from typing import List, Dict, Optional, Union

LotInfoValue = Optional[Union[datetime, str]]


def parse_lot_info(lines: List[str]) -> Dict[str, LotInfoValue]:
    result: Dict[str, LotInfoValue] = {
        "start_time": None,
        "end_time": None,
        "lane": None,
    }

    for line in lines:
        line = line.strip()

        if line.startswith("LOT START"):
            result["start_time"] = datetime.strptime(
                line.replace("LOT START", "").strip(),
                "%Y-%m-%d %H:%M:%S"
            )

        elif line.startswith("LOT END"):
            result["end_time"] = datetime.strptime(
                line.replace("LOT END", "").strip(),
                "%Y-%m-%d %H:%M:%S"
            )

        elif line.startswith("Lane="):
            result["lane"] = line.replace("Lane=", "").strip() or None

    return result


def parse_lot_time(lines: List[str]) -> Dict[str, Optional[datetime]]:
    lot_info = parse_lot_info(lines)
    return {
        "start_time": lot_info["start_time"],
        "end_time": lot_info["end_time"],
    }
