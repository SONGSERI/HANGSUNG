## LOT–Machine ERD

```mermaid

erDiagram

    LOT {
        string lot_name PK            "EXIST"
        string product_code           "EXIST"
        string machine_no             "EXIST"
        string stage_no               "EXIST"
        string lane_no                "EXIST"
        string head_group             "EXIST"
        datetime report_date          "EXIST"
        string log_type               "EXIST"

        string work_order             "NEW"
        string model_code             "NEW"
        string line_code              "NEW"
        string shift_code             "NEW"
        datetime lot_start_time       "NEW"
        datetime lot_end_time         "NEW"
    }

    LOT_TIME_SUMMARY {
        string lot_name PK            "EXIST"
        float prod_time               "EXIST"
        float idle_time               "EXIST"
        float stop_time               "EXIST"
        float mount_time              "EXIST"
        float actual_time             "EXIST"

        float planned_time            "NEW"
        float availability_rate       "NEW"
        float performance_rate        "NEW"
        float oee_lite                "NEW"
    }

    LOT_COUNT_SUMMARY {
        string lot_name PK            "EXIST"
        int board_count               "EXIST"
        int module_count              "EXIST"
        int pickup_count              "EXIST"
        int mount_count               "EXIST"
        int pickup_miss_count         "EXIST"

        int good_count                "NEW"
        int reject_count              "NEW"
        float yield_rate              "NEW"
    }

    LOT_RESOURCE_USAGE {
        string lot_name PK            "EXIST"
        string resource_type          "EXIST"
        string resource_code          "EXIST"
        int pickup_count              "EXIST"
        int mount_count               "EXIST"
        int miss_count                "EXIST"

        string error_type             "NEW"
        string error_code             "NEW"
        int error_count               "NEW"
        float usage_time              "NEW"
        datetime first_error_time     "NEW"
        datetime last_error_time      "NEW"
    }

    LOT_STOP_EVENT {
        string lot_name FK            "NEW"
        string machine_no             "NEW"
        string stage_no               "NEW"
        string lane_no                "NEW"
        datetime stop_start_time      "NEW"
        datetime stop_end_time        "NEW"
        float stop_duration           "NEW"
        string stop_category          "NEW"
        string stop_code              "NEW"
        string stop_reason            "NEW"
    }

    LOT ||--|| LOT_TIME_SUMMARY : has
    LOT ||--|| LOT_COUNT_SUMMARY : has
    LOT ||--o{ LOT_RESOURCE_USAGE : uses
    LOT ||--o{ LOT_STOP_EVENT : causes
