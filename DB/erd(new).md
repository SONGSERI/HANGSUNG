```mermaid
erDiagram

    FA_2_MARKING_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_2_MARKING_DTL {
        bigint _Index
        varchar PLANT_CD
        varchar WC_CD
        varchar FILE_NM
        timestamp FILE_DT
    }

    FA_14_AOI_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_14_AOI_DTL {
        bigint _Index
        varchar PLANT_CD
        varchar WC_CD
        varchar FILE_NM
        timestamp FILE_DT
    }

    FA_24_SPI_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_24_SPI_DTL {
        bigint _Index
        varchar PLANT_CD
        varchar WC_CD
        varchar FILE_NM
        timestamp FILE_DT
    }

    FA_26_34_MOUNTER_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_26_34_MOUNTER_DTL {
        bigint _Index
        varchar PLANT_CD
        varchar WC_CD
        varchar FILE_NM
        timestamp FILE_DT
    }

    FA_35_MOI_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_35_MOI_DTL {
        bigint _Index
        varchar PLANT_CD
        varchar WC_CD
        varchar FILE_NM
        timestamp FILE_DT
    }

    FA_42_AOI_HDR {
        bigint _Index
        varchar PLANT_CD PK
        varchar WC_CD PK
        varchar FILE_NM PK
        timestamp MAKE_DT
        char POST_FLAG
    }

    FA_42_AOI_DTL {
        bigint _Index
        varchar PLANT_CD
        varchar WC_CD
        varchar FILE_NM
        timestamp FILE_DT
    }

    %% 관계 (반드시 마지막에 위치)

    FA_2_MARKING_HDR ||--o{ FA_2_MARKING_DTL
    FA_14_AOI_HDR ||--o{ FA_14_AOI_DTL
    FA_24_SPI_HDR ||--o{ FA_24_SPI_DTL
    FA_26_34_MOUNTER_HDR ||--o{ FA_26_34_MOUNTER_DTL
    FA_35_MOI_HDR ||--o{ FA_35_MOI_DTL
    FA_42_AOI_HDR ||--o{ FA_42_AOI_DTL
