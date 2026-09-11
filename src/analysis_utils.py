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

def simple_baseline_forecast(df, forecast_days=30):
    """
    최근 이동평균 기반 베이스라인 30일 추세 예측
    """
    last_date = df['Date'].max()
    last_close = df['Close'].iloc[-1]
    recent_trend = (df['Close'].iloc[-1] - df['Close'].iloc[-30]) / 30
    
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days, freq='B')
    forecast_values = [last_close + (recent_trend * (i + 1)) for i in range(forecast_days)]
    
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'Forecast_Close': forecast_values
    })
    return forecast_df
