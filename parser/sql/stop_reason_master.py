# 정지 사유 코드 마스터 (ERD: STOP_REASON)

STOP_REASON_MASTER = {
    "WAIT PRE":  {"code": "WAIT_PRE",  "group": "WAIT"},
    "WAIT POST": {"code": "WAIT_POST", "group": "WAIT"},
    "PICKUP ERROR": {"code": "PICKUP_ERR", "group": "ERROR"},
    "RECOGNITION ERROR": {"code": "RECOG_ERR", "group": "ERROR"},
    "PLACEMENT ERROR": {"code": "PLACE_ERR", "group": "ERROR"},
    "TRANSFER ERROR": {"code": "TRANSFER_ERR", "group": "ERROR"},
    "CHANGEOVER": {"code": "CHANGEOVER", "group": "SETUP"},
}
