import os
import pandas as pd
import yfinance as yf

def fetch_samsung_data():
    print("Fetching Samsung Electronics (005930.KS) stock data from Yahoo Finance (2024 to present)...")
    
    # 2024-01-01 ~ 최근까지 데이터 수집
    ticker = "005930.KS"
    start_date = "2024-01-01"
    
    df = yf.download(ticker, start=start_date, progress=False)
    
    if df.empty:
        raise ValueError(f"No data fetched for {ticker} starting from {start_date}.")
    
    # MultiIndex 컬럼일 경우 단일 레벨로 정리
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df.reset_index(inplace=True)
    
    # 컬럼 이름 정제
    df.rename(columns={
        "Date": "Date",
        "Open": "Open",
        "High": "High",
        "Low": "Low",
        "Close": "Close",
        "Adj Close": "Adj_Close",
        "Volume": "Volume"
    }, inplace=True)
    
    # 저장 디렉토리 생성
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", "samsung_stock_2024_present.csv")
    
    # 날짜 정렬 및 결측치 체크
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values('Date', inplace=True)
    
    # Forward fill 결측치 처리 (필요시)
    df.ffill(inplace=True)
    
    df.to_csv(csv_path, index=False)
    print(f"Data successfully fetched and saved to {csv_path}")
    print(f"Total data points: {len(df)}")
    print(f"Date range: {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}")
    print("\nFirst 5 rows:")
    print(df.head())

if __name__ == "__main__":
    fetch_samsung_data()
