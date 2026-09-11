import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose

def load_and_preprocess_data(file_path="data/samsung_stock_2024_present.csv"):
    """
    CSV 주가 데이터를 로드하고 전처리를 수행합니다.
    """
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    
    # 결측치 확인 및 Forward Fill
    df = df.ffill().bfill()
    
    # 기본 컬럼 타입 검증
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    return df

def calculate_technical_indicators(df):
    """
    이동평균(SMA/EMA), 변동성(Rolling Std, 볼린저밴드), 수익률(Daily Return) 계산
    """
    df = df.copy()
    
    # 이동평균선
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # 20일 변동성 및 볼린저 밴드
    df['Std_20'] = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['SMA_20'] + (df['Std_20'] * 2)
    df['Lower_Band'] = df['SMA_20'] - (df['Std_20'] * 2)
    
    # 일별 수익률 (%)
    df['Daily_Return'] = df['Close'].pct_change() * 100
    
    # 월/요일 정보
    df['YearMonth'] = df['Date'].dt.to_period('M')
    df['DayOfWeek'] = df['Date'].dt.day_name()
    
    return df

def decompose_time_series(df, period=20):
    """
    Statsmodels seasonal_decompose를 이용한 시계열 성분 분해 (추세, 계절성, 잔차)
    """
    ts = df.set_index('Date')['Close'].dropna()
    decomposition = seasonal_decompose(ts, model='additive', period=period)
    
    result_df = pd.DataFrame({
        'Observed': decomposition.observed,
        'Trend': decomposition.trend,
        'Seasonal': decomposition.seasonal,
        'Resid': decomposition.resid
    })
    return result_df, decomposition

def simple_baseline_forecast(df, forecast_days=30, trend_window=30, method='linear', trend_bias=0.0):
    """
    최근 N일간의 데이터를 기반으로 선형 회귀(OLS) 추세를 산출하여 향후 주가를 예측합니다.
    """
    df_clean = df.dropna(subset=['Close']).copy()
    if len(df_clean) < 5:
        raise ValueError("예측을 위해 최소 5개 이상의 데이터가 필요합니다.")
        
    recent_subset = df_clean.tail(min(trend_window, len(df_clean)))
    
    x = np.arange(len(recent_subset))
    y = recent_subset['Close'].values
    
    if method == 'linear':
        # 최소자승법(OLS) 1차 선형 회귀 (기울기, 절편)
        slope, intercept = np.polyfit(x, y, 1)
    elif method == 'ma':
        # 이동평균 변화율 기반
        slope = (y[-1] - y[0]) / len(y) if len(y) > 1 else 0
        intercept = y[-1] - slope * (len(y) - 1)
    else:
        slope, intercept = np.polyfit(x, y, 1)
        
    last_date = df_clean['Date'].max()
    last_close = df_clean['Close'].iloc[-1]
    
    # 시뮬레이션 추세 바이어스 적용
    adjusted_slope = slope + (trend_bias * (last_close * 0.001))
    
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days, freq='B')
    
    # 마지막 종가로부터의 예측 변화
    forecast_values = [last_close + (adjusted_slope * (i + 1)) for i in range(forecast_days)]
    
    # 회귀 잔차(Residual) 기반 표준 오차 및 95% 신뢰 구간 계산
    y_pred = intercept + slope * x
    residuals = y - y_pred
    std_err = np.std(residuals) if len(residuals) > 1 else (last_close * 0.01)
    if std_err == 0:
        std_err = last_close * 0.01
        
    upper_bound = [v + (1.96 * std_err * np.sqrt(1 + (i + 1) / len(recent_subset))) for i, v in enumerate(forecast_values)]
    lower_bound = [v - (1.96 * std_err * np.sqrt(1 + (i + 1) / len(recent_subset))) for i, v in enumerate(forecast_values)]
    
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'Forecast_Close': forecast_values,
        'Upper_Bound': upper_bound,
        'Lower_Bound': lower_bound
    })
    return forecast_df

