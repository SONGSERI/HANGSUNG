from db import execute_upsert

SQL_FILE = """
INSERT INTO file (
    file_id, file_name, file_datetime, file_sequence,
    line_id, process_no, stage_no, machine_order,
    lot_name, file_type
)
VALUES (%(file_id)s, %(file_name)s, %(file_datetime)s, %(file_sequence)s,
        %(line_id)s, %(process_no)s, %(stage_no)s, %(machine_order)s,
        %(lot_name)s, %(file_type)s)
ON CONFLICT (file_id) DO NOTHING
"""

SQL_LOT = """
INSERT INTO lot (lot_id, lot_name, start_time, end_time, lane)
VALUES (%(lot_id)s, %(lot_name)s, %(start_time)s, %(end_time)s, %(lane)s)
ON CONFLICT (lot_id) DO NOTHING
"""

SQL_MACHINE = """
INSERT INTO machine (machine_id, line_id, stage_no, machine_order)
VALUES (%(machine_id)s, %(line_id)s, %(stage_no)s, %(machine_order)s)
ON CONFLICT (machine_id) DO NOTHING
"""

SQL_LOT_MACHINE = """
INSERT INTO lot_machine (lot_machine_id, lot_id, machine_id)
VALUES (%(lot_machine_id)s, %(lot_id)s, %(machine_id)s)
ON CONFLICT (lot_machine_id) DO NOTHING
"""

SQL_FILE_LOT_MACHINE = """
INSERT INTO file_lot_machine (file_id, lot_machine_id)
VALUES (%(file_id)s, %(lot_machine_id)s)
ON CONFLICT DO NOTHING
"""

def insert_core(conn, file_row, lot_row, machine_row, lot_machine_row):
    execute_upsert(conn, SQL_FILE, [file_row])
    execute_upsert(conn, SQL_LOT, [lot_row])
    execute_upsert(conn, SQL_MACHINE, [machine_row])
    execute_upsert(conn, SQL_LOT_MACHINE, [lot_machine_row])
    execute_upsert(conn, SQL_FILE_LOT_MACHINE, [{
        "file_id": file_row["file_id"],
        "lot_machine_id": lot_machine_row["lot_machine_id"],
    }])

def insert_file_rows(conn, file_rows, lot_machine_id):
    if not file_rows:
        return
    execute_upsert(conn, SQL_FILE, file_rows)
    file_lot_machine_rows = [
        {
            "file_id": row["file_id"],
            "lot_machine_id": lot_machine_id,
        }
        for row in file_rows
    ]
    execute_upsert(conn, SQL_FILE_LOT_MACHINE, file_lot_machine_rows)
