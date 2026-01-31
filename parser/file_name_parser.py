# file_name_parser.py
import os
import re
from datetime import datetime

FILE_PATTERN = re.compile(
    r'(?P<date>\d{8})(?P<seq>\d+)-'
    r'(?P<line>[^-]+)-'
    r'(?P<process>[^-]+)-'
    r'(?P<stage>[^-]+)-'
    r'(?P<machine>[^-]+)-'
    r'(?P<lot>[^.]+)\.(?P<ext>u01|u03)'
)

def parse_file_name(file_path: str) -> dict:
    file_name = os.path.basename(file_path)
    m = FILE_PATTERN.match(file_name)

    if not m:
        raise ValueError(f"Invalid file name format: {file_name}")

    gd = m.groupdict()

    return {
        "file_name": file_name,
        "file_datetime": datetime.strptime(gd["date"], "%Y%m%d"),
        "file_sequence": gd["seq"],
        "line_id": gd["line"],
        "process_no": gd["process"],
        "stage_no": gd["stage"],
        "machine_order": gd["machine"],
        "lot_name": gd["lot"],
        "file_type": gd["ext"],
    }
