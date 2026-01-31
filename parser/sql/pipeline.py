from db import get_conn
from insert_master import insert_stop_reason_master
from insert_core import insert_core
from insert_u01 import insert_u01
from insert_u03 import insert_u03

def run_pipeline(
    file_row,
    lot_row,
    machine_row,
    lot_machine_row,
    mts_row,
    stop_logs,
    pickup_summary,
    components,
    component_summaries
):
    conn = get_conn()

    insert_stop_reason_master()
    insert_core(conn, file_row, lot_row, machine_row, lot_machine_row)

    if mts_row or stop_logs:
        insert_u01(conn, lot_machine_row["lot_machine_id"], mts_row, stop_logs)

    if pickup_summary:
        insert_u03(conn, pickup_summary, components, component_summaries)

    conn.close()
