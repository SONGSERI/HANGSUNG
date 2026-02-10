-- =========================
-- RESET : 기존 테이블 삭제
-- =========================
DROP TABLE IF EXISTS tag_realtime CASCADE;
DROP TABLE IF EXISTS tag_spec CASCADE;
DROP TABLE IF EXISTS tag_info CASCADE;
DROP TABLE IF EXISTS tag_category CASCADE;
DROP TABLE IF EXISTS component_pickup_summary CASCADE;
DROP TABLE IF EXISTS component CASCADE;
DROP TABLE IF EXISTS pickup_error_summary CASCADE;
DROP TABLE IF EXISTS stop_log CASCADE;
DROP TABLE IF EXISTS stop_reason CASCADE;
DROP TABLE IF EXISTS machine_time_summary CASCADE;
DROP TABLE IF EXISTS file_lot_machine CASCADE;
DROP TABLE IF EXISTS lot_machine CASCADE;
DROP TABLE IF EXISTS machine CASCADE;
DROP TABLE IF EXISTS lot CASCADE;
DROP TABLE IF EXISTS file CASCADE;


-- =========================
-- FILE : 로그 파일 메타
-- =========================
CREATE TABLE file (
    file_id            VARCHAR(64) PRIMARY KEY,
    file_name          TEXT NOT NULL,
    file_datetime      DATE NOT NULL,
    file_sequence      INTEGER NOT NULL,
    line_id            VARCHAR(16) NOT NULL,
    process_no         INTEGER NOT NULL,
    stage_no           INTEGER NOT NULL,
    machine_order      INTEGER NOT NULL,
    lot_name           VARCHAR(128) NOT NULL,
    file_type          VARCHAR(8) NOT NULL
);

CREATE INDEX idx_file_lot
    ON file (lot_name, line_id, stage_no, machine_order);


-- =========================
-- LOT : Lot 단위 정보
-- =========================
CREATE TABLE lot (
    lot_id      VARCHAR(64) PRIMARY KEY,
    lot_name    VARCHAR(128) NOT NULL,
    start_time  TIMESTAMP,
    end_time    TIMESTAMP,
    lane        VARCHAR(32)
);

CREATE UNIQUE INDEX idx_lot_name
    ON lot (lot_name);


-- =========================
-- MACHINE : 설비 마스터
-- =========================
CREATE TABLE machine (
    machine_id     VARCHAR(64) PRIMARY KEY,
    line_id        VARCHAR(16) NOT NULL,
    stage_no       INTEGER NOT NULL,
    machine_order  INTEGER NOT NULL
);

CREATE UNIQUE INDEX idx_machine_unique
    ON machine (line_id, stage_no, machine_order);


-- =========================
-- LOT_MACHINE : Lot × Machine 실행 단위
-- =========================
CREATE TABLE lot_machine (
    lot_machine_id VARCHAR(64) PRIMARY KEY,
    lot_id         VARCHAR(64) NOT NULL,
    machine_id     VARCHAR(64) NOT NULL,
    CONSTRAINT fk_lm_lot
        FOREIGN KEY (lot_id) REFERENCES lot (lot_id),
    CONSTRAINT fk_lm_machine
        FOREIGN KEY (machine_id) REFERENCES machine (machine_id)
);

CREATE UNIQUE INDEX idx_lot_machine_unique
    ON lot_machine (lot_id, machine_id);


-- =========================
-- FILE_LOT_MACHINE : 파일 ↔ 실행 매핑
-- =========================
CREATE TABLE file_lot_machine (
    file_id         VARCHAR(64) NOT NULL,
    lot_machine_id  VARCHAR(64) NOT NULL,
    PRIMARY KEY (file_id, lot_machine_id),
    CONSTRAINT fk_flm_file
        FOREIGN KEY (file_id) REFERENCES file (file_id),
    CONSTRAINT fk_flm_lm
        FOREIGN KEY (lot_machine_id) REFERENCES lot_machine (lot_machine_id)
);


-- =========================
-- MACHINE_TIME_SUMMARY : 시간 집계
-- =========================
CREATE TABLE machine_time_summary (
    lot_machine_id               VARCHAR(64) PRIMARY KEY,
    power_on_time_sec            INTEGER,
    running_time_sec             INTEGER,
    real_running_time_sec        INTEGER,
    total_stop_time_sec          INTEGER,
    transfer_time_sec            INTEGER,
    board_recognition_time_sec   INTEGER,
    placement_time_sec           INTEGER,
    CONSTRAINT fk_mts_lm
        FOREIGN KEY (lot_machine_id) REFERENCES lot_machine (lot_machine_id)
);


-- =========================
-- STOP_REASON : 정지 코드 사전
-- =========================
CREATE TABLE stop_reason (
    stop_reason_code   VARCHAR(32) PRIMARY KEY,
    stop_reason_name   VARCHAR(128) NOT NULL,
    stop_reason_group  VARCHAR(32) NOT NULL
);


-- =========================
-- STOP_LOG : 정지 이력 (누적)
-- =========================
CREATE TABLE stop_log (
    stop_log_id        VARCHAR(64) PRIMARY KEY,
    lot_machine_id     VARCHAR(64) NOT NULL,
    stop_reason_code   VARCHAR(32) NOT NULL,
    duration_sec       INTEGER NOT NULL,
    stop_count         INTEGER NOT NULL,
    source_file_id     VARCHAR(64) NOT NULL,
    CONSTRAINT fk_sl_lm
        FOREIGN KEY (lot_machine_id) REFERENCES lot_machine (lot_machine_id),
    CONSTRAINT fk_sl_reason
        FOREIGN KEY (stop_reason_code) REFERENCES stop_reason (stop_reason_code),
    CONSTRAINT fk_sl_file
        FOREIGN KEY (source_file_id) REFERENCES file (file_id)
);

CREATE INDEX idx_stop_log_lm
    ON stop_log (lot_machine_id);


-- =========================
-- PICKUP_ERROR_SUMMARY : 설비 품질 요약
-- =========================
CREATE TABLE pickup_error_summary (
    lot_machine_id                         VARCHAR(64) PRIMARY KEY,
    total_pickup_count                     INTEGER,
    total_error_count                      INTEGER,
    pickup_error_count                     INTEGER,
    recognition_error_count                INTEGER,
    thick_error_count                      INTEGER,
    placement_error_count                  INTEGER,
    part_drop_error_count                  INTEGER,
    transfer_unit_part_drop_error_count    INTEGER,
    pre_pickup_inspection_error_count      INTEGER,
    CONSTRAINT fk_pes_lm
        FOREIGN KEY (lot_machine_id) REFERENCES lot_machine (lot_machine_id)
);


-- =========================
-- COMPONENT : 부품/구성요소 마스터
-- =========================
CREATE TABLE component (
    component_id      VARCHAR(64) PRIMARY KEY,
    machine_id        VARCHAR(64) NOT NULL,
    table_id          VARCHAR(32),
    feeder_id         VARCHAR(32),
    feeder_serial     VARCHAR(64),
    nozzle_changer    VARCHAR(32),
    nozzle_holder     VARCHAR(32),
    nozzle_serial     VARCHAR(64),
    part_number       VARCHAR(64),
    library_name      VARCHAR(64),
    CONSTRAINT fk_component_machine
        FOREIGN KEY (machine_id) REFERENCES machine (machine_id)
);


-- =========================
-- COMPONENT_PICKUP_SUMMARY : 구성요소별 집계
-- =========================
CREATE TABLE component_pickup_summary (
    lot_machine_id             VARCHAR(64) NOT NULL,
    component_id               VARCHAR(64) NOT NULL,
    pickup_count               INTEGER,
    error_count                INTEGER,
    pickup_error_count         INTEGER,
    recognition_error_count    INTEGER,
    source_file_id             VARCHAR(64) NOT NULL,
    PRIMARY KEY (lot_machine_id, component_id),
    CONSTRAINT fk_cps_lm
        FOREIGN KEY (lot_machine_id) REFERENCES lot_machine (lot_machine_id),
    CONSTRAINT fk_cps_component
        FOREIGN KEY (component_id) REFERENCES component (component_id),
    CONSTRAINT fk_cps_file
        FOREIGN KEY (source_file_id) REFERENCES file (file_id)
);


-- =========================
-- TAG_CATEGORY : 태그 분류
-- =========================
CREATE TABLE tag_category (
    tag_category_id      VARCHAR(64) PRIMARY KEY,
    tag_category_name    VARCHAR(128) NOT NULL,
    parent_category_id   VARCHAR(64),
    description          TEXT,
    CONSTRAINT fk_tag_category_parent
        FOREIGN KEY (parent_category_id) REFERENCES tag_category (tag_category_id)
);


-- =========================
-- TAG_INFO : 태그 기준 정보
-- =========================
CREATE TABLE tag_info (
    tag_id            VARCHAR(64) PRIMARY KEY,
    tag_name          VARCHAR(128) NOT NULL,
    tag_category_id   VARCHAR(64) NOT NULL,
    machine_id        VARCHAR(64),
    data_type         VARCHAR(32),
    unit              VARCHAR(32),
    source_system     VARCHAR(64),
    is_active         BOOLEAN,
    description       TEXT,
    CONSTRAINT fk_tag_info_category
        FOREIGN KEY (tag_category_id) REFERENCES tag_category (tag_category_id),
    CONSTRAINT fk_tag_info_machine
        FOREIGN KEY (machine_id) REFERENCES machine (machine_id)
);


-- =========================
-- TAG_SPEC : 태그 기준값/스펙
-- =========================
CREATE TABLE tag_spec (
    tag_spec_id    VARCHAR(64) PRIMARY KEY,
    tag_id         VARCHAR(64) NOT NULL,
    spec_type      VARCHAR(32) NOT NULL,
    spec_value     DOUBLE PRECISION,
    effective_from TIMESTAMP,
    effective_to   TIMESTAMP,
    CONSTRAINT fk_tag_spec_info
        FOREIGN KEY (tag_id) REFERENCES tag_info (tag_id)
);


-- =========================
-- TAG_REALTIME : 실시간 데이터 적재
-- =========================
CREATE TABLE tag_realtime (
    tag_data_id     VARCHAR(64) PRIMARY KEY,
    tag_id          VARCHAR(64) NOT NULL,
    machine_id      VARCHAR(64),
    recorded_at     TIMESTAMP NOT NULL,
    tag_value       DOUBLE PRECISION,
    quality_flag    VARCHAR(32),
    source_file_id  VARCHAR(64),
    CONSTRAINT fk_tag_rt_info
        FOREIGN KEY (tag_id) REFERENCES tag_info (tag_id),
    CONSTRAINT fk_tag_rt_machine
        FOREIGN KEY (machine_id) REFERENCES machine (machine_id),
    CONSTRAINT fk_tag_rt_file
        FOREIGN KEY (source_file_id) REFERENCES file (file_id)
);
