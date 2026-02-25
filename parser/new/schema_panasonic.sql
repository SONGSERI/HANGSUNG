-- Panasonic SMT log schema (flexible JSONB + structured report info)

CREATE TABLE IF NOT EXISTS report (
  report_id TEXT PRIMARY KEY,
  file_path TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_dir TEXT,
  file_ext TEXT,
  file_ts TIMESTAMP,
  format TEXT,
  version TEXT,
  machine TEXT,
  report_dt TIMESTAMP,
  author_type TEXT,
  author TEXT,
  diff TEXT,
  mjsid TEXT,
  comment TEXT
);

CREATE TABLE IF NOT EXISTS report_info (
  report_id TEXT PRIMARY KEY REFERENCES report(report_id) ON DELETE CASCADE,
  stage TEXT,
  lane TEXT,
  serial TEXT,
  serialstatus TEXT,
  code TEXT,
  bcrstatus TEXT,
  productid TEXT,
  rev TEXT,
  planid TEXT,
  output TEXT,
  lotname TEXT,
  lotnumber TEXT,
  masterwo TEXT,
  subwo TEXT
);

CREATE TABLE IF NOT EXISTS report_kv_sections (
  report_id TEXT REFERENCES report(report_id) ON DELETE CASCADE,
  section_name TEXT NOT NULL,
  data JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_report_kv_sections_report_id ON report_kv_sections(report_id);
CREATE INDEX IF NOT EXISTS idx_report_kv_sections_section ON report_kv_sections(section_name);

CREATE TABLE IF NOT EXISTS report_table_sections (
  report_id TEXT REFERENCES report(report_id) ON DELETE CASCADE,
  section_name TEXT NOT NULL,
  columns JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_report_table_sections_report_id ON report_table_sections(report_id);
CREATE INDEX IF NOT EXISTS idx_report_table_sections_section ON report_table_sections(section_name);

CREATE TABLE IF NOT EXISTS report_table_rows (
  report_id TEXT REFERENCES report(report_id) ON DELETE CASCADE,
  section_name TEXT NOT NULL,
  row_index INTEGER NOT NULL,
  data JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_report_table_rows_report_id ON report_table_rows(report_id);
CREATE INDEX IF NOT EXISTS idx_report_table_rows_section ON report_table_rows(section_name);
