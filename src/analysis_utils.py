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

def advanced_arima_forecast(df, forecast_days=30, order=(1, 1, 1), auto_fit=True):
    """
    statsmodels ARIMA 모델을 사용하고 AIC 최적 차수(p,d,q)를 자동 검색하여 향후 주가를 예측합니다.
    """
    df_clean = df.dropna(subset=['Close']).copy()
    if len(df_clean) < 15:
        raise ValueError("ARIMA 예측을 위해 최소 15개 이상의 데이터가 필요합니다.")
        
    ts = df_clean['Close'].values
    last_date = df_clean['Date'].max()
    
    best_order = order
    if auto_fit:
        best_aic = float('inf')
        for p in range(3):
            for d in [1]:
                for q in range(3):
                    try:
                        m = ARIMA(ts, order=(p, d, q)).fit()
                        if m.aic < best_aic:
                            best_aic = m.aic
                            best_order = (p, d, q)
                    except Exception:
                        pass
                        
    try:
        model = ARIMA(ts, order=best_order)
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

def ensemble_forecast(df, forecast_days=30, trend_window=30):
    """
    Auto-ARIMA, Holt 지수평활, 선형회귀(OLS) 모델을 결합한 최적 가중 앙상블(Weighted Ensemble) 예측
    """
    f_arima = advanced_arima_forecast(df, forecast_days=forecast_days, auto_fit=True)
    f_holt = advanced_holt_forecast(df, forecast_days=forecast_days)
    f_ols = simple_baseline_forecast(df, forecast_days=forecast_days, trend_window=trend_window, method='linear')
    
    ens_vals = 0.5 * f_arima['Forecast_Close'] + 0.3 * f_holt['Forecast_Close'] + 0.2 * f_ols['Forecast_Close']
    ens_upper = 0.5 * f_arima['Upper_Bound'] + 0.3 * f_holt['Upper_Bound'] + 0.2 * f_ols['Upper_Bound']
    ens_lower = 0.5 * f_arima['Lower_Bound'] + 0.3 * f_holt['Lower_Bound'] + 0.2 * f_ols['Lower_Bound']
    
    forecast_df = pd.DataFrame({
        'Date': f_arima['Date'],
        'Forecast_Close': ens_vals,
        'Upper_Bound': ens_upper,
        'Lower_Bound': ens_lower
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

def advanced_time_series_forecast(df, forecast_days=30, trend_window=30, method='ensemble', trend_bias=0.0):
    """
    통합 시계열 예측 엔트리 포인트 (최적 앙상블, Auto-ARIMA, Holt 지수평활, OLS 선형회귀, 이동평균)
    """
    if method == 'ensemble':
        return ensemble_forecast(df, forecast_days=forecast_days, trend_window=trend_window)
    elif method == 'arima':
        return advanced_arima_forecast(df, forecast_days=forecast_days, auto_fit=True)
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
        '최적 앙상블 (Auto-ARIMA+Holt+OLS)': 'ensemble',
        'Auto-ARIMA (AIC 최적화)': 'arima',
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

def validate_2024_to_2025_forecast(df):
    """
    2024년 주가 데이터(학습 데이터)만을 이용하여 2025년 주가를 예측하고,
    실제 2025년 주가 데이터와 1:1 비교하여 오차율(MAPE %, MAE, RMSE)을 산출합니다.
    """
    df_clean = df.dropna(subset=['Close']).copy()
    df_2024 = df_clean[df_clean['Date'].dt.year == 2024].sort_values('Date').reset_index(drop=True)
    df_2025 = df_clean[df_clean['Date'].dt.year == 2025].sort_values('Date').reset_index(drop=True)
    
    if len(df_2024) < 30 or len(df_2025) == 0:
        return pd.DataFrame(), {}
        
    n_days_2025 = len(df_2025)
    actual_2025 = df_2025['Close'].values
    
    methods = {
        '최적 앙상블 (Auto-ARIMA+Holt+OLS)': 'ensemble',
        'Auto-ARIMA (AIC 최적화)': 'arima',
        'Holt 지수 평활법': 'holt',
        '선형 회귀 (OLS)': 'linear',
        '이동평균 (MA)': 'ma'
    }
    
    results = []
    forecast_dfs = {}
    
    for label, code in methods.items():
        try:
            fc_df = advanced_time_series_forecast(df_2024, forecast_days=n_days_2025, method=code)
            fc_df['Date'] = df_2025['Date'].values[:len(fc_df)]
            forecast_dfs[code] = fc_df
            
            preds_full = fc_df['Forecast_Close'].values[:len(actual_2025)]
            
            mae_full = np.mean(np.abs(actual_2025 - preds_full))
            rmse_full = np.sqrt(np.mean((actual_2025 - preds_full) ** 2))
            mape_full = np.mean(np.abs((actual_2025 - preds_full) / actual_2025)) * 100
            
            half_n = min(120, len(actual_2025))
            mae_half = np.mean(np.abs(actual_2025[:half_n] - preds_full[:half_n]))
            mape_half = np.mean(np.abs((actual_2025[:half_n] - preds_full[:half_n]) / actual_2025[:half_n])) * 100
            
            results.append({
                '모델명': label,
                '2025 상반기 MAPE (%)': round(mape_half, 2),
                '2025 전체 MAPE (%)': round(mape_full, 2),
                '전체 MAE (원)': round(mae_full, 1),
                '전체 RMSE (원)': round(rmse_full, 1)
            })
        except Exception as e:
            continue
            
    res_df = pd.DataFrame(results).sort_values(by='2025 전체 MAPE (%)').reset_index(drop=True)
    return res_df, forecast_dfs




