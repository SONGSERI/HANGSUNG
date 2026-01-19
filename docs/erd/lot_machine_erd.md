## ERD

```mermaid

erDiagram

   erDiagram

    LOT {
        %% RAW (LOG DIRECT)
        string lot_name PK
        string product_id
        int rev
        string plan_id
        string machine
        int stage_no
        int lane_no
        string mjs_id
        datetime report_date
        int output_qty

        %% EXTENSION (FUTURE)
        string work_order
        string model_code
        string line_code
        string shift_code
        datetime lot_start_time
        datetime lot_end_time
    }


    TIME_METRIC {
        %% RAW (LOG DIRECT)
        float power_on_time
        float change_time
        float prod_view_time
        float maintenance_time
        float data_edit_time
        float unit_adjust_time
        float idle_time
        float prod_time
        float actual_time
        float load_time
        float board_recog_time
        float mount_time
        float total_stop_time

        float f_wait_time
        float r_wait_time
        float s_wait_time
        float c_wait_time
        float b_wait_time
        float p_wait_time

        float sc_stop_time
        float sce_stop_time
        float other_stop_time
        float conv_stop_time
        float brcg_stop_time
        float trouble_time
        float mhrcg_stop_time
        float fb_stop_time
        float bndrcg_stop_time

        float cp_err_time
        float cr_err_time
        float cd_err_time
        float cm_err_time
        float ct_err_time
        float trs_err_time
        float prd_stop_time
        float judge_stop_time
        float other_line_stop_time
        float bnd_stop_time

        float mc_fwait_time
        float mc_rwait_time
        float joint_pass_wait_time
        float ppi_stop_time
        float simulation_time

        %% CALCULATED (ANALYSIS)
        float run_ratio
        float stop_ratio
        float mount_ratio
        float idle_ratio
    }


    COUNT_METRIC {
        %% RAW (LOG DIRECT)
        int board_cnt
        int module_cnt

        int f_wait_cnt
        int r_wait_cnt
        int s_wait_cnt
        int c_wait_cnt
        int b_wait_cnt
        int p_wait_cnt

        int sc_stop_cnt
        int sce_stop_cnt
        int other_stop_cnt
        int conv_stop_cnt
        int brcg_stop_cnt
        int trouble_cnt
        int mhrcg_stop_cnt
        int fb_stop_cnt
        int bndrcg_stop_cnt

        int cp_err_cnt
        int cr_err_cnt
        int cd_err_cnt
        int cm_err_cnt
        int ct_err_cnt
        int trs_err_cnt

        int total_pickup_cnt
        int pickup_miss_cnt
        int retry_miss_cnt
        int drop_miss_cnt
        int mount_miss_cnt
        int head_miss_cnt
        int trs_miss_cnt

        int lot_board_cnt
        int lot_module_cnt

        int mc_fwait_cnt
        int mc_rwait_cnt
        int joint_pass_wait_cnt

        int total_mount_cnt
        int ppi_stop_cnt
        int ppi_err_cnt

        %% CALCULATED (ANALYSIS)
        float pickup_miss_rate
        float mount_yield
        float retry_rate
    }


    CYCLE_STAT {
        %% RAW (LOG DIRECT)
        float cycle_time_1
        float cycle_time_2
        float cycle_time_3

        %% CALCULATED (ANALYSIS)
        float cycle_avg
        float cycle_std
    }


    RESOURCE_METRIC {
        %% RAW (LOG DIRECT)
        string resource_type
        int head_no
        int feeder_addr
        int feeder_slot
        int nozzle_no
        string resource_serial
        string part_no
        string library_name

        int pickup_cnt
        int p_miss_cnt
        int r_miss_cnt
        int d_miss_cnt
        int m_miss_cnt
        int h_miss_cnt
        int trs_miss_cnt
        int mount_cnt
        int ppi_err_cnt

        %% CALCULATED (ANALYSIS)
        float miss_rate
        float efficiency
        int total_error_cnt
    }


    QUALITY_SUMMARY {
        %% RAW (LOG DIRECT)
        int bad_board_cnt
        int bad_block_cnt
        int bad_parts_cnt
        int ok_parts_cnt
        int retry_board_cnt

        int lot_block_cnt
        int lot_bad_board_cnt
        int lot_bad_block_cnt
        int lot_bad_parts_cnt
        int lot_ok_parts_cnt
        int lot_retry_board_cnt

        %% CALCULATED (ANALYSIS)
        float board_yield
        float part_yield
        float retry_ratio
    }


    LOT ||--|| TIME_METRIC : has
    LOT ||--|| COUNT_METRIC : has
    LOT ||--|| CYCLE_STAT : has
    LOT ||--|| QUALITY_SUMMARY : has
    LOT ||--o{ RESOURCE_METRIC : uses




