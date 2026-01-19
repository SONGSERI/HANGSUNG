## ERD

```mermaid

erDiagram

    LOT
-------------------------------------------------
PK  lot_id
◎  lot_name
◎  product_id
◎  rev
◎  plan_id
◎  machine
◎  stage_no
◎  lane_no
◎  mjs_id
◎  report_date
◎  output_qty

△  work_order
△  model_code
△  line_code
△  shift_code
△  lot_start_time
△  lot_end_time

LOT_TIME_SUMMARY
-------------------------------------------------
PK  time_id
FK  lot_id

◎  power_on_time
◎  change_time
◎  prod_view_time
◎  maintenance_time
◎  data_edit_time
◎  unit_adjust_time
◎  idle_time
◎  prod_time
◎  actual_time
◎  load_time
◎  board_recog_time
◎  mount_time
◎  total_stop_time

◎  f_wait_time
◎  r_wait_time
◎  s_wait_time
◎  c_wait_time
◎  b_wait_time
◎  p_wait_time

◎  sc_stop_time
◎  sce_stop_time
◎  other_stop_time
◎  conv_stop_time
◎  brcg_stop_time
◎  trouble_time
◎  mhrcg_stop_time
◎  fb_stop_time
◎  bndrcg_stop_time

◎  cp_err_time
◎  cr_err_time
◎  cd_err_time
◎  cm_err_time
◎  ct_err_time
◎  trs_err_time
◎  prd_stop_time
◎  judge_stop_time
◎  other_line_stop_time
◎  bnd_stop_time

◎  mc_fwait_time
◎  mc_rwait_time
◎  joint_pass_wait_time
◎  ppi_stop_time
◎  simulation_time

△  planned_time
△  availability_rate
△  performance_rate
△  oee

LOT_CYCLE_TIME
-------------------------------------------------
PK  cycle_id
FK  lot_id

◎  cycle_time_1
◎  cycle_time_2
◎  cycle_time_3

LOT_COUNT_SUMMARY
-------------------------------------------------
PK  count_id
FK  lot_id

◎  board_cnt
◎  module_cnt

◎  f_wait_cnt
◎  r_wait_cnt
◎  s_wait_cnt
◎  c_wait_cnt
◎  b_wait_cnt
◎  p_wait_cnt

◎  sc_stop_cnt
◎  sce_stop_cnt
◎  other_stop_cnt
◎  conv_stop_cnt
◎  brcg_stop_cnt
◎  trouble_cnt
◎  mhrcg_stop_cnt
◎  fb_stop_cnt
◎  bndrcg_stop_cnt

◎  cp_err_cnt
◎  cr_err_cnt
◎  cd_err_cnt
◎  cm_err_cnt
◎  ct_err_cnt
◎  trs_err_cnt

◎  total_pickup_cnt
◎  pickup_miss_cnt
◎  retry_miss_cnt
◎  drop_miss_cnt
◎  mount_miss_cnt
◎  head_miss_cnt
◎  trs_miss_cnt

◎  lot_board_cnt
◎  lot_module_cnt

◎  mc_fwait_cnt
◎  mc_rwait_cnt
◎  joint_pass_wait_cnt

◎  total_mount_cnt
◎  ppi_stop_cnt
◎  ppi_err_cnt

△  good_cnt
△  reject_cnt
△  yield_rate

LOT_RESOURCE_USAGE
-------------------------------------------------
PK  resource_id
FK  lot_id

◎  resource_type        -- FEEDER / NOZZLE
◎  head_no
◎  feeder_addr
◎  feeder_slot
◎  nozzle_no
◎  resource_serial
◎  part_no
◎  library_name

◎  pickup_cnt
◎  p_miss_cnt
◎  r_miss_cnt
◎  d_miss_cnt
◎  m_miss_cnt
◎  h_miss_cnt
◎  trs_miss_cnt
◎  mount_cnt
◎  ppi_err_cnt

△  error_type
△  error_code
△  first_error_time
△  last_error_time
△  usage_time


LOT_INSPECTION
-------------------------------------------------
PK  inspect_id
FK  lot_id

◎  bad_board_cnt
◎  bad_block_cnt
◎  bad_parts_cnt
◎  ok_parts_cnt
◎  retry_board_cnt

◎  lot_block_cnt
◎  lot_bad_board_cnt
◎  lot_bad_block_cnt
◎  lot_bad_parts_cnt
◎  lot_ok_parts_cnt
◎  lot_retry_board_cnt

LOT
 ├─ 1:1 → LOT_TIME_SUMMARY
 ├─ 1:1 → LOT_COUNT_SUMMARY
 ├─ 1:1 → LOT_CYCLE_TIME
 ├─ 1:1 → LOT_INSPECTION
 └─ 1:N → LOT_RESOURCE_USAGE


