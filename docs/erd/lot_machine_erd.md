## ERD

```mermaid

erDiagram

    LOT {
        string lot_name PK "LOT 식별자"
        string product_id "제품 ID"
        int rev "제품 리비전"
        string plan_id "생산 계획 ID"
        string machine "설비 모델"
        int stage_no "Stage 번호"
        int lane_no "Lane 번호"
        string mjs_id "장비 작업(Job) ID"
        datetime report_date "리포트 생성 시각"
        int output_qty "생산 수량"
        datetime lot_start_time "LOT 시작 시각"
        datetime lot_end_time "LOT 종료 시각"

        string work_order "작업지시서 번호 (MES 추가)"
        string model_code "모델 코드 (MES 추가)"
        string line_code "라인 코드 (MES 추가)"
        string shift_code "근무조 코드 (MES 추가)"

    }


    TIME_METRIC {
        string lot_name PK, FK "LOT 식별자"

        float power_on_time "전원 ON 시간"
        float change_time "모델 변경 시간"
        float prod_view_time "생산 대기 시간"
        float maintenance_time "보전 시간"
        float data_edit_time "데이터 수정 시간"
        float unit_adjust_time "유닛 조정 시간"
        float idle_time "유휴 시간"
        float prod_time "생산 시간"
        float actual_time "실제 가동 시간"
        float load_time "로딩 시간"
        float board_recog_time "보드 인식 시간"
        float mount_time "실장 시간"
        float total_stop_time "총 정지 시간"

        float f_wait_time "전면 대기 시간"
        float r_wait_time "후면 대기 시간"
        float s_wait_time "정지 대기 시간"
        float c_wait_time "컨베이어 대기"
        float b_wait_time "버퍼 대기"
        float p_wait_time "팔레트 대기"

        float sc_stop_time "Short cycle 정지"
        float sce_stop_time "Short cycle 에러"
        float other_stop_time "기타 정지"
        float conv_stop_time "컨베이어 정지"
        float brcg_stop_time "보드 인식 정지"
        float trouble_time "트러블 정지"
        float mhrcg_stop_time "수동 인식 정지"
        float fb_stop_time "피드백 정지"
        float bndrcg_stop_time "밴드 인식 정지"

        float cp_err_time "부품 픽업 에러"
        float cr_err_time "부품 인식 에러"
        float cd_err_time "부품 낙하 에러"
        float cm_err_time "부품 실장 에러"
        float ct_err_time "툴 에러"
        float trs_err_time "트레이 에러"
        float prd_stop_time "생산 정지"
        float judge_stop_time "판정 대기"
        float other_line_stop_time "타라인 영향"
        float bnd_stop_time "밴드 정지"

        float mc_fwait_time "장비 전면 대기"
        float mc_rwait_time "장비 후면 대기"
        float joint_pass_wait_time "연결 대기"
        float ppi_stop_time "PPI 정지"
        float simulation_time "시뮬레이션 시간"

        float run_ratio "가동률 (계산하여 추가예정)"
        float stop_ratio "정지 비율 (계산하여 추가예정)"
        float mount_ratio "실장 비율 (계산하여 추가예정)"
        float idle_ratio "유휴 비율 (계산하여 추가예정)"
    }


    COUNT_METRIC {
        string lot_name PK, FK "LOT 식별자"

        int board_cnt "보드 수량"
        int module_cnt "모듈 수량"

        int f_wait_cnt "전면 대기 횟수"
        int r_wait_cnt "후면 대기 횟수"
        int s_wait_cnt "정지 대기 횟수"
        int c_wait_cnt "컨베이어 대기 횟수"
        int b_wait_cnt "버퍼 대기 횟수"
        int p_wait_cnt "팔레트 대기 횟수"

        int sc_stop_cnt "Short cycle 정지 횟수"
        int sce_stop_cnt "Short cycle 에러 횟수"
        int other_stop_cnt "기타 정지 횟수"
        int conv_stop_cnt "컨베이어 정지 횟수"
        int brcg_stop_cnt "보드 인식 정지 횟수"
        int trouble_cnt "트러블 횟수"
        int mhrcg_stop_cnt "수동 인식 정지 횟수"
        int fb_stop_cnt "피드백 정지 횟수"
        int bndrcg_stop_cnt "밴드 인식 정지 횟수"

        int cp_err_cnt "픽업 에러 횟수"
        int cr_err_cnt "인식 에러 횟수"
        int cd_err_cnt "낙하 에러 횟수"
        int cm_err_cnt "실장 에러 횟수"
        int ct_err_cnt "툴 에러 횟수"
        int trs_err_cnt "트레이 에러 횟수"

        int total_pickup_cnt "총 픽업 수량"
        int pickup_miss_cnt "픽업 실패 수량"
        int retry_miss_cnt "재시도 실패"
        int drop_miss_cnt "낙하 실패"
        int mount_miss_cnt "실장 실패"
        int head_miss_cnt "헤드 실패"
        int trs_miss_cnt "트레이 실패"

        int lot_board_cnt "LOT 보드 수량"
        int lot_module_cnt "LOT 모듈 수량"

        int mc_fwait_cnt "장비 전면 대기"
        int mc_rwait_cnt "장비 후면 대기"
        int joint_pass_wait_cnt "연결 대기"

        int total_mount_cnt "총 실장 수량"
        int ppi_stop_cnt "PPI 정지 횟수"
        int ppi_err_cnt "PPI 에러 횟수"

        float pickup_miss_rate "픽업 실패율 (계산하여 추가예정)"
        float mount_yield "실장 수율 (계산하여 추가예정)"
        float retry_rate "재시도 비율 (계산하여 추가예정)"
    }


    CYCLE_STAT {
        string lot_name PK, FK "LOT 식별자"

        float cycle_time_1 "사이클 타임 1"
        float cycle_time_2 "사이클 타임 2"
        float cycle_time_3 "사이클 타임 3"

        float cycle_avg "평균 사이클 (계산하여 추가예정)"
        float cycle_std "사이클 표준편차 (계산하여 추가예정)"
    }


    RESOURCE_METRIC {
        int resource_id PK "자원 고유 ID"
        string lot_name FK "LOT 식별자"

        string resource_type "자원 유형 (FEEDER/NOZZLE)"
        int head_no "헤드 번호"
        int feeder_addr "피더 주소"
        int feeder_slot "피더 슬롯"
        int nozzle_no "노즐 번호"
        string resource_serial "자원 시리얼"
        string part_no "부품 번호"
        string library_name "라이브러리 이름"

        int pickup_cnt "픽업 수량"
        int p_miss_cnt "픽업 실패"
        int r_miss_cnt "인식 실패"
        int d_miss_cnt "낙하 실패"
        int m_miss_cnt "실장 실패"
        int h_miss_cnt "헤드 실패"
        int trs_miss_cnt "트레이 실패"
        int mount_cnt "실장 수량"
        int ppi_err_cnt "PPI 에러"

        float miss_rate "자원 불량률 (계산하여 추가예정)"
        float efficiency "자원 효율 (계산하여 추가예정)"
        int total_error_cnt "총 에러 수 (계산하여 추가예정)"
    }


    QUALITY_SUMMARY {
        string lot_name PK, FK "LOT 식별자"

        int bad_board_cnt "불량 보드 수"
        int bad_block_cnt "불량 블록 수"
        int bad_parts_cnt "불량 부품 수"
        int ok_parts_cnt "정상 부품 수"
        int retry_board_cnt "재작업 보드 수"

        int lot_block_cnt "LOT 블록 수"
        int lot_bad_board_cnt "LOT 불량 보드"
        int lot_bad_block_cnt "LOT 불량 블록"
        int lot_bad_parts_cnt "LOT 불량 부품"
        int lot_ok_parts_cnt "LOT 정상 부품"
        int lot_retry_board_cnt "LOT 재작업 보드"

        float board_yield "보드 수율 (계산하여 추가예정)"
        float part_yield "부품 수율 (계산하여 추가예정)"
        float retry_ratio "재작업 비율 (계산하여 추가예정)"
    }


    LOT ||--|| TIME_METRIC : "LOT별 시간 지표"
    LOT ||--|| COUNT_METRIC : "LOT별 수량 지표"
    LOT ||--|| CYCLE_STAT : "LOT별 사이클 통계"
    LOT ||--|| QUALITY_SUMMARY : "LOT별 품질 요약"
    LOT ||--o{ RESOURCE_METRIC : "LOT별 자원 사용"





