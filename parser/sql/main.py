# main.py
# 파일 단위 처리

from file_name_parser import parse_file_name
from utils import make_hash
from models import Lot, Machine, LotMachine

def process_file(file_path: str):
    meta = parse_file_name(file_path)

    file_id = make_hash(meta["file_name"])
    lot_id = make_hash(meta["lot_name"])
    machine_id = make_hash(meta["line_id"], meta["stage_no"], meta["machine_order"])
    lot_machine_id = make_hash(lot_id, machine_id)

    lot = Lot(lot_id=lot_id, lot_name=meta["lot_name"])
    machine = Machine(
        machine_id=machine_id,
        line_id=meta["line_id"],
        stage_no=meta["stage_no"],
        machine_order=meta["machine_order"],
    )
    lot_machine = LotMachine(
        lot_machine_id=lot_machine_id,
        lot_id=lot_id,
        machine_id=machine_id,
    )

    print(lot)
    print(machine)
    print(lot_machine)


if __name__ == "__main__":
    process_file(
        "test/20260116000000391-05-1-1-3-NAD_H_T_EBR37416101.u01"
    )

