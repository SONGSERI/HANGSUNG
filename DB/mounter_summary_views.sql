DROP MATERIALIZED VIEW IF EXISTS public.mv_mounter_daily_summary;
DROP MATERIALIZED VIEW IF EXISTS public.mv_mounter_machine_summary;
DROP MATERIALIZED VIEW IF EXISTS public.mv_mounter_process_summary;
DROP MATERIALIZED VIEW IF EXISTS public.mv_mounter_lot_summary;
DROP MATERIALIZED VIEW IF EXISTS public.mv_mounter_tag_machine_summary;
DROP MATERIALIZED VIEW IF EXISTS public.mv_mounter_quality_machine_summary;

CREATE MATERIALIZED VIEW public.mv_mounter_daily_summary AS
SELECT
    DATE("FILE_DT") AS day,
    COUNT(*) AS total_rows,
    SUM(COALESCE(NULLIF(regexp_replace("OUTPUT"::text, '[^0-9\.-]', '', 'g'), '')::numeric, 0)) AS total_output,
    COUNT(DISTINCT "MACH_CD") AS machine_count,
    COUNT(DISTINCT CONCAT(COALESCE("LANE", '-'), ':', COALESCE("STAGE", '-'))) AS process_count,
    COUNT(DISTINCT "LOT_NM") AS lot_count,
    MIN("FILE_DT") AS first_event_ts,
    MAX("FILE_DT") AS last_event_ts
FROM public."FA_26_34_MOUNTER_DTL"
GROUP BY 1;

CREATE INDEX IF NOT EXISTS idx_mv_mounter_daily_summary_day
ON public.mv_mounter_daily_summary(day DESC);

CREATE MATERIALIZED VIEW public.mv_mounter_machine_summary AS
SELECT
    DATE("FILE_DT") AS day,
    "MACH_CD" AS machine_id,
    "LANE" AS line_id,
    "STAGE" AS stage_no,
    COUNT(*) AS production_rows,
    SUM(COALESCE(NULLIF(regexp_replace("OUTPUT"::text, '[^0-9\.-]', '', 'g'), '')::numeric, 0)) AS output_qty,
    COUNT(DISTINCT "LOT_NM") AS lot_count,
    MIN("FILE_DT") AS first_event_ts,
    MAX("FILE_DT") AS last_event_ts
FROM public."FA_26_34_MOUNTER_DTL"
GROUP BY 1, 2, 3, 4;

CREATE INDEX IF NOT EXISTS idx_mv_mounter_machine_summary_day
ON public.mv_mounter_machine_summary(day DESC, machine_id);

CREATE MATERIALIZED VIEW public.mv_mounter_process_summary AS
SELECT
    DATE("FILE_DT") AS day,
    "LANE" AS line_id,
    "STAGE" AS stage_no,
    COUNT(*) AS production_rows,
    SUM(COALESCE(NULLIF(regexp_replace("OUTPUT"::text, '[^0-9\.-]', '', 'g'), '')::numeric, 0)) AS output_qty,
    COUNT(DISTINCT "MACH_CD") AS machine_count,
    COUNT(DISTINCT "LOT_NM") AS lot_count,
    MIN("FILE_DT") AS first_event_ts,
    MAX("FILE_DT") AS last_event_ts
FROM public."FA_26_34_MOUNTER_DTL"
GROUP BY 1, 2, 3;

CREATE INDEX IF NOT EXISTS idx_mv_mounter_process_summary_day
ON public.mv_mounter_process_summary(day DESC, line_id, stage_no);

CREATE MATERIALIZED VIEW public.mv_mounter_lot_summary AS
SELECT
    DATE("FILE_DT") AS day,
    "LOT_NM" AS lot_id,
    COUNT(*) AS production_rows,
    SUM(COALESCE(NULLIF(regexp_replace("OUTPUT"::text, '[^0-9\.-]', '', 'g'), '')::numeric, 0)) AS output_qty,
    COUNT(DISTINCT "MACH_CD") AS machine_count,
    COUNT(DISTINCT "STAGE") AS stage_count,
    COUNT(DISTINCT "LANE") AS line_count,
    MIN("FILE_DT") AS first_event_ts,
    MAX("FILE_DT") AS last_event_ts
FROM public."FA_26_34_MOUNTER_DTL"
GROUP BY 1, 2;

CREATE INDEX IF NOT EXISTS idx_mv_mounter_lot_summary_day
ON public.mv_mounter_lot_summary(day DESC, lot_id);

CREATE MATERIALIZED VIEW public.mv_mounter_tag_machine_summary AS
SELECT
    DATE("_devicedate") AS day,
    "_equipcode" AS machine_id,
    "_linecode" AS line_id,
    COUNT(*) AS tag_events,
    SUM(CASE WHEN UPPER("_tagname") LIKE '%SETUP%' OR UPPER("_tagname") LIKE '%CHANGEOVER%' OR UPPER("_tagname") LIKE '%TEACH%' OR UPPER("_tagname") LIKE '%CALIB%' OR UPPER("_tagname") LIKE '%INITIAL%' THEN 1 ELSE 0 END) AS setup_events,
    SUM(CASE WHEN UPPER("_tagname") LIKE '%FEEDER%' OR UPPER("_tagname") LIKE '%FDR%' OR UPPER("_tagname") LIKE '%REEL%' OR UPPER("_tagname") LIKE '%SUPPLY%' OR UPPER("_tagname") LIKE '%FEED%' THEN 1 ELSE 0 END) AS feeder_error_events,
    SUM(CASE WHEN UPPER("_tagname") LIKE '%PICKUP%' OR UPPER("_tagname") LIKE '%SUCTION%' OR UPPER("_tagname") LIKE '%NOZZLE%' OR UPPER("_tagname") LIKE '%VACUUM%' OR UPPER("_tagname") LIKE '%CPErr%' THEN 1 ELSE 0 END) AS pickup_error_events,
    SUM(CASE WHEN UPPER("_tagname") LIKE '%RECOG%' OR UPPER("_tagname") LIKE '%VISION%' OR UPPER("_tagname") LIKE '%MARK%' OR UPPER("_tagname") LIKE '%ALIGN%' OR UPPER("_tagname") LIKE '%CRErr%' THEN 1 ELSE 0 END) AS recog_error_events,
    SUM(CASE WHEN UPPER("_tagname") LIKE '%PLACE%' OR UPPER("_tagname") LIKE '%OFFSET%' OR UPPER("_tagname") LIKE '%SHIFT%' THEN 1 ELSE 0 END) AS place_error_events,
    SUM(CASE WHEN UPPER("_tagname") LIKE '%TRANSFER%' OR UPPER("_tagname") LIKE '%CONVEYOR%' OR UPPER("_tagname") LIKE '%BUFFER%' OR UPPER("_tagname") LIKE '%INTERLOCK%' OR UPPER("_tagname") LIKE '%CTErr%' THEN 1 ELSE 0 END) AS transfer_error_events,
    SUM(CASE WHEN UPPER("_tagname") LIKE '%WAIT%' THEN 1 ELSE 0 END) AS wait_events,
    SUM(CASE WHEN UPPER("_tagname") LIKE '%STOP%' OR UPPER("_tagname") LIKE '%ERR%' THEN 1 ELSE 0 END) AS stop_events
FROM public."_mounter_tag"
GROUP BY 1, 2, 3;

CREATE INDEX IF NOT EXISTS idx_mv_mounter_tag_machine_summary_day
ON public.mv_mounter_tag_machine_summary(day DESC, machine_id);

CREATE MATERIALIZED VIEW public.mv_mounter_quality_machine_summary AS
WITH quality_union AS (
    SELECT DATE("FILE_DT") AS day, "MACH_CD" AS machine_id, "LANE" AS line_id,
           "MACHINERESULT" AS machine_result, "REVIEWRESULT" AS review_result, "CALLRESULT" AS call_result
    FROM public."FA_14_AOI_DTL"
    UNION ALL
    SELECT DATE("FILE_DT") AS day, "MACH_CD" AS machine_id, "LANE" AS line_id,
           "MACHINERESULT" AS machine_result, "REVIEWRESULT" AS review_result, "CALLRESULT" AS call_result
    FROM public."FA_42_AOI_DTL"
    UNION ALL
    SELECT DATE("FILE_DT") AS day, "MACH_CD" AS machine_id, "LANE" AS line_id,
           "MACHINERESULT" AS machine_result, "REVIEWRESULT" AS review_result, "CALLRESULT" AS call_result
    FROM public."FA_35_MOI_DTL"
)
SELECT
    day,
    machine_id,
    line_id,
    COUNT(*) AS inspect_count,
    SUM(
        CASE
            WHEN UPPER(COALESCE(machine_result, '')) LIKE '%FAIL%'
              OR UPPER(COALESCE(machine_result, '')) LIKE '%NG%'
              OR UPPER(COALESCE(machine_result, '')) LIKE '%ERR%'
              OR UPPER(COALESCE(machine_result, '')) LIKE '%BAD%'
              OR UPPER(COALESCE(machine_result, '')) LIKE '%REWORK%'
              OR UPPER(COALESCE(review_result, '')) LIKE '%FAIL%'
              OR UPPER(COALESCE(review_result, '')) LIKE '%NG%'
              OR UPPER(COALESCE(review_result, '')) LIKE '%ERR%'
              OR UPPER(COALESCE(review_result, '')) LIKE '%BAD%'
              OR UPPER(COALESCE(call_result, '')) LIKE '%FAIL%'
              OR UPPER(COALESCE(call_result, '')) LIKE '%NG%'
              OR UPPER(COALESCE(call_result, '')) LIKE '%ERR%'
            THEN 1 ELSE 0
        END
    ) AS fail_count
FROM quality_union
GROUP BY 1, 2, 3;

CREATE INDEX IF NOT EXISTS idx_mv_mounter_quality_machine_summary_day
ON public.mv_mounter_quality_machine_summary(day DESC, machine_id);
