## LOT–Machine ERD

```mermaid


erDiagram

    EQUIPMENT {
        string equipment_code PK
        string equipment_type
        string model
        string serial_no
    }

    STAGE {
        string equipment_code PK
        int stage_no PK
    }

    LANE {
        string equipment_code PK
        int stage_no PK
        int lane_no PK
        string lane_side
    }

    LOT {
        string lot_name PK
        string equipment_code FK
        int stage_no FK
        int lane_no FK
        datetime start_time
        datetime end_time
    }

    EQUIPMENT_RESOURCE {
        string resource_code PK
        string equipment_code FK
        string resource_type
        string model
        string serial_no
    }

    LOT_RESOURCE_USAGE {
        string lot_name FK
        string resource_code FK
        int pickup_cnt
        int mount_cnt
        int error_cnt
    }

    EQUIPMENT ||--o{ STAGE : has
    STAGE ||--o{ LANE : has
    LANE ||--o{ LOT : produces

    EQUIPMENT ||--o{ EQUIPMENT_RESOURCE : owns
    LOT ||--o{ LOT_RESOURCE_USAGE : records
    EQUIPMENT_RESOURCE ||--o{ LOT_RESOURCE_USAGE : used_in
