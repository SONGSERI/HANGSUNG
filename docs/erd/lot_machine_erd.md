## LOT–Machine ERD

```mermaid

erDiagram

    LOT {
        string lot_name PK
        string product_id
        int rev
        string plan_id
        string machine
        int stage_no
        int lane_no
        string mjs_id
        datetime report_date
        int output
    }

    LOT_TIME_SUMMARY {
        string lot_name PK
        float power_on
        float change_time
        float prod_view
        float maintenance
        float data_edit
        float unit_adjust
        float idle_time
        float prod_time
        float actual_time
        float load_time
        float board_recog_time
        float mount_time
        float total_stop_time

        float f_wait
        float r_wait
        float s_wait
        float c_wait
        float b_wait
        float p_wait

        float sc_stop
        float sce_stop
        float other_stop
        float conv_stop
        float brcg_stop
        float trouble_stop
        float mhrcg_stop
        float fb_stop
        float bndrcg_stop

        float cp_err
        float cr_err
        float cd_err
        float cm_err
        float ct_err
        float trs_err
        float prd_stop
        float judge_stop
        float other_line_stop
        float bnd_stop

        float mc_fwait
        float mc_rwait
        float joint_pass_wait
        float ppi_stop
        float simulation
    }

    LOT_CYCLE_TIME {
        string lot_name PK
        float cycle_time_1
        float cycle_time_2
        float cycle_time_3
    }

    LOT_COUNT_SUMMARY {
        string lot_name PK
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

        int total_pickup
        int pickup_miss
        int retry_miss
        int drop_miss
        int mount_miss
        int head_miss
        int trs_miss

        int lot_board
        int lot_module

        int mc_fwait_cnt
        int mc_rwait_cnt
        int joint_pass_wait_cnt

        int total_mount
        int ppi_stop_cnt
        int ppi_err_cnt
    }

    LOT_RESOURCE_USAGE {
        string lot_name PK
        string resource_type PK   "FEEDER / NOZZLE"
        string resource_code PK

        int head_no
        int feeder_addr
        int feeder_slot
        string part_no

        int pickup_cnt
        int p_miss
        int r_miss
        int d_miss
        int m_miss
        int h_miss
        int trs_miss
        int mount_cnt
        int ppi_err
    }

    LOT_INSPECTION {
        string lot_name PK
        int bad_board
        int bad_block
        int bad_parts
        int ok_parts
        int retry_board

        int lot_block
        int lot_bad_board
        int lot_bad_block
        int lot_bad_parts
        int lot_ok_parts
        int lot_retry_board
    }

    LOT ||--|| LOT_TIME_SUMMARY : has
    LOT ||--|| LOT_COUNT_SUMMARY : has
    LOT ||--|| LOT_CYCLE_TIME : has
    LOT ||--o{ LOT_RESOURCE_USAGE : uses
    LOT ||--|| LOT_INSPECTION : inspects
