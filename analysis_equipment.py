from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class EquipmentAnomalyParams:
    min_total_stop_sec: int = 300

    w_stop_time: float = 1.0
    w_stop_count: float = 0.5
    w_error_ratio: float = 1.0

    anomaly_method: str = "zscore"
    anomaly_threshold: float = 3.0


def _zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or np.isnan(std):
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def _iqr(series: pd.Series) -> pd.Series:
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    if iqr == 0 or np.isnan(iqr):
        return pd.Series(0.0, index=series.index)
    return (series - q3) / iqr


def run_equipment_anomaly_analysis(
    lot_machine_view: pd.DataFrame,
    stop_log: pd.DataFrame,
    stop_reason: pd.DataFrame,
    params: EquipmentAnomalyParams,
) -> pd.DataFrame:
    merged = (
        stop_log.merge(stop_reason, on="stop_reason_code", how="left")
        .merge(
            lot_machine_view[["lot_machine_id", "machine_id", "line_id"]],
            on="lot_machine_id",
            how="left",
        )
    )

    summary = (
        merged.groupby(["line_id", "machine_id"], dropna=False)
        .agg(
            total_stop_sec=("duration_sec", "sum"),
            total_stop_count=("stop_count", "sum"),
        )
        .reset_index()
    )

    reason_ratio = (
        merged.groupby(["machine_id", "stop_reason_group"], dropna=False)
        .agg(reason_stop_sec=("duration_sec", "sum"))
        .reset_index()
        .pivot_table(
            index="machine_id",
            columns="stop_reason_group",
            values="reason_stop_sec",
            fill_value=0,
        )
        .reset_index()
    )

    df = summary.merge(reason_ratio, on="machine_id", how="left")
    df = df[df["total_stop_sec"] >= params.min_total_stop_sec]

    if "ERROR" not in df.columns:
        df["ERROR"] = 0.0

    df["raw_score"] = (
        params.w_stop_time * df["total_stop_sec"]
        + params.w_stop_count * df["total_stop_count"]
        + params.w_error_ratio * df["ERROR"]
    )

    score_fn = _zscore if params.anomaly_method == "zscore" else _iqr
    df["anomaly_score"] = score_fn(df["raw_score"].fillna(0))
    df["is_anomaly"] = df["anomaly_score"].abs() >= params.anomaly_threshold

    return df.sort_values(["is_anomaly", "anomaly_score"], ascending=[False, False])
