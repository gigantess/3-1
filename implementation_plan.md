# 시계열 데이터 분석 및 인사이트 리포트 / 대시보드 단계별 구현 계획

`mission.md`에 명시된 모든 미션(필수 요구사항, 보너스 과제, 제약조건, AI 투명성 의무 명시)을 누락 없이 완수하기 위해 **Phase별/Step별 순차 구현 계획**으로 구체화했습니다.

---

## User Review Required

> [!NOTE]
> **분석 대상 데이터셋 선택**
> - **기본 설정 데이터**: **삼성전자(005930.KS)** 2023~2024년 2개년 일단위 주가/거래량 시계열 데이터 (Yahoo Finance API `yfinance` 자동 수집, 약 500+ 데이터 포인트).
> - **선정 이유**: 100개 이상의 충분한 포인트, 이동평균/변동성/수익률 패턴 분석 및 시계열 분해/예측 심화 분석에 최적.
> - 별도로 희망하시는 데이터셋이 있으시면 변경 진행 가능합니다.

---

## Proposed Changes & Step-by-Step Implementation

### Phase 1: 개발 환경 구성 및 데이터 수집/전처리 (Step 1 ~ Step 2)

#### Step 1: 개발 환경 및 의존성 정의
- [NEW] [requirements.txt](file:///d:/cody/3-1/requirements.txt)
  - 필수 라이브러리 정의: `pandas`, `numpy`, `matplotlib`, `seaborn`, `yfinance`, `statsmodels`, `plotly`, `streamlit`
- [NEW] [README.md](file:///d:/cody/3-1/README.md)
  - 프로젝트 구조, 요구 환경(Python 3.10+), 설치/실행 명령 가이드 작성.

#### Step 2: 시계열 데이터 수집 및 정제 모듈
- [NEW] [data/samsung_stock_2023_2024.csv](file:///d:/cody/3-1/data/samsung_stock_2023_2024.csv)
  - `yfinance`를 활용하여 2023-01-01 ~ 2024-12-31 삼성전자 일별 종가, 거래량 데이터 수집 (500+ 개 포인트).
- [NEW] [analysis.ipynb](file:///d:/cody/3-1/analysis.ipynb) / [src/data_loader.py](file:///d:/cody/3-1/src/data_loader.py)
  - 데이터 기본 정보(기간, 컬럼, 데이터 타입) 확인.
  - 비거래일(주말/공휴일) 처리 및 결측치/이상치 탐지 기준 명시 (Forward Fill 및 Interpolation 처리 적용).

---

### Phase 2: 시계열 데이터 분석 및 심화 옵션 수행 (Step 3 ~ Step 5)

#### Step 3: 필수 시계열 분석 기법 적용 (최소 2가지)
- [MODIFY] [analysis.ipynb](file:///d:/cody/3-1/analysis.ipynb)
  - **기법 1 (이동평균 & 변동성)**: 20일, 50일 Simple/Exponential Moving Average (SMA/EMA) 및 20일 Rolling Standard Deviation(볼린저 밴드) 계산.
  - **기법 2 (수익률 & 구간별 통계)**: 일별/월별 수익률(Percentage Change) 및 요일별 변동성 통계 집계.

#### Step 4: 보너스 과제 B - 시계열 심화 (분해 및 베이스라인 예측)
- [MODIFY] [analysis.ipynb](file:///d:/cody/3-1/analysis.ipynb)
  - **시계열 분해 (Seasonal Decomposition)**: `statsmodels`의 `seasonal_decompose`를 사용하여 추세(Trend), 계절성(Seasonal), 잔차/노이즈(Resid) 성분 분리 및 해석.
  - **베이스라인 예측 (Baseline Forecast)**: 이동평균 / Naive / ARIMA 모델을 이용한 향후 30일 간의 추세 예측 수행 및 모델의 가정과 한계 서술.

#### Step 5: 고화질 시각화 그래프 생성 및 저장 (`images/`)
- [NEW] `images/01_price_trend_and_ma.png` - 종가 추이 및 이동평균선(20일/50일)/변동성 밴드 차트.
- [NEW] `images/02_monthly_returns_bar.png` - 월별 수익률 분포 및 요일별 변동성 차트.
- [NEW] `images/03_seasonal_decomposition.png` - 추세/계절성/노이즈 분해 4단 멀티플롯.
- [NEW] `images/04_baseline_forecast.png` - 향후 30일 베이스라인 예측 결과 차트.

---

### Phase 3: 최종 인사이트 리포트 및 문서화 (Step 6 ~ Step 7)

#### Step 6: `REPORT.md` 분석 리포트 생성
- [NEW] [REPORT.md](file:///d:/cody/3-1/REPORT.md)
  - `mission.md` 규격에 맞춘 7가지 필수 목차 구성:
    1. **분석 주제 및 선정 이유**: 주제 및 분석 목적.
    2. **분석 질문 (3개)**:
       - Q1. 2023~2024년 전체적인 상승/하락 추세 및 주가 꺾임 구간은 어디인가?
       - Q2. 이동평균 교차점(골든/데드크로스) 및 변동성 급증 구간의 특징은 무엇인가?
       - Q3. 월별/분기별 수익률 패턴에 규칙성이나 특정 월의 경향성이 존재하는가?
    3. **데이터 설명**: Yahoo Finance 출처, 기간, 데이터 포인트 수, 결측치/이상치 처리 기준.
    4. **분석 결과 및 시각화**: 저장된 4개 시각화 이미지 포함 및 상세 해설.
    5. **인사이트 (3개 이상)**: 각 인사이트별 **관찰(Fact: 수치/근거)** + **원인(Why: 가능 가설)** + **행동(Action: 다음 단계/의사결정 제안)** 형식 서술.
    6. **결론 및 한계점**: 데이터 분석 요약 및 외부 거시 경제 변수 미반영 등 한계점 명시.
    7. **AI 사용 투명성 (의무 항목)**:
       - (1) 사용 작업 (전처리 스크립트 작성, 시각화 서식 조정, 문장 정제)
       - (2) 사용 이유 (작업 시간 단축, 대안 코드 검토)
       - (3) 검증 방법 (샘플 데이터 수동 통계 계산 비교, 차트 재현 확인)

#### Step 7: 재현성 가이드 문서 완료
- [MODIFY] [README.md](file:///d:/cody/3-1/README.md)
  - 노트북 실행 순서, 데이터 수집/분석 스크립트 실행 명령, 라이선스/출처 유의사항 추가.

---

### Phase 4: 보너스 과제 A - 인터랙티브 웹 대시보드 구축 (Step 8)

#### Step 8: Streamlit 서비스화 대시보드 개발
- [NEW] [app.py](file:///d:/cody/3-1/app.py)
  - **Streamlit 기반 대시보드 앱 구현**:
    - 날짜 범위(Date Range) 동적 조율 슬라이더.
    - 이동평균선(10일/20일/50일/120일) 선택 켜기/끄기 및 변동성 지표 필터.
    - Plotly 차트 기반 확대/축소 및 마우스 툴팁 인터랙션.
    - 계절성 분해 및 30일 예측 결과 시뮬레이션 인터페이스.
  - 실행 화면 캡처 및 대시보드 시연 시나리오를 `README.md` 및 `REPORT.md`에 반영.

---

## Verification Plan

### Automated Tests / Scripts
1. **데이터 및 수집 검증**: `python -c "import pandas as pd; df=pd.read_csv('data/samsung_stock_2023_2024.csv'); print(len(df))"` (데이터 포인트 100개 이상 검증).
2. **코드 문법 검증**: `python -m py_compile app.py` (Streamlit 앱 에러 유무 검증).
3. **노트북 실행 테스트**: Jupyter Notebook 전체 실행으로 시각화 PNG 4개 자동 생성 확인.

### Manual Verification
1. `REPORT.md` 문서 내 7개 목차, 질문 3개, 관찰-원인-행동 인사이트 3개, 시각화 4개, AI 사용 투명성 섹션 존재 확인.
2. `streamlit run app.py` 실행 후 브라우저 필터 조작에 따른 차트 변경 동작 확인.