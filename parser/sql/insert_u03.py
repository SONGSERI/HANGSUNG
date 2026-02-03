from db import execute_upsert

SQL_PICKUP_SUMMARY = """
INSERT INTO pickup_error_summary (
    lot_machine_id,
    total_pickup_count, total_error_count,
    pickup_error_count, recognition_error_count,
    thick_error_count, placement_error_count,
    part_drop_error_count, transfer_unit_part_drop_error_count,
    pre_pickup_inspection_error_count
)
VALUES (
    %(lot_machine_id)s,
    %(total_pickup_count)s, %(total_error_count)s,
    %(pickup_error_count)s, %(recognition_error_count)s,
    %(thick_error_count)s, %(placement_error_count)s,
    %(part_drop_error_count)s, %(transfer_unit_part_drop_error_count)s,
    %(pre_pickup_inspection_error_count)s
)
ON CONFLICT (lot_machine_id)
DO UPDATE SET
    total_pickup_count = EXCLUDED.total_pickup_count,
    total_error_count = EXCLUDED.total_error_count
"""

SQL_COMPONENT = """
INSERT INTO component (
    component_id, machine_id, table_id, feeder_id, feeder_serial,
    nozzle_changer, nozzle_holder, nozzle_serial,
    part_number, library_name
)
VALUES (
    %(component_id)s, %(machine_id)s, %(table_id)s, %(feeder_id)s, %(feeder_serial)s,
    %(nozzle_changer)s, %(nozzle_holder)s, %(nozzle_serial)s,
    %(part_number)s, %(library_name)s
)
ON CONFLICT (component_id) DO NOTHING
"""

SQL_COMPONENT_SUMMARY = """
INSERT INTO component_pickup_summary (
    lot_machine_id, component_id,
    pickup_count, error_count,
    pickup_error_count, recognition_error_count,
    source_file_id
)
VALUES (
    %(lot_machine_id)s, %(component_id)s,
    %(pickup_count)s, %(error_count)s,
    %(pickup_error_count)s, %(recognition_error_count)s,
    %(source_file_id)s
)
ON CONFLICT (lot_machine_id, component_id)
DO UPDATE SET
    pickup_count = EXCLUDED.pickup_count,
    error_count = EXCLUDED.error_count
"""

# 🔒 기본값 세트 (DB 스키마 기준)
PICKUP_SUMMARY_DEFAULT = {
    "total_pickup_count": 0,
    "total_error_count": 0,
    "pickup_error_count": 0,
    "recognition_error_count": 0,
    "thick_error_count": 0,
    "placement_error_count": 0,
    "part_drop_error_count": 0,
    "transfer_unit_part_drop_error_count": 0,
    "pre_pickup_inspection_error_count": 0,
}


def insert_u03(conn, pickup_summary, components, component_summaries):
    # pickup_summary 방어 (KeyError 차단)
    safe_pickup_summary = {
        **PICKUP_SUMMARY_DEFAULT,
        **pickup_summary,
    }

    execute_upsert(conn, SQL_PICKUP_SUMMARY, [safe_pickup_summary])

    if components:
        execute_upsert(conn, SQL_COMPONENT, components)

    if component_summaries:
        execute_upsert(conn, SQL_COMPONENT_SUMMARY, component_summaries)
