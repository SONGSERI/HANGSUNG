from datetime import datetime
from typing import List, Dict, Optional

def parse_lot_time(lines: List[str]) -> Dict[str, Optional[datetime]]:
    result = {"start_time": None, "end_time": None}

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

    return result
