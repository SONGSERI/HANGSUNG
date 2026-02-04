from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class QualityRiskParams:
    min_pickup_count: int = 1000

    w_pickup: float = 1.0
    w_recognition: float = 1.0
    w_pre_pickup: float = 0.5
    w_stop_ratio: float = 0.5

    risk_bins: tuple = (0.0, 0.02, 0.05, 1.0)
    risk_labels: tuple = ("LOW", "MEDIUM", "HIGH")

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


def run_quality_risk_analysis(
    lot,
    lot_machine,
    machine,
    time_summary,
    pickup_summary,
    params: QualityRiskParams,
) -> pd.DataFrame:
    view = (
        lot_machine.merge(lot, on="lot_id", how="left")
        .merge(machine, on="machine_id", how="left")
        .merge(time_summary, on="lot_machine_id", how="left")
        .merge(pickup_summary, on="lot_machine_id", how="left")
    )

    view = view[view["total_pickup_count"].fillna(0) >= params.min_pickup_count]

    view["pickup_error_rate"] = view["pickup_error_count"] / view["total_pickup_count"]
    view["recognition_error_rate"] = view["recognition_error_count"] / view["total_pickup_count"]
    view["pre_pickup_error_rate"] = (
        view["pre_pickup_inspection_error_count"] / view["total_pickup_count"]
    )

    view["stop_time_ratio"] = (
        view["total_stop_time_sec"]
        / (view["running_time_sec"] + view["total_stop_time_sec"]).replace(0, np.nan)
    )

    view["risk_score"] = (
        params.w_pickup * view["pickup_error_rate"].fillna(0)
        + params.w_recognition * view["recognition_error_rate"].fillna(0)
        + params.w_pre_pickup * view["pre_pickup_error_rate"].fillna(0)
        + params.w_stop_ratio * view["stop_time_ratio"].fillna(0)
    )

    view["risk_level"] = pd.cut(
        view["risk_score"],
        bins=params.risk_bins,
        labels=params.risk_labels,
        include_lowest=True,
    )

    score_fn = _zscore if params.anomaly_method == "zscore" else _iqr
    view["risk_anomaly_score"] = score_fn(view["risk_score"].fillna(0))
    view["is_anomaly"] = view["risk_anomaly_score"].abs() >= params.anomaly_threshold

    return view.sort_values(["risk_level", "risk_score"], ascending=[False, False])
