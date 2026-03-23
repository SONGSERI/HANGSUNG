아래 그대로 복사해서 사용하면 됩니다.

```mermaid
erDiagram
    %% =========================
    %% HEADER TABLES (파일 이력)
    %% =========================

    FA_2_MARKING_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_14_AOI_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_24_SPI_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_26_34_MOUNTER_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_35_MOI_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_42_AOI_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    %% =========================
    %% DETAIL TABLES (파싱 데이터)
    %% =========================

    FA_2_MARKING_DTL {
        bigint _Index
        varchar PLANT_CD FK
        varchar WC_CD FK
        varchar FILE_NM FK
        timestamp FILE_DT
        varchar MACH_CD
        varchar VALUE
        timestamp MAKE_DT
    }

    FA_14_AOI_DTL {
        bigint _Index
        varchar PLANT_CD FK
        varchar WC_CD FK
        varchar FILE_NM FK
        timestamp FILE_DT
        varchar MACH_CD
        varchar LANE
        varchar DATA_TYPE
        varchar BARCODE
        varchar PANELBARCODE
        varchar ENDDATETIME
        varchar PCBMODEL
    }

    FA_24_SPI_DTL {
        bigint _Index
        varchar PLANT_CD FK
        varchar WC_CD FK
        varchar FILE_NM FK
        timestamp FILE_DT
        varchar MACH_CD
        varchar LANE
        varchar DATA_TYPE
        varchar PANELBARCODE
        varchar MODEL
        varchar MACHINERESULT
        varchar REVIEWRESULT
    }

    FA_26_34_MOUNTER_DTL {
        bigint _Index
        varchar PLANT_CD
        varchar WC_CD
        varchar FILE_NM
        timestamp FILE_DT
        varchar MACH_CD
        varchar STAGE
        varchar LANE
        varchar OUTPUT
        varchar LOT_NM
        varchar SECTION
        varchar ROW_NUM
    }

    FA_35_MOI_DTL {
        bigint _Index
        varchar PLANT_CD FK
        varchar WC_CD FK
        varchar FILE_NM FK
        timestamp FILE_DT
        varchar MACH_CD
        varchar LANE
        varchar DATA_TYPE
        varchar BARCODE
        varchar PANELBARCODE
        varchar ENDDATETIME
        varchar PCBMODEL
    }

    FA_42_AOI_DTL {
        bigint _Index
        varchar PLANT_CD FK
        varchar WC_CD FK
        varchar FILE_NM FK
        timestamp FILE_DT
        varchar MACH_CD
        varchar LANE
        varchar DATA_TYPE
        varchar BARCODE
        varchar PANELBARCODE
        varchar ENDDATETIME
        varchar PCBMODEL
    }

    %% =========================
    %% RAW TAG TABLE
    %% =========================

    _mounter_tag {
        timestamptz _devicedate
        varchar _linecode
        varchar _workcode
        varchar _equipcode
        text _type
        text _tagname
        text _value
        timestamptz _insertdate
    }

    %% =========================
    %% RELATION (LOGICAL FK)
    %% =========================

    FA_2_MARKING_HDR ||--o{ FA_2_MARKING_DTL : "PLANT_CD, WC_CD, FILE_NM"
    FA_14_AOI_HDR   ||--o{ FA_14_AOI_DTL   : "PLANT_CD, WC_CD, FILE_NM"
    FA_24_SPI_HDR   ||--o{ FA_24_SPI_DTL   : "PLANT_CD, WC_CD, FILE_NM"
    FA_26_34_MOUNTER_HDR ||--o{ FA_26_34_MOUNTER_DTL : "PLANT_CD, WC_CD, FILE_NM"
    FA_35_MOI_HDR   ||--o{ FA_35_MOI_DTL   : "PLANT_CD, WC_CD, FILE_NM"
    FA_42_AOI_HDR   ||--o{ FA_42_AOI_DTL   : "PLANT_CD, WC_CD, FILE_NM"

    %% =========================
    %% WEAK RELATION (비정형 연계)
    %% =========================

    FA_26_34_MOUNTER_DTL .. _mounter_tag : "LINE/WORKCODE, MACH/EQUIP, TIME"
```
