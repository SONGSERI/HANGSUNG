# LOT–Machine ERD

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
    ...
