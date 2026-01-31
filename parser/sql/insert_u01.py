from db import execute_upsert

SQL_MTS = """
INSERT INTO machine_time_summary (
    lot_machine_id,
    power_on_time_sec, running_time_sec, real_running_time_sec,
    total_stop_time_sec, transfer_time_sec,
    board_recognition_time_sec, placement_time_sec
)
VALUES (
    %(lot_machine_id)s,
    %(power_on_time_sec)s, %(running_time_sec)s, %(real_running_time_sec)s,
    %(total_stop_time_sec)s, %(transfer_time_sec)s,
    %(board_recognition_time_sec)s, %(placement_time_sec)s
)
ON CONFLICT (lot_machine_id)
DO UPDATE SET
    power_on_time_sec = EXCLUDED.power_on_time_sec,
    running_time_sec = EXCLUDED.running_time_sec,
    real_running_time_sec = EXCLUDED.real_running_time_sec,
    total_stop_time_sec = EXCLUDED.total_stop_time_sec,
    transfer_time_sec = EXCLUDED.transfer_time_sec,
    board_recognition_time_sec = EXCLUDED.board_recognition_time_sec,
    placement_time_sec = EXCLUDED.placement_time_sec
"""

SQL_STOP_LOG = """
INSERT INTO stop_log (
    stop_log_id, lot_machine_id, stop_reason_code,
    duration_sec, stop_count, source_file_id
)
VALUES (
    %(stop_log_id)s, %(lot_machine_id)s, %(stop_reason_code)s,
    %(duration_sec)s, %(stop_count)s, %(source_file_id)s
)
ON CONFLICT (stop_log_id) DO NOTHING
"""

def insert_u01(conn, lot_machine_id, mts_row, stop_logs):
    mts_row["lot_machine_id"] = lot_machine_id
    execute_upsert(conn, SQL_MTS, [mts_row])
    execute_upsert(conn, SQL_STOP_LOG, stop_logs)
