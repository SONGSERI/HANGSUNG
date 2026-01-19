erDiagram

    RAW_LOG {
        string raw_log_id
        string lot_id
        string machine_no
        string log_text
        datetime collected_at
        boolean parsed_yn
    }

    LOT {
        string lot_id
        string machine_no
        string lane
        datetime period_from
        datetime period_to
    }

    LOT_PRODUCTION_SUMMARY {
        string lot_id
        int prod_time_sec
        int actual_time_sec
        int total_stop_time_sec
        int board_cnt
        int module_cnt
        int total_mount_cnt
        int pickup_miss_cnt
        int retry_miss_cnt
    }

    LOT_STOP_DETAIL {
        string lot_id
        string stop_code
        int stop_time_sec
        int stop_count
    }

    PICKUP_FEEDER_STAT {
        string lot_id
        int head_table_no
        int head_no
        int feeder_no
        string part_no
        int pickup_cnt
        int pmiss_cnt
        int rmiss_cnt
        int mount_cnt
    }

    PICKUP_NOZZLE_STAT {
        string lot_id
        int head_table_no
        int head_no
        string nozzle_no
        int pickup_cnt
        int pmiss_cnt
    }

    RAW_LOG ||--|| LOT : creates
    LOT ||--|| LOT_PRODUCTION_SUMMARY : has
    LOT ||--o{ LOT_STOP_DETAIL : has
    LOT ||--o{ PICKUP_FEEDER_STAT : has
    LOT ||--o{ PICKUP_NOZZLE_STAT : has
