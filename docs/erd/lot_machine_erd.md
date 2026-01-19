# LOT – Machine ERD

```mermaid
erDiagram
    LOT {
        string lot_id PK
        string line_id
        string lane
        datetime start_time
        datetime end_time
        int total_pickup_cnt
        int total_error_cnt
        int spoilage_ppm
    }

    ERROR_SUMMARY {
        string lot_id FK
        string error_type PK
        int error_cnt
    }

    MACHINE_PRODUCTION {
        string lot_id FK
        string machine_no PK
        string stage
        int panel_cnt
        int pattern_cnt
        float running_rate
        int running_time_sec
        int real_running_time_sec
        int stop_time_sec
        int pickup_cnt
        int error_cnt
        int spoilage_ppm
    }

    PICKUP_STAT_MACHINE {
        string lot_id FK
        string machine_no PK
        int pickup_cnt
        int error_cnt
        float error_rate
        int spoilage_ppm
    }

    MACHINE_STOP_DETAIL {
        string lot_id FK
        string machine_no FK
        string stop_type PK
        int stop_time_sec
        int stop_count
    }

    PICKUP_STAT_FEEDER {
        string lot_id FK
        string machine_no FK
        int head_table_no PK
        int feeder_no PK
        string side
        string part_no
        string library_name
        int pickup_cnt
        int error_cnt
        int pickup_err_cnt
        int recognition_err_cnt
        int spoilage_ppm
    }

    LOT ||--o{ ERROR_SUMMARY : has
    LOT ||--o{ MACHINE_PRODUCTION : has
    LOT ||--o{ PICKUP_STAT_MACHINE : has
    MACHINE_PRODUCTION ||--o{ MACHINE_STOP_DETAIL : generates
    MACHINE_PRODUCTION ||--o{ PICKUP_STAT_FEEDER : contains
