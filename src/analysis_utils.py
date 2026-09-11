import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.api import Holt

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
        slope, intercept = np.polyfit(x, y, 1)
    elif method == 'ma':
        slope = (y[-1] - y[0]) / len(y) if len(y) > 1 else 0
        intercept = y[-1] - slope * (len(y) - 1)
    else:
        slope, intercept = np.polyfit(x, y, 1)
        
    last_date = df_clean['Date'].max()
    last_close = df_clean['Close'].iloc[-1]
    
    adjusted_slope = slope + (trend_bias * (last_close * 0.001))
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days, freq='B')
    forecast_values = [last_close + (adjusted_slope * (i + 1)) for i in range(forecast_days)]
    
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

def advanced_arima_forecast(df, forecast_days=30, order=(1, 1, 1)):
    """
    statsmodels ARIMA 모델을 사용하여 시계열 자기회귀 및 이동평균 오차 기반 향후 주가를 예측합니다.
    """
    df_clean = df.dropna(subset=['Close']).copy()
    if len(df_clean) < 15:
        raise ValueError("ARIMA 예측을 위해 최소 15개 이상의 데이터가 필요합니다.")
        
    ts = df_clean['Close'].values
    last_date = df_clean['Date'].max()
    
    try:
        model = ARIMA(ts, order=order)
        res = model.fit()
        forecast_res = res.get_forecast(steps=forecast_days)
        forecast_values = forecast_res.predicted_mean
        conf_int = forecast_res.conf_int(alpha=0.05)
        
        lower_bound = conf_int[:, 0]
        upper_bound = conf_int[:, 1]
    except Exception as e:
        return advanced_holt_forecast(df, forecast_days=forecast_days)
        
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days, freq='B')
    
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'Forecast_Close': forecast_values,
        'Upper_Bound': upper_bound,
        'Lower_Bound': lower_bound
    })
    return forecast_df

def advanced_holt_forecast(df, forecast_days=30, damped_trend=True):
    """
    Holt's Linear Exponential Smoothing (이중 지수 평활법) 모델 기반 향후 주가 예측
    """
    df_clean = df.dropna(subset=['Close']).copy()
    if len(df_clean) < 10:
        raise ValueError("Holt 예측을 위해 최소 10개 이상의 데이터가 필요합니다.")
        
    ts = df_clean['Close'].values
    last_date = df_clean['Date'].max()
    
    try:
        model = Holt(ts, initialization_method="estimated", damped_trend=damped_trend)
        res = model.fit()
        forecast_values = res.forecast(forecast_days)
        
        residuals = res.resid
        std_err = np.std(residuals) if len(residuals) > 1 else (ts[-1] * 0.01)
        if std_err == 0:
            std_err = ts[-1] * 0.01
            
        upper_bound = [v + (1.96 * std_err * np.sqrt(1 + (i + 1) / len(ts))) for i, v in enumerate(forecast_values)]
        lower_bound = [v - (1.96 * std_err * np.sqrt(1 + (i + 1) / len(ts))) for i, v in enumerate(forecast_values)]
    except Exception as e:
        return simple_baseline_forecast(df, forecast_days=forecast_days, method='linear')
        
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days, freq='B')
    
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'Forecast_Close': forecast_values,
        'Upper_Bound': upper_bound,
        'Lower_Bound': lower_bound
    })
    return forecast_df

def advanced_time_series_forecast(df, forecast_days=30, trend_window=30, method='arima', trend_bias=0.0):
    """
    통합 시계열 예측 엔트리 포인트 (ARIMA, Holt 지수평활, OLS 선형회귀, 이동평균)
    """
    if method == 'arima':
        return advanced_arima_forecast(df, forecast_days=forecast_days)
    elif method == 'holt':
        return advanced_holt_forecast(df, forecast_days=forecast_days)
    else:
        return simple_baseline_forecast(df, forecast_days=forecast_days, trend_window=trend_window, method=method, trend_bias=trend_bias)

def evaluate_forecast_models(df, test_days=30):
    """
    과거 홀드아웃(Backtesting) 검증을 통한 모델별 예측 성능(MAE, RMSE, MAPE %) 평가
    """
    df_clean = df.dropna(subset=['Close']).copy()
    if len(df_clean) < test_days + 30:
        return pd.DataFrame()
        
    train_df = df_clean.iloc[:-test_days]
    test_df = df_clean.iloc[-test_days:]
    actuals = test_df['Close'].values
    
    methods = {
        'ARIMA (자기회귀 모델)': 'arima',
        'Holt 지수 평활법': 'holt',
        '선형 회귀 (OLS)': 'linear',
        '이동평균 (MA)': 'ma'
    }
    
    results = []
    for label, code in methods.items():
        try:
            fc_df = advanced_time_series_forecast(train_df, forecast_days=test_days, method=code)
            preds = fc_df['Forecast_Close'].values[:len(actuals)]
            
            mae = np.mean(np.abs(actuals - preds))
            rmse = np.sqrt(np.mean((actuals - preds) ** 2))
            mape = np.mean(np.abs((actuals - preds) / actuals)) * 100
            
            results.append({
                '모델명': label,
                'MAPE (%)': round(mape, 2),
                'MAE (원)': round(mae, 1),
                'RMSE (원)': round(rmse, 1)
            })
        except Exception:
            continue
            
    res_df = pd.DataFrame(results).sort_values(by='MAPE (%)').reset_index(drop=True)
    return res_df



