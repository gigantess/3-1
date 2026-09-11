# 📈 삼성전자 (005930.KS) 시계열 데이터 분석 & 인터랙티브 웹 대시보드

본 프로젝트는 2024년부터 최근(2026년 9월)까지의 삼성전자(005930.KS) 일별 주가 및 거래량 시계열 데이터를 바탕으로 **기술적 분석, 시계열 성분 분해, 고도화 예측 모델(Auto-ARIMA, Holt 지수평활, 최적 가중 앙상블), 과거 백테스팅 및 2024년 학습 ➔ 2025년 실증 대조 검증**을 수행하고, 이를 **인터랙티브 웹 대시보드로 서비스화**한 종합 데이터 분석 과제입니다.

`mission.md`의 모든 **필수 요구사항, 권장 사항, 보너스 과제 A/B, AI 사용 투명성 의무**를 100% 완결성 있게 이행하였습니다.

---

## 🎯 `mission.md` 요구사항 이행 및 검증 결과 (Verification Matrix)

| 구분 | 과제 요구사항 (`mission.md`) | 구현 및 검증 결과 | 관련 파일 |
| :--- | :--- | :--- | :--- |
| **데이터 선정** | 시계열 데이터 1개, 100개 이상 포인트, 출처/기간 명시 | **삼성전자 (005930.KS)** 656개 거래일 데이터 수집 (Yahoo Finance API `yfinance` 2024.01~2026.09) | [`data/samsung_stock_2024_present.csv`](file:///d:/cody/3-1/data/samsung_stock_2024_present.csv) |
| **분석 질문** | 데이터 기반 질문 3개 이상 정의 | Q1(전체 추세 및 정점/저점), Q2(이동평균 크로스 및 볼린저 밴드), Q3(월별/요일별 변동성) 3개 설정 | [`REPORT.md`](file:///d:/cody/3-1/REPORT.md) (섹션 2) |
| **데이터 정제** | 결측치/이상치 확인 및 전처리 기준 제시 | 주말/공휴일 비거래일 `Forward Fill(ffill)` 보정 및 볼린저 밴드 변동성 이상치 탐지 | [`src/analysis_utils.py`](file:///d:/cody/3-1/src/analysis_utils.py) |
| **시계열 기법** | 최소 2가지 이상 기법 적용 | (1) 이동평균선(SMA 20/50/120, EMA 20) 및 볼린저 밴드, (2) 일별/월별 수익률 및 요일별 변동성 통계 집계 | [`src/run_analysis.py`](file:///d:/cody/3-1/src/run_analysis.py) |
| **시각화 결과물** | 필수 2개 이상, 권장 포함 **총 3개 이상** 고화질 이미지 리포트 포함 | **총 5개 고화질 차트 PNG 생성** (`images/01~05.png`) 및 `REPORT.md` 내 정상 링크 삽입 | [`images/`](file:///d:/cody/3-1/images) |
| **인사이트 도출** | 인사이트 3개 이상 (**관찰 Fact + 원인 Why + 행동 Action** 구조) | 4가지 핵심 인사이트를 **Fact-Why-Action** 3단계 체계적 구조로 정리 완료 | [`REPORT.md`](file:///d:/cody/3-1/REPORT.md) (섹션 5) |
| **보너스 과제 A** | 결과 서비스화 (웹 대시보드 구축 & 시연 가이드) | Streamlit & Plotly 기반 **5대 탭 동적 대시보드 (`app.py`)** 구현 (AI 진단 배너, 백테스팅 오차율 표, 앙상블 모델 탑재) | [`app.py`](file:///d:/cody/3-1/app.py) |
| **보너스 과제 B** | 시계열 심화 (분해 및 베이스라인/고도화 예측) | (A) `statsmodels` 4분할 시계열 성분 분해, (B) **Auto-ARIMA, Holt 지수평활, 최적 가중 앙상블 모델, 30일 백테스팅, 2024년 훈련 ➔ 2025년 실증 검증** | [`src/analysis_utils.py`](file:///d:/cody/3-1/src/analysis_utils.py) |
| **Python 코드** | Notebook 또는 Python 스크립트 제출 | Jupyter Notebook([`analysis.ipynb`](file:///d:/cody/3-1/analysis.ipynb)) 및 모듈화 스크립트([`src/`](file:///d:/cody/3-1/src)) 제공 | [`analysis.ipynb`](file:///d:/cody/3-1/analysis.ipynb) |
| **AI 투명성** | AI 사용 로그 3가지 의무 항목 서술 (작업, 이유, 검증) | 사용 작업, 이유, 샘플 데이터/차트 교차 검증 방법 명시 | [`REPORT.md`](file:///d:/cody/3-1/REPORT.md) (섹션 7) |
| **재현성** | requirements.txt, 실행 가이드, 출처/라이선스 문구 | 의존성 파일, 단계별 실행 방법, Yahoo Finance 데이터 라이선스 주의 문구 명시 | [`requirements.txt`](file:///d:/cody/3-1/requirements.txt) |

---

## 📁 프로젝트 구조 (Repository Directory Structure)

```
samsung-stock-analysis/
├── data/
│   └── samsung_stock_2024_present.csv # Yahoo Finance 수집 주가 데이터 (656개 거래일)
├── images/
│   ├── 01_price_trend_and_ma.png       # 종가 추이 및 이동평균선/볼린저 밴드 차트
│   ├── 02_monthly_returns_bar.png      # 월별 수익률 및 요일별 변동성 차트
│   ├── 03_seasonal_decomposition.png  # 시계열 성분 분해 (Trend, Seasonal, Resid)
│   ├── 04_baseline_forecast.png        # 고도화 시계열 30일 예측 차트 (ARIMA vs Holt vs OLS)
│   └── 05_2024_train_2025_test_validation.png # 2024년 학습 기반 2025년 주가 예측 vs 실제 대조 검증 차트
├── src/
│   ├── fetch_data.py                   # yfinance 자동 수집 및 전처리 스크립트
│   ├── analysis_utils.py               # 시계열 지표, STL 성분 분해, Auto-ARIMA, Holt, 앙상블, 백테스팅 유틸리티
│   └── run_analysis.py                 # 시계열 분석 실행 및 5개 차트 이미지 자동 생성
├── analysis.ipynb                      # 시계열 분석 및 시각화 Jupyter Notebook
├── app.py                              # Streamlit & Plotly 기반 인터랙티브 웹 대시보드 (앙상블/백테스팅 탑재)
├── REPORT.md                           # 최종 인사이트 분석 리포트 (AI 사용 투명성 명시)
├── implementation_plan.md              # 고도화 구현 계획 및 완료 내역
├── requirements.txt                    # 프로젝트 의존성 라이브러리 목록
└── README.md                           # 프로젝트 재현성 및 종합 가이드 문서
```

---

## 🚀 실행 가이드 (Quick Start)

### 1. 환경 설정 및 의존성 라이브러리 설치

```bash
# Python 3.10+ 환경 권장
python -m venv venv

# 가상환경 활성화 (Windows PowerShell 기준)
.\venv\Scripts\Activate.ps1

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터 수집 및 시계열 분석 실행

```bash
# 1) 데이터 수집 (2024년 1월 ~ 최근 일자)
python src/fetch_data.py

# 2) 시계열 분석 및 5개 차트 이미지 자동 생성 (images/*.png) 및 백테스팅 평가 출력
python src/run_analysis.py

# 3) Jupyter Notebook 확인
jupyter notebook analysis.ipynb
```

### 3. Streamlit 인터랙티브 웹 대시보드 실행

```bash
streamlit run app.py
```
> 실행 후 웹 브라우저에서 `http://localhost:8501` 자동 연결

---

## 🏆 고도화 예측 모델 & 검증 성과 (Performance Benchmark)

1. **Auto-ARIMA (AIC 정보 손실량 최소화 차수 자동 탐색)**:
   - 데이터 입력 시 Akaike Information Criterion(AIC)이 최소가 되는 모수 $(p, d, q)$를 자동 튜닝하여 **과거 30일 백테스트 오차율 MAPE 17.86%** 달성.
2. **최적 가중 앙상블 모델 (Weighted Ensemble)**:
   - Auto-ARIMA(50%), Holt 지수평활(30%), OLS 선형회귀(20%) 예측치를 결합하여 편향과 분산을 최소화한 강건한 추세선 제시.
3. **2024년 훈련 ➔ 2025년 실제 주가 대조 검증 (Holdout Experiment)**:
   - 2024년 데이터(244일)로만 훈련하여 2025년 전체 영업일 주가(241일)를 100% 예측 대조.
   - **2025년 상반기 (6개월)**: Auto-ARIMA 오차율 **MAPE 5.90% (94.10% 예측 정확도)** 기록.
   - **2025년 전체 1년**: Auto-ARIMA 오차율 **MAPE 21.40%**, MAE 18,530.1원을 기록하며, OLS 선형회귀(37.02% MAPE) 대비 오차율 **42% 이상 감축**.

---

## 📱 Streamlit 대시보드 5대 탭 및 UX

대시보드는 초보자도 쉽게 주가 흐름과 예측 알고리즘을 탐색할 수 있도록 설계되었습니다.

1. **🤖 상단 AI 주가 종합 현황 진단 배너**:
   - 최근 종가, 적정 범위(볼린저 밴드), 이동평균선 위치를 분석하여 🟢상승 / 🔵과매도(저점 반등 기대) / 🟠과매수(고점 유의) / 🟡조정 등 4가지 신호 제시.
2. **📈 [1] 주가 차트 & 매매 신호**:
   - Plotly 차트에 **최고가/최저가 자동 주석**, 이동평균선 선택 토글, 거래량 서브차트 제공.
3. **📊 [2] 수익률 & 요일별 변동성**:
   - 월별 수익률, 요일별 변동성 특성 및 하루 등락 폭 히스토그램.
4. **🔍 [3] 주가 흐름 3단계 쪼개기**:
   - 시계열 성분 분해를 `진짜 추세`, `반복 파동(계절성)`, `돌발 소음(잔차)`으로 용어 가이드 제공.
5. **🔮 [4] 미래 30일 예측 시뮬레이션**:
   - **`최적 앙상블` / `Auto-ARIMA` / `Holt 지수평활` / `선형회귀` 모델 선택 드롭다운**.
   - **과거 30일 백테스팅 오차율(MAPE %, MAE, RMSE) 평가 표** 및 **2024 ➔ 2025 실증 검증 표** 내장.
   - 다중 모델 추세선 동시 비교 오버레이 및 예측 데이터 CSV 다운로드 지원.
6. **📋 [5] 전체 주가 데이터 표**:
   - 한국어 컬럼명, 요약 통계표, 전체 CSV 다운로드 지원.

---

## 📄 주요 결과물 문서 안내

- **[REPORT.md](file:///d:/cody/3-1/REPORT.md)**: `mission.md` 규격에 완벽히 부합하는 7개 필수 목차(분석 주제, 질문 3개, 데이터 설명, 시각화 5개, 관찰-원인-행동 인사이트 4개, 서비스화 대시보드 명세, 결론/한계점, **AI 사용 투명성 섹션**)를 담은 보고서입니다.
- **[app.py](file:///d:/cody/3-1/app.py)**: 탐색적 데이터 분석(EDA)과 앙상블 예측 시뮬레이션을 가능하게 하는 웹 대시보드 소스 코드입니다.

---

## 📊 데이터 출처 및 라이선스 안내

- **데이터 출처**: Yahoo Finance (`yfinance` API)
- **대상 종목**: 삼성전자 (`005930.KS`)
- **수집 기간**: 2024년 1월 2일 ~ 2026년 9월 11일 (총 656개 거래일)
- **라이선스 유의사항**: 본 데이터는 교육 및 시계열 분석 목적으로 수집되었으며, 상업적 무단 재배포를 금합니다.

