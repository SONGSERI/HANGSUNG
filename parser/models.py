# models.py
from dataclasses import dataclass

@dataclass
class Lot:
    lot_id: str
    lot_name: str
    start_time: str | None = None
    end_time: str | None = None
    lane: str | None = None

@dataclass
class Machine:
    machine_id: str
    line_id: str
    stage_no: str
    machine_order: str

@dataclass
class LotMachine:
    lot_machine_id: str
    lot_id: str
    machine_id: str
