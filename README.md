# HANGSUNG

NPM LOG 데이터 수집 구조 및 파싱 정의서
1. 목적
NPM 설비에서 생성되는 ProductReport 로그를
LOT 단위 기준으로 구조화하여
분석/이력/이상 탐지를 가능하게 한다.
본 문서는
① ERD 기반 테이블 구조와
② 실제 LOG 파일 파싱 규칙을 함께 정의한다.
2. 전체 구조 개요
LOG 파일 1개 = LOT 1개
LOT을 기준으로 요약 / 상세 테이블 분리
Row 폭발 영역(Feeder / Nozzle)은 별도 테이블로 분리
erDiagram
    LOT ||--|| LOT_TIME_SUMMARY : has
    LOT ||--|| LOT_COUNT_SUMMARY : has
    LOT ||--o{ LOT_STOP : has
    LOT ||--o{ FEEDER_STAT : has
    LOT ||--o{ NOZZLE_STAT : has
3. 테이블 구조 정의
3.1 LOT (헤더 테이블)
역할
로그 전체를 대표하는 기준 테이블
모든 하위 테이블의 FK 기준
컬럼명	설명	LOG 위치
lot_id	LOT ID	[Information].LotName
machine	설비명	[Index].Machine
lane	Lane 번호	[Information].Lane
product_id	제품 코드	[Information].ProductID
rev	Revision	[Information].Rev
start_time	작업 시작	[Index].Date
end_time	작업 종료	수집 시각
3.2 LOT_TIME_SUMMARY (시간 요약)
역할
LOT 단위 설비 시간 분해
컬럼명	설명	LOG 위치
lot_id	LOT ID	FK
prod_time	생산 시간	[Time].Prod
actual_time	실 생산 시간	[Time].Actual
mount_time	Mount 시간	[Time].Mount
total_stop_time	총 정지 시간	[Time].TotalStop
rwait_time	Rear Wait	[Time].Rwait
3.3 LOT_COUNT_SUMMARY (수량 요약)
역할
LOT 단위 생산/불량 수치 요약
컬럼명	설명	LOG 위치
lot_id	LOT ID	FK
board_cnt	Board 수	[Count].Board
module_cnt	Module 수	[Count].Module
total_pickup_cnt	Pickup 총량	[Count].TPickup
total_mount_cnt	Mount 총량	[Count].TMount
pickup_miss_cnt	Pickup Miss	[Count].TPMiss
retry_miss_cnt	Retry Miss	[Count].TRMiss
3.4 LOT_STOP (정지 상세)
역할
Stop 유형별 시간/횟수 관리
분석 핵심 테이블
컬럼명	설명
lot_id	LOT ID
stop_type	Stop 코드 (SCStop, CPErr 등)
stop_time	정지 시간
stop_count	발생 횟수
3.5 FEEDER_STAT (Feeder 단위 통계)
역할
Part / Feeder 이상 분석
컬럼명	설명	LOG
lot_id	LOT ID	FK
head_table_no	Head Table	BLKCode
feeder_no	Feeder Address	FAdd
part_no	Part Name	PartsName
pickup_cnt	Pickup	Pickup
pmiss_cnt	Pickup Miss	PMiss
rmiss_cnt	Retry Miss	RMiss
mount_cnt	Mount	Mount
3.6 NOZZLE_STAT (Nozzle 단위 통계)
역할
Nozzle 수명 / 불량 집중도 분석
컬럼명	설명	LOG
lot_id	LOT ID	FK
head_no	Head 번호	Head
nozzle_no	Nozzle 번호	NCAdd
pickup_cnt	Pickup	Pickup
pmiss_cnt	Pickup Miss	PMiss
mount_cnt	Mount	Mount
4. LOG 파싱 규칙 정의
4.1 공통 규칙
[Section] 단위로 파싱
Key=Value → 컬럼 매핑
문자열 " " 제거
숫자는 float / int 변환
존재하지 않는 값은 NULL
4.2 LOG 유형 ① Header / Summary 영역
대상 섹션
[Index]
[Information]
[Time]
[Count]
파싱 방식
1회 파싱 → 1 Row
LOT / LOT_TIME_SUMMARY / LOT_COUNT_SUMMARY에 각각 Insert
4.3 LOG 유형 ② 반복 Row 영역 (폭발 영역)
대상 섹션
[MountPickupFeeder]
[MountPickupNozzle]
파싱 방식
라인 1줄 = DB Row 1개
헤더 라인은 컬럼 정의로 사용
LOT_ID는 상위 LOT에서 주입
4.4 STOP 데이터 파싱 규칙
예시
[Time]
SCStop=70.83
CPErr=46.84

[Count]
SCStop=2
CPErr=3
변환 결과
lot_id	stop_type	stop_time	stop_count
LOT	SCStop	70.83	2
LOT	CPErr	46.84	3
Time / Count 양쪽에 존재하는 항목만 대상
값이 0이면 저장 제외 가능 (옵션)
5. 설계 의도 요약
본 구조는 정규화 DB가 아닌 로그 분석용 구조
LOT 기준으로:
시간
수량
정지
Feeder
Nozzle
를 독립 분석 가능
MES / AI / 통계 확장에 바로 사용 가능
6. 다음 확장 가능 항목
LOT → SHIFT / HOUR 분해
Feeder / Nozzle 이상 기준치 관리
동일 Part / Nozzle 간 비교 분석
