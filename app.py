import pandas as pd
import streamlit as st

from data_layer import generate_sample_data, load_raw_data
from transform import build_clean_views, build_component_fact, build_feature_marts, build_inspection_fact, build_stop_event_fact, build_tag_event_fact
from ui_tabs import _css, render_equipment_screen, render_rca, render_summary


def _build_rca_demo_clean(raw):
    clean = build_clean_views(raw)
    shop = clean.get("vw_shopfloor_event_fact", pd.DataFrame()).copy()
    if shop.empty and "fa_26_34_mounter_dtl" in raw:
        shop = clean.get("vw_mounter_item_fact", pd.DataFrame()).copy()
    clean["vw_shopfloor_event_fact"] = shop
    clean["vw_stop_event_fact"] = build_stop_event_fact(raw)
    clean["vw_inspection_event_fact"] = build_inspection_fact(raw)
    clean["vw_tag_event_fact"] = build_tag_event_fact(raw)
    clean["vw_component_error_fact"] = build_component_fact(raw)
    return clean


def main():
    st.set_page_config(layout="wide", page_title="SMT 제조 분석 워크벤치", page_icon="📈")
    _css()
    st.markdown('<div class="hero"><h1>SMT 제조 분석 워크벤치</h1><p>Mounter 데이터 요약 → 설비/공정/LOT 판단 → 개선 우선순위</p></div>', unsafe_allow_html=True)
    sample = False
    try:
        raw = load_raw_data("전체")
        if not raw or all(isinstance(v, pd.DataFrame) and v.empty for k, v in raw.items() if k != "_meta"):
            raw = generate_sample_data()
            sample = True
    except Exception:
        raw = generate_sample_data()
        sample = True
    clean = build_clean_views(raw)
    marts = build_feature_marts(clean)
    rca_source = clean
    rca_marts = marts
    has_rca_data = any(
        not clean.get(key, pd.DataFrame()).empty
        for key in ["vw_stop_event_fact", "vw_inspection_event_fact", "vw_tag_event_fact", "vw_component_error_fact"]
    )
    rca_sample_mode = not has_rca_data
    if rca_sample_mode:
        rca_raw = generate_sample_data()
        rca_source = _build_rca_demo_clean(rca_raw)
        rca_marts = build_feature_marts(rca_source)
    tabs = st.tabs(["데이터 요약", "문제 분석 및 개선", "RCA 설명"])
    with tabs[0]:
        render_summary(raw, clean, marts, sample)
    with tabs[1]:
        render_equipment_screen(clean, marts)
    with tabs[2]:
        render_rca(rca_source, rca_marts, rca_sample_mode)


if __name__ == "__main__":
    main()
