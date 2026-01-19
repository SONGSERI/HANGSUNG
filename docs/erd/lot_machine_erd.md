## LOT–Machine ERD

```mermaid
erDiagram
    LOT {
        string lot_id
        string machine_no
        string lane
    }

    PICKUP_FEEDER_STAT {
        string lot_id
        int head_table_no
        int head_no
        int feeder_no
        string part_no
    }

    LOT ||--o{ PICKUP_FEEDER_STAT : has
