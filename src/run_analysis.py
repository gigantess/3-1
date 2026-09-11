import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 폰트 설정 (Windows/Cross-platform 지원)
plt.rcParams['font.family'] = 'Malgun Gothic' if os.name == 'nt' else 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font=plt.rcParams['font.family'])

from analysis_utils import (
    load_and_preprocess_data,
    calculate_technical_indicators,
    decompose_time_series,
    simple_baseline_forecast,
    advanced_time_series_forecast,
    evaluate_forecast_models
)

def main():
    print("Starting Phase 2: Time Series Analysis & Visualization Chart Generation...")
    os.makedirs("images", exist_ok=True)
    
    # 1. 데이터 로드 및 기술적 지표 계산
    raw_df = load_and_preprocess_data("data/samsung_stock_2024_present.csv")
    df = calculate_technical_indicators(raw_df)
    
    print(f"Loaded dataset: {len(df)} rows from {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}")
    
    # -------------------------------------------------------------
    # Chart 1: 종가 추이, 이동평균선(20일/50일), 볼린저 밴드
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(df['Date'], df['Close'], label='종가 (Close)', color='#1f77b4', linewidth=1.8)
    ax.plot(df['Date'], df['SMA_20'], label='20일 이동평균 (SMA 20)', color='#ff7f0e', linestyle='--', linewidth=1.5)
    ax.plot(df['Date'], df['SMA_50'], label='50일 이동평균 (SMA 50)', color='#2ca02c', linestyle='-.', linewidth=1.5)
    
    # 볼린저 밴드 채우기
    ax.fill_between(df['Date'], df['Lower_Band'], df['Upper_Band'], color='#1f77b4', alpha=0.12, label='볼린저 밴드 (±2 Std)')
    
    ax.set_title("삼성전자 (005930.KS) 주가 추이 및 이동평균 / 볼린저 밴드 (2024~현재)", fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel("날짜 (Date)", fontsize=12)
    ax.set_ylabel("주가 (KRW)", fontsize=12)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    chart1_path = "images/01_price_trend_and_ma.png"
    plt.savefig(chart1_path, dpi=300)
    plt.close()
    print(f"Chart 1 saved to {chart1_path}")

    # -------------------------------------------------------------
    # Chart 2: 월별 수익률 및 요일별 평균 변동성
    # -------------------------------------------------------------
    monthly_df = df.groupby('YearMonth')['Daily_Return'].sum().reset_index()
    monthly_df['YearMonth_Str'] = monthly_df['YearMonth'].astype(str)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 월별 누적 수익률 바 차트
    colors = ['#d62728' if val < 0 else '#1f77b4' for val in monthly_df['Daily_Return']]
    bars = ax1.bar(monthly_df['YearMonth_Str'], monthly_df['Daily_Return'], color=colors, alpha=0.85)
    ax1.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax1.set_title("월별 누적 수익률 (%)", fontsize=14, fontweight='bold')
    ax1.set_xlabel("년-월", fontsize=11)
    ax1.set_ylabel("수익률 (%)", fontsize=11)
    ax1.tick_params(axis='x', rotation=45)
    
    # 요일별 평균 수익률 및 변동성
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_df = df.groupby('DayOfWeek')['Daily_Return'].agg(['mean', 'std']).reindex(day_order).reset_index()
    day_df['Day_KR'] = ['월요일', '화요일', '수요일', '목요일', '금요일']
    
    ax2.bar(day_df['Day_KR'], day_df['std'], color='#9467bd', alpha=0.8)
    ax2.set_title("요일별 일일 수익률 변동성 (표준편차 %)", fontsize=14, fontweight='bold')
    ax2.set_xlabel("요일", fontsize=11)
    ax2.set_ylabel("표준편차 (%)", fontsize=11)
    
    plt.suptitle("삼성전자 월별 수익률 및 요일별 변동성 분석", fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    chart2_path = "images/02_monthly_returns_bar.png"
    plt.savefig(chart2_path, dpi=300)
    plt.close()
    print(f"Chart 2 saved to {chart2_path}")

    # -------------------------------------------------------------
    # Chart 3: 시계열 분해 (Trend, Seasonal, Resid)
    # -------------------------------------------------------------
    decomp_df, decomposition = decompose_time_series(df, period=20)
    
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    axes[0].plot(decomp_df.index, decomp_df['Observed'], color='#1f77b4', linewidth=1.2)
    axes[0].set_ylabel('관측치 (Observed)', fontsize=10)
    axes[0].set_title("시계열 성분 분해 (Seasonal Decomposition - Trend / Seasonal / Resid)", fontsize=15, fontweight='bold')
    
    axes[1].plot(decomp_df.index, decomp_df['Trend'], color='#ff7f0e', linewidth=1.5)
    axes[1].set_ylabel('추세 (Trend)', fontsize=10)
    
    axes[2].plot(decomp_df.index, decomp_df['Seasonal'], color='#2ca02c', linewidth=1.0)
    axes[2].set_ylabel('계절성 (Seasonal)', fontsize=10)
    
    axes[3].scatter(decomp_df.index, decomp_df['Resid'], color='#d62728', s=10, alpha=0.6)
    axes[3].axhline(0, color='black', linestyle='--', linewidth=0.8)
    axes[3].set_ylabel('잔차 (Resid)', fontsize=10)
    axes[3].set_xlabel('날짜', fontsize=11)
    
    for ax in axes:
        ax.grid(True, linestyle=':', alpha=0.5)
        
    plt.tight_layout()
    chart3_path = "images/03_seasonal_decomposition.png"
    plt.savefig(chart3_path, dpi=300)
    plt.close()
    print(f"Chart 3 saved to {chart3_path}")

    # -------------------------------------------------------------
    # Chart 4: 고도화 시계열 예측 (ARIMA & Holt & OLS 비교)
    # -------------------------------------------------------------
    arima_df = advanced_time_series_forecast(df, forecast_days=30, method='arima')
    holt_df = advanced_time_series_forecast(df, forecast_days=30, method='holt')
    ols_df = advanced_time_series_forecast(df, forecast_days=30, method='linear')
    
    fig, ax = plt.subplots(figsize=(14, 6))
    recent_history = df.tail(90)
    
    ax.plot(recent_history['Date'], recent_history['Close'], label='최근 주가 추이 (관측치)', color='#1f77b4', linewidth=2.0)
    ax.plot(arima_df['Date'], arima_df['Forecast_Close'], label='ARIMA 모델 예측 (자기회귀)', color='#8b5cf6', linestyle='-', linewidth=2.2, marker='o', markersize=3)
    ax.plot(holt_df['Date'], holt_df['Forecast_Close'], label='Holt 이중 지수평활 예측', color='#10b981', linestyle='--', linewidth=2.0)
    ax.plot(ols_df['Date'], ols_df['Forecast_Close'], label='OLS 선형회귀 추세선', color='#f59e0b', linestyle=':', linewidth=1.8)
    
    ax.fill_between(arima_df['Date'], arima_df['Lower_Bound'], arima_df['Upper_Bound'], color='#8b5cf6', alpha=0.12, label='ARIMA 95% 예측 신뢰 구간')
    
    ax.set_title("삼성전자 향후 30 영업일 고도화 시계열 주가 예측 (ARIMA vs Holt vs OLS)", fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel("날짜 (Date)", fontsize=12)
    ax.set_ylabel("주가 (KRW)", fontsize=12)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    chart4_path = "images/04_baseline_forecast.png"
    plt.savefig(chart4_path, dpi=300)
    plt.close()
    print(f"Chart 4 saved to {chart4_path}")

    # 백테스팅 성능 평가 출력
    eval_df = evaluate_forecast_models(df, test_days=30)
    print("\n[Model Accuracy Backtesting Results (Holdout 30 days)]")
    print(eval_df.to_string(index=False))

    print("Phase 2 analysis and visualization completed successfully!")

if __name__ == "__main__":
    main()
