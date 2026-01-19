# HANGSUNG

데이터 수집 구조 & 파싱 정의서
1. 문서 목적
본 문서는 NPM 설비 ProductReport LOG를 대상으로
LOT 기준 데이터 수집 구조를 정의하고
실제 LOG 파일을 DB 테이블로 어떻게 파싱하는지를 명확히 설명한다.
대상 LOG:
ProductReport (Index / Information / Time / Count / MountPickup*)
2. 전체 데이터 구조 개요
기본 원칙
LOG 파일 1개 = LOT 1개
LOT을 기준으로 요약 / 상세 테이블 분리
반복 Row 영역(Feeder / Nozzle)은 별도 테이블로 관리
ERD 개요
erDiagram
    LOT ||--|| LOT_TIME_SUMMARY : has
    LOT ||--|| LOT_COUNT_SUMMARY : has
    LOT ||--o{ LOT_STOP : has
    LOT ||--o{ FEEDER_STAT : has
    LOT ||--o{ NOZZLE_STAT : has
3. 테이블 구조 정의
3.1 LOT (헤더 테이블)
역할
LOG 전체를 대표하는 기준 테이블
모든 하위 테이블의 기준 키
컬럼명	타입	설명	LOG 위치
lot_id	string	LOT ID	[Information].LotName
machine	string	설비명	[Index].Machine
lane	int	Lane 번호	[Information].Lane
product_id	string	제품 코드	[Information].ProductID
rev	string	Revision	[Information].Rev
start_time	datetime	작업 시작	[Index].Date
end_time	datetime	작업 종료	수집 시각
3.2 LOT_TIME_SUMMARY (시간 요약)
역할
LOT 단위 설비 시간 구성 분석
컬럼명	타입	설명	LOG 위치
lot_id	string	LOT ID	FK
prod_time	float	생산 시간	[Time].Prod
actual_time	float	실제 생산 시간	[Time].Actual
mount_time	float	Mount 시간	[Time].Mount
total_stop_time	float	총 정지 시간	[Time].TotalStop
rwait_time	float	Rear Wait	[Time].Rwait
3.3 LOT_COUNT_SUMMARY (수량 요약)
역할
LOT 단위 생산량 / 불량 요약
컬럼명	타입	설명	LOG 위치
lot_id	string	LOT ID	FK
board_cnt	int	Board 수	[Count].Board
module_cnt	int	Module 수	[Count].Module
total_pickup_cnt	int	총 Pickup	[Count].TPickup
total_mount_cnt	int	총 Mount	[Count].TMount
pickup_miss_cnt	int	Pickup Miss	[Count].TPMiss
retry_miss_cnt	int	Retry Miss	[Count].TRMiss
3.4 LOT_STOP (정지 상세)
역할
정지 유형별 시간 / 횟수 관리
설비 손실 분석의 핵심 테이블
컬럼명	타입	설명
lot_id	string	LOT ID
stop_type	string	Stop 코드 (SCStop, CPErr 등)
stop_time	float	정지 시간
stop_count	int	발생 횟수
3.5 FEEDER_STAT (Feeder 통계)
역할
Feeder / Part 단위 Pickup 이상 분석
컬럼명	타입	설명	LOG 필드
lot_id	string	LOT ID	상위 LOT
head_table_no	string	Head Table	BLKCode
feeder_no	int	Feeder Address	FAdd
part_no	string	Part Name	PartsName
pickup_cnt	int	Pickup 수	Pickup
pmiss_cnt	int	Pickup Miss	PMiss
rmiss_cnt	int	Retry Miss	RMiss
mount_cnt	int	Mount 수	Mount
3.6 NOZZLE_STAT (Nozzle 통계)
역할
Nozzle 수명 / 불량 집중도 분석
컬럼명	타입	설명	LOG 필드
lot_id	string	LOT ID	상위 LOT
head_no	int	Head 번호	Head
nozzle_no	string	Nozzle 번호	NCAdd
pickup_cnt	int	Pickup 수	Pickup
pmiss_cnt	int	Pickup Miss	PMiss
mount_cnt	int	Mount 수	Mount
4. LOG 파싱 규칙
4.1 공통 규칙
[Section] 단위 파싱
Key=Value 구조 사용
문자열 " " 제거
숫자 필드는 int / float 변환
값이 없는 경우 NULL 처리
4.2 Header / Summary 영역 파싱
대상 섹션
[Index]
[Information]
[Time]
[Count]
처리 방식
LOG 1회 파싱
LOT / LOT_TIME_SUMMARY / LOT_COUNT_SUMMARY 각각 1 Row 생성
4.3 반복 Row 영역 파싱 (Row Explosion)
대상 섹션
[MountPickupFeeder]
[MountPickupNozzle]
처리 방식
라인 1줄 = DB Row 1개
첫 줄은 컬럼 정의
모든 Row에 lot_id를 FK로 주입
4.4 STOP 데이터 파싱 규칙
LOG 예시
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
Time / Count 양쪽에 존재하는 항목만 처리
값이 0인 항목은 저장 제외 가능 (옵션)
5. 설계 의도 요약
본 구조는 운영 DB가 아닌 로그 분석용 구조
LOT 기준으로:
시간
수량
정지
Feeder
Nozzle
를 독립적으로 분석 가능
MES / AI / 통계 분석으로 확장 용이
6. 향후 확장 방향
LOT → SHIFT / HOUR 단위 분해
Part / Nozzle 이상 기준 테이블 추가
동일 Part / 설비 간 비교 분석
