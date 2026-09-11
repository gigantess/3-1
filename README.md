# 삼성전자 시계열 데이터 분석 & 인사이트 리포트 / 대시보드

이 프로젝트는 2024년부터 최근까지의 삼성전자(005930.KS) 일단위 주가 및 거래량 시계열 데이터를 분석하고, 의미 있는 패턴과 인사이트를 도출하며 인터랙티브 웹 대시보드로 서비스화한 과제입니다.

## 📁 프로젝트 구조

```
samsung-stock-analysis/
├── data/
│   └── samsung_stock_2024_present.csv # Yahoo Finance 수집 주가 데이터 (2024년 ~ 최근)
├── images/
│   ├── 01_price_trend_and_ma.png       # 종가 추이 및 이동평균선/변동성 차트
│   ├── 02_monthly_returns_bar.png      # 월별 수익률 및 요일별 변동성 차트
│   ├── 03_seasonal_decomposition.png  # 시계열 성분 분해 (Trend, Seasonal, Resid)
│   └── 04_baseline_forecast.png        # 베이스라인 30일 예측 차트
├── src/
│   ├── fetch_data.py                   # 데이터 수집 및 전처리 스크립트
│   └── analysis_utils.py               # 시계열 지표/분해/예측 유틸리티
├── analysis.ipynb                      # 시계열 분석 및 시각화 노트북
├── app.py                              # Streamlit 웹 대시보드 앱
├── REPORT.md                           # 최종 인사이트 분석 리포트 (AI 사용 투명성 포함)
├── requirements.txt                    # 의존성 라이브러리 목록
└── README.md                           # 프로젝트 설명 문서
```

## 🚀 실행 방법 (Quick Start)

### 1. 환경 설정 및 의존성 설치

```bash
python -m venv venv
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 데이터 수집 및 분석 실행

```bash
# 데이터 수집 스크립트 실행
python src/fetch_data.py

# Jupyter Notebook 실행
jupyter notebook analysis.ipynb
```

### 3. Streamlit 대시보드 실행

```bash
streamlit run app.py
```

## 📊 데이터 정보 & 라이선스

- **출처**: Yahoo Finance (`yfinance` API)
- **종목**: 삼성전자 (`005930.KS`)
- **기간**: 2024년 1월 1일 ~ 현재
- **라이선스 유의사항**: 본 데이터는 학술/분석 목적으로 수집되었으며 상업적 재배포를 금합니다.
