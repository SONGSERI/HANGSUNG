import numpy as np
import pandas as pd


# =====================================================
# Base View Builder (LOT × MACHINE)
# =====================================================
def build_lot_machine_view(
    lot: pd.DataFrame,
    lot_machine: pd.DataFrame,
    machine: pd.DataFrame,
    time_summary: pd.DataFrame,
    pickup_summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    LOT × MACHINE 기준 분석용 베이스 테이블 생성
    """
    view = (
        lot_machine
        .merge(lot, on="lot_id", how="left")
        .merge(machine, on="machine_id", how="left")
        .merge(time_summary, on="lot_machine_id", how="left")
        .merge(pickup_summary, on="lot_machine_id", how="left")
    )

    # datetime 보정 (안전장치)
    for col in ["start_time", "end_time"]:
        if col in view.columns:
            view[col] = pd.to_datetime(view[col], errors="coerce")

    return view


# =====================================================
# Production Analysis
# =====================================================
def production_kpis(lot_machine_view: pd.DataFrame) -> dict:
    """
    생산 KPI 계산
    - UPS
    - LOT 단위 생산량
    - 가동/정지 시간 요약
    """
    view = lot_machine_view.copy()

    # 기본 방어
    view["running_time_sec"] = view["running_time_sec"].replace(0, np.nan)
    view["total_pickup_count"] = view["total_pickup_count"].fillna(0)

    # KPI 계산
    view["ups"] = view["total_pickup_count"] / view["running_time_sec"]
    view["actual_qty"] = view["total_pickup_count"]

    lot_level = (
        view.groupby(
            ["lot_id", "lot_name", "line_id"],
            dropna=False
        )
        .agg(
            start_time=("start_time", "min"),
            end_time=("end_time", "max"),
            running_time_sec=("running_time_sec", "sum"),
            total_stop_time_sec=("total_stop_time_sec", "sum"),
            actual_qty=("actual_qty", "sum"),
            ups=("ups", "mean"),
        )
        .reset_index()
    )

    # 파생 지표
    lot_level["running_time_hr"] = lot_level["running_time_sec"] / 3600
    lot_level["stop_time_hr"] = lot_level["total_stop_time_sec"] / 3600

    return {
        "lot_level": lot_level
    }
