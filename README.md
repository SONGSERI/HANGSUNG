# NPM ProductReport LOG 데이터 수집 정의

---

## 1. 개요

- 대상 설비: ??
- 대상 로그: ProductReport
- 원칙  
  - LOG 파일 1개 = LOT 1개  
  - LOT 기준으로 모든 데이터 수집

---


## 2. LOG 파싱 규칙

### 2.1 파일 이름
- Production Report 
  파일이름 [Timestamp]-[Machine]-[Stage]-[Lane]-[Head]-[LotName].[LogType]
  20260116000000391-05-1-1-3-NAD_H_T_EBR37416101.u01


### 2.2 공통

- [Section] 단위 파싱
- Key=Value 형식 사용
- 문자열 따옴표 제거
- 숫자 필드는 int / float 변환

---

### 2.3 Header / Summary 영역

대상 섹션
```
[Index]
[Information]
[Time]
[Count]
```

처리 방식
- LOG 1개당 1회 파싱
- LOT / LOT_TIME_SUMMARY / LOT_COUNT_SUMMARY 각각 1 Row 생성

---

### 2.4 Feeder / Nozzle 영역

대상 섹션
```
[MountPickupFeeder]
[MountPickupNozzle]
```

처리 방식
- 데이터 라인 1줄 = DB Row 1개
- lot_id는 상위 LOT에서 주입

---

### 2.5 STOP 데이터 처리

LOG 예시
```
[Time]
SCStop=70.83

[Count]
SCStop=2
```

변환 결과

| lot_id | stop_type | stop_time | stop_count |
|------|-----------|-----------|------------|
| LOT | SCStop | 70.83 | 2 |

- Time / Count 모두 존재하는 항목만 저장
- 값이 0이면 저장 제외 가능

---

