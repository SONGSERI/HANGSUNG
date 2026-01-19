## LOT–Machine ERD

```mermaid

erDiagram

    LOT {
        string lot_name PK
        string product_code
        datetime start_time
        datetime end_time
        string machine_code
    }

    MACHINE_CONTEXT {
        string machine_code PK
        string machine_model
        string stage_no
        string lane_no
        string lane_side
    }

    LOT_TIME_SUMMARY {
        string lot_name PK
        float prod_time
        float idle_time
        float stop_time
        float mount_time
        float actual_time
    }

    LOT_COUNT_SUMMARY {
        string lot_name PK
        int board_cnt
        int module_cnt
        int pickup_cnt
        int mount_cnt
        int pickup_miss_cnt
    }

    LOT_RESOURCE_USAGE {
        string lot_name PK
        string resource_type
        string resource_code
        int pickup_cnt
        int mount_cnt
        int miss_cnt
    }

    LOT ||--|| MACHINE_CONTEXT : runs_on
    LOT ||--|| LOT_TIME_SUMMARY : has
    LOT ||--|| LOT_COUNT_SUMMARY : has
    LOT ||--o{ LOT_RESOURCE_USAGE : uses

