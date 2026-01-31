from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Lot:
    lot_id: str
    lot_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    lane: Optional[str] = None

@dataclass
class Machine:
    machine_id: str
    line_id: str
    stage_no: int
    machine_order: int

@dataclass
class LotMachine:
    lot_machine_id: str
    lot_id: str
    machine_id: str
