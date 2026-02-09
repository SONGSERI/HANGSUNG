from db import execute_upsert

SQL_TAG_CATEGORY = """
INSERT INTO tag_category (
    tag_category_id, tag_category_name, parent_category_id, description
)
VALUES (
    %(tag_category_id)s, %(tag_category_name)s, %(parent_category_id)s, %(description)s
)
ON CONFLICT (tag_category_id)
DO UPDATE SET
    tag_category_name = EXCLUDED.tag_category_name,
    parent_category_id = EXCLUDED.parent_category_id,
    description = EXCLUDED.description
"""

SQL_TAG_INFO = """
INSERT INTO tag_info (
    tag_id, tag_name, tag_category_id, machine_id,
    data_type, unit, source_system, is_active, description
)
VALUES (
    %(tag_id)s, %(tag_name)s, %(tag_category_id)s, %(machine_id)s,
    %(data_type)s, %(unit)s, %(source_system)s, %(is_active)s, %(description)s
)
ON CONFLICT (tag_id)
DO UPDATE SET
    tag_name = EXCLUDED.tag_name,
    tag_category_id = EXCLUDED.tag_category_id,
    machine_id = EXCLUDED.machine_id,
    data_type = EXCLUDED.data_type,
    unit = EXCLUDED.unit,
    source_system = EXCLUDED.source_system,
    is_active = EXCLUDED.is_active,
    description = EXCLUDED.description
"""

SQL_TAG_SPEC = """
INSERT INTO tag_spec (
    tag_spec_id, tag_id, spec_type, spec_value, effective_from, effective_to
)
VALUES (
    %(tag_spec_id)s, %(tag_id)s, %(spec_type)s, %(spec_value)s,
    %(effective_from)s, %(effective_to)s
)
ON CONFLICT (tag_spec_id)
DO UPDATE SET
    spec_type = EXCLUDED.spec_type,
    spec_value = EXCLUDED.spec_value,
    effective_from = EXCLUDED.effective_from,
    effective_to = EXCLUDED.effective_to
"""

SQL_TAG_REALTIME = """
INSERT INTO tag_realtime (
    tag_data_id, tag_id, machine_id, recorded_at,
    tag_value, quality_flag, source_file_id
)
VALUES (
    %(tag_data_id)s, %(tag_id)s, %(machine_id)s, %(recorded_at)s,
    %(tag_value)s, %(quality_flag)s, %(source_file_id)s
)
ON CONFLICT (tag_data_id) DO NOTHING
"""


def insert_tags(
    conn,
    tag_categories=None,
    tag_infos=None,
    tag_specs=None,
    tag_realtime=None,
):
    if tag_categories:
        execute_upsert(conn, SQL_TAG_CATEGORY, tag_categories)
    if tag_infos:
        execute_upsert(conn, SQL_TAG_INFO, tag_infos)
    if tag_specs:
        execute_upsert(conn, SQL_TAG_SPEC, tag_specs)
    if tag_realtime:
        execute_upsert(conn, SQL_TAG_REALTIME, tag_realtime)
