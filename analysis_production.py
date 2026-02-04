import numpy as np
import pandas as pd


def build_lot_machine_view(
    lot, lot_machine, machine, time_summary, pickup_summary
):
    return (
        lot_machine.merge(lot, on="lot_id", how="left")
        .merge(machine, on="machine_id", how="left")
        .merge(time_summary, on="lot_machine_id", how="left")
        .merge(pickup_summary, on="lot_machine_id", how="left")
    )


def production_kpis(lot_machine_view: pd.DataFrame) -> dict:
    view = lot_machine_view.copy()

    view["ups"] = view["total_pickup_count"] / view["running_time_sec"].replace(0, np.nan)
    view["actual_qty"] = view["total_pickup_count"].fillna(0)

    lot_level = (
        view.groupby(["lot_id", "lot_name", "line_id"], dropna=False)
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

    return {"lot_level": lot_level}
