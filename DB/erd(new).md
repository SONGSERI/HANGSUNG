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

    FA_2_MARKING_HDR ||--o{ FA_2_MARKING_DTL : contains
    FA_14_AOI_HDR ||--o{ FA_14_AOI_DTL : contains
    FA_24_SPI_HDR ||--o{ FA_24_SPI_DTL : contains
    FA_26_34_MOUNTER_HDR ||--o{ FA_26_34_MOUNTER_DTL : contains
    FA_35_MOI_HDR ||--o{ FA_35_MOI_DTL : contains
    FA_42_AOI_HDR ||--o{ FA_42_AOI_DTL : contains
