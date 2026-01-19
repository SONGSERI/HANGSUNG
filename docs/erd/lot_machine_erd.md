## LOT–Machine ERD

```mermaid

erDiagram

    LOT {
        string lot_id
        string machine
        string lane
        string product_id
        string rev
        datetime start_time
        datetime end_time
    }

    LOT_TIME_SUMMARY {
        string lot_id
        float prod_time
        float actual_time
        float total_stop_time
        float mount_time
        float rwait_time
    }

    LOT_COUNT_SUMMARY {
        string lot_id
        int board_cnt
        int module_cnt
        int total_pickup_cnt
        int total_mount_cnt
        int pickup_miss_cnt
        int retry_miss_cnt
    }

    LOT_STOP {
        string lot_id
        string stop_type
        float stop_time
        int stop_count
    }

    FEEDER_STAT {
        string lot_id
        int head_table_no
        int feeder_no
        string part_no
        int pickup_cnt
        int pmiss_cnt
        int rmiss_cnt
        int mount_cnt
    }

    NOZZLE_STAT {
        string lot_id
        int head_no
        string nozzle_no
        int pickup_cnt
        int pmiss_cnt
        int mount_cnt
    }

    LOT ||--|| LOT_TIME_SUMMARY : has
    LOT ||--|| LOT_COUNT_SUMMARY : has
    LOT ||--o{ LOT_STOP : has
    LOT ||--o{ FEEDER_STAT : has
    LOT ||--o{ NOZZLE_STAT : has

