## LOT–Machine ERD

```mermaid


erDiagram

    EQUIPMENT {
        int equipment_id PK
        string equipment_type
        string model
        string serial_no
    }

    STAGE {
        int stage_id PK
        int equipment_id FK
        int stage_no
        string stage_name
    }

    LANE {
        int lane_id PK
        int stage_id FK
        int lane_no
        string lane_side
    }

    LOT {
        int lot_id PK
        int equipment_id FK
        int stage_id FK
        int lane_id FK
        string lot_name
        datetime start_time
        datetime end_time
    }

    EQUIPMENT_RESOURCE {
        int resource_id PK
        int equipment_id FK
        string resource_type
        string model
        string serial_no
    }

    LOT_RESOURCE_USAGE {
        int usage_id PK
        int lot_id FK
        int resource_id FK
        int pickup_cnt
        int mount_cnt
        int error_cnt
    }

    EQUIPMENT ||--o{ STAGE : has
    STAGE ||--o{ LANE : has
    LANE ||--o{ LOT : produces

    EQUIPMENT ||--o{ LOT : runs
    EQUIPMENT ||--o{ EQUIPMENT_RESOURCE : owns

    LOT ||--o{ LOT_RESOURCE_USAGE : records
    EQUIPMENT_RESOURCE ||--o{ LOT_RESOURCE_USAGE : used_in
