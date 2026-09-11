# 삼성전자 시계열 데이터 분석 & 인사이트 리포트 / 대시보드

이 프로젝트는 2024년부터 최근(2026년 9월)까지의 삼성전자(005930.KS) 일단위 주가 및 거래량 시계열 데이터를 분석하고, 의미 있는 패턴과 인사이트를 도출하며 인터랙티브 웹 대시보드로 서비스화한 과제입니다.

## 📁 프로젝트 구조

```
samsung-stock-analysis/
├── data/
│   └── samsung_stock_2024_present.csv # Yahoo Finance 수집 주가 데이터 (656개 포인트)
├── images/
│   ├── 01_price_trend_and_ma.png       # 종가 추이 및 이동평균선/볼린저 밴드 차트
│   ├── 02_monthly_returns_bar.png      # 월별 수익률 및 요일별 변동성 차트
│   ├── 03_seasonal_decomposition.png  # 시계열 성분 분해 (Trend, Seasonal, Resid)
│   └── 04_baseline_forecast.png        # 베이스라인 30일 예측 차트
├── src/
│   ├── fetch_data.py                   # 데이터 수집 및 전처리 스크립트
│   ├── analysis_utils.py               # 시계열 지표/분해/예측 유틸리티
│   └── run_analysis.py                 # 시계열 분석 실행 및 차트 자동 생성 스크립트
├── analysis.ipynb                      # 시계열 분석 및 시각화 노트북
├── app.py                              # Streamlit 웹 대시보드 앱
├── REPORT.md                           # 최종 인사이트 분석 리포트 (AI 사용 투명성 포함)
├── requirements.txt                    # 의존성 라이브러리 목록
└── README.md                           # 프로젝트 설명 문서
```

## 🚀 실행 방법 (Quick Start)

### 1. 환경 설정 및 의존성 설치

```bash
# 가상환경 생성 및 활성화
python -m venv venv
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터 수집 및 분석 실행

```bash
# 1) 데이터 수집 (2024년 ~ 최근)
python src/fetch_data.py

# 2) 시계열 분석 및 차트 자동 생성 (images/*.png)
python src/run_analysis.py

# 3) Jupyter Notebook 실행
jupyter notebook analysis.ipynb
```

### 3. Streamlit 웹 대시보드 실행 및 인터랙티브 탐색

```bash
streamlit run app.py
```
> 실행 후 브라우저에서 `http://localhost:8501` 접속

#### 📱 대시보드 주요 기능 (5개 탭)
1. **📈 주가 추이 & 기술적 지표**: 날짜 범위 슬라이더, 캔들스틱/선 차트 전환, 이동평균선(10/20/50/120일) 선택, 볼린저 밴드 및 거래량 서브차트 ON/OFF.
2. **📊 수익률 & 요일별 변동성**: 월별 누적 수익률 바 차트, 요일별 수익률 변동성(표준편차) 분석 및 일일 수익률 분포 히스토그램.
3. **🔍 시계열 성분 분해**: `statsmodels` 기반 관측치/추세/계절성/잔차 4분할 Plotly 동적 분해 차트 (주기 선택 가능).
4. **🔮 30일 예측 시뮬레이션**: 향후 30 영업일 추세선 및 ±95% 신뢰구간 시뮬레이션, 추세 가중치 튜닝 및 예측 데이터 CSV 다운로드.
5. **📋 데이터 탐색 & 다운로드**: 필터링된 전체 데이터셋 조회, 요약 통계량 표 및 전체 CSV 다운로드.

#### 🎯 대시보드 필터/시나리오 시연 안내
- **시나리오 1 (기술적 지표 과매도 확인)**: 날짜 범위를 2024년 7월~11월 하락장으로 설정 후 '볼린저 밴드'와 'SMA 20일/50일'을 켜서 하한 이탈 시점의 반등 패턴을 탐색.
- **시나리오 2 (요일별 리스크 관리)**: '수익률 & 요일별 변동성' 탭에서 금요일/월요일의 높은 변동성(표준편차) 수치를 확인.
- **시나리오 3 (예측 가중치 시뮬레이션)**: '30일 예측 시뮬레이션' 탭에서 사이드바의 '추세 가중치'를 조절하여 상방/하방 시나리오별 주가 경로 및 신뢰구간 변동을 가상 시뮬레이션.

---

## 📄 주요 결과물 안내

- **[REPORT.md](file:///d:/cody/3-1/REPORT.md)**: 분석 질문 3개, 시각화 4개, **관찰(Fact)-원인(Why)-행동(Action)** 구조의 인사이트 3개, 인터랙티브 웹 대시보드 명세, 결론/한계점 및 **AI 사용 투명성 섹션**이 완전히 정리된 보고서입니다.
- **[app.py](file:///d:/cody/3-1/app.py)**: Streamlit & Plotly 기반 서비스화 대시보드 웹 애플리케이션.

---

## 📊 데이터 정보 & 라이선스

- **출처**: Yahoo Finance (`yfinance` API)
- **종목**: 삼성전자 (`005930.KS`)
- **기간**: 2024년 1월 2일 ~ 2026년 9월 11일 (총 656개 거래일)
- **Git Commit 계정**: `true9090@gmail.com`
- **라이선스 유의사항**: 본 데이터는 학술 및 시계열 분석 연습 목적으로 수집되었으며, 상업적 무단 재배포를 금합니다.

