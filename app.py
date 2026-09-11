import os
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from statsmodels.tsa.seasonal import seasonal_decompose

# src 모듈 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from analysis_utils import load_and_preprocess_data

# Streamlit 페이지 설정
st.set_page_config(
    page_title="삼성전자 주가 시계열 분석 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-delta-pos {
        color: #22C55E;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .metric-delta-neg {
        color: #EF4444;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        border-radius: 8px 8px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    file_path = "data/samsung_stock_2024_present.csv"
    if not os.path.exists(file_path):
        file_path = "../data/samsung_stock_2024_present.csv"
    df = load_and_preprocess_data(file_path)
    
    # 추가 기술적 지표 계산
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_120'] = df['Close'].rolling(window=120).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    df['Std_20'] = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['SMA_20'] + (df['Std_20'] * 2)
    df['Lower_Band'] = df['SMA_20'] - (df['Std_20'] * 2)
    
    df['Daily_Return'] = df['Close'].pct_change() * 100
    df['YearMonth'] = df['Date'].dt.to_period('M')
    df['DayOfWeek'] = df['Date'].dt.day_name()
    return df


df_raw = load_data()

# ==========================================
# 사이드바 컨트롤 파널
# ==========================================
st.sidebar.header("🎛️ 분석 옵션 & 필터")

# 1. 날짜 범위 선택
min_date = df_raw['Date'].min().date()
max_date = df_raw['Date'].max().date()

start_date, end_date = st.sidebar.date_input(
    "🗓️ 분석 기간 선택",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# 날짜 필터링 적용
mask = (df_raw['Date'].dt.date >= start_date) & (df_raw['Date'].dt.date <= end_date)
df = df_raw.loc[mask].copy().reset_index(drop=True)

st.sidebar.markdown("---")

# 2. 이동평균선 선택
st.sidebar.subheader("📈 이동평균선(MA) 선택")
selected_mas = st.sidebar.multiselect(
    "표시할 이동평균선 선택",
    options=['SMA 10일', 'SMA 20일', 'SMA 50일', 'SMA 120일', 'EMA 20일'],
    default=['SMA 20일', 'SMA 50일']
)

# 3. 보조 지표 옵션
st.sidebar.subheader("🛡️ 보조 지표 옵션")
show_bollinger = st.sidebar.checkbox("볼린저 밴드 (±2 Std) 표시", value=True)
show_volume = st.sidebar.checkbox("하단 거래량(Volume) 차트 표시", value=True)
chart_type = st.sidebar.radio("차트 유형 선택", options=["선 그래프 (Line)", "캔들스틱 (Candlestick)"], index=0)

st.sidebar.markdown("---")

# 4. 베이스라인 예측 시뮬레이션 설정
st.sidebar.subheader("🔮 예측 시뮬레이션 설정")
forecast_days = st.sidebar.slider("향후 예측 기간 (영업일)", min_value=5, max_value=60, value=30, step=5)
trend_window = st.sidebar.slider("추세 계산 기준 과거 일수", min_value=10, max_value=60, value=30, step=5)
trend_bias = st.sidebar.slider("추세 가중치 (시뮬레이션 조절)", min_value=-2.0, max_value=2.0, value=0.0, step=0.1, help="가중치가 (+)이면 보수적/긍정 시나리오, (-)이면 하방 시나리오를 반영합니다.")

# ==========================================
# 메인 헤더 & KPI 메트릭 카드
# ==========================================
st.markdown('<div class="main-header">📊 삼성전자 (005930.KS) 시계열 분석 & 예측 대시보드</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">조회 기간: <b>{start_date.strftime("%Y-%m-%d")}</b> ~ <b>{end_date.strftime("%Y-%m-%d")}</b> ({len(df)} 거래일 데이터)</div>', unsafe_allow_html=True)

if len(df) > 0:
    first_close = df['Close'].iloc[0]
    last_close = df['Close'].iloc[-1]
    change_val = last_close - first_close
    change_pct = (change_val / first_close) * 100
    
    max_price = df['High'].max()
    min_price = df['Low'].min()
    avg_vol = df['Volume'].mean()
    volatility = df['Daily_Return'].std()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="최근 종가",
            value=f"{last_close:,.0f} 원",
            delta=f"{change_pct:+.2f}% (기간 대비)",
            delta_color="normal"
        )
    with col2:
        st.metric(
            label="기간 최고가",
            value=f"{max_price:,.0f} 원"
        )
    with col3:
        st.metric(
            label="기간 최저가",
            value=f"{min_price:,.0f} 원"
        )
    with col4:
        st.metric(
            label="일평균 거래량",
            value=f"{avg_vol/1e6:.2f} M주"
        )
    with col5:
        st.metric(
            label="일일 변동성 (표준편차)",
            value=f"{volatility:.2f}%"
        )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 탭 구성
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 주가 추이 & 기술적 지표",
    "📊 수익률 & 요일별 변동성",
    "🔍 시계열 성분 분해",
    "🔮 30일 예측 시뮬레이션",
    "📋 데이터 탐색 & 다운로드"
])

# ------------------------------------------
# Tab 1: 주가 추이 및 기술적 지표
# ------------------------------------------
with tab1:
    st.subheader("📈 인터랙티브 주가 추이 차트")
    
    if len(df) == 0:
        st.warning("선택한 날짜 범위에 데이터가 없습니다.")
    else:
        # Subplots 생성 (주가 + 거래량)
        if show_volume:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.75, 0.25])
        else:
            fig = make_subplots(rows=1, cols=1)

        # 메인 주가 차트
        if chart_type == "캔들스틱 (Candlestick)":
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="주가 (OHLC)",
                    increasing_line_color='#22C55E',
                    decreasing_line_color='#EF4444'
                ),
                row=1, col=1
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Close'],
                    mode='lines',
                    name="종가 (Close)",
                    line=dict(color='#2563EB', width=2)
                ),
                row=1, col=1
            )

        # 이동평균선 오버레이
        ma_colors = {
            'SMA 10일': ('SMA_10', '#F59E0B', 'dash'),
            'SMA 20일': ('SMA_20', '#10B981', 'solid'),
            'SMA 50일': ('SMA_50', '#8B5CF6', 'dashdot'),
            'SMA 120일': ('SMA_120', '#EC4899', 'longdash'),
            'EMA 20일': ('EMA_20', '#06B6D4', 'dot')
        }

        for ma_name in selected_mas:
            if ma_name in ma_colors:
                col_name, color_code, dash_style = ma_colors[ma_name]
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df[col_name],
                        mode='lines',
                        name=ma_name,
                        line=dict(color=color_code, width=1.5, dash=dash_style)
                    ),
                    row=1, col=1
                )

        # 볼린저 밴드
        if show_bollinger:
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Upper_Band'],
                    mode='lines',
                    name="볼린저 상한 (Upper Band)",
                    line=dict(color='rgba(148, 163, 184, 0.5)', width=1, dash='dot')
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Lower_Band'],
                    mode='lines',
                    name="볼린저 하한 (Lower Band)",
                    line=dict(color='rgba(148, 163, 184, 0.5)', width=1, dash='dot'),
                    fill='tonexty',
                    fillcolor='rgba(148, 163, 184, 0.12)'
                ),
                row=1, col=1
            )

        # 하단 거래량 차트
        if show_volume:
            colors = ['#22C55E' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#EF4444' for i in range(len(df))]
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['Volume'],
                    name="거래량 (Volume)",
                    marker_color=colors,
                    opacity=0.7
                ),
                row=2, col=1
            )

        fig.update_layout(
            height=650,
            hovermode="x unified",
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white",
            xaxis_rangeslider_visible=False
        )

        fig.update_yaxes(title_text="주가 (KRW)", row=1, col=1)
        if show_volume:
            fig.update_yaxes(title_text="거래량", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)

        st.info("💡 **차트 활용 팁**: 마우스 드래그로 원하는 구간을 확대(Zoom)할 수 있으며, 범례 항목을 클릭하여 특정 지표를 켜거나 끌 수 있습니다.")

# ------------------------------------------
# Tab 2: 수익률 & 요일별 변동성
# ------------------------------------------
with tab2:
    st.subheader("📊 수익률 및 요일별 변동성 분석")

    r_col1, r_col2 = st.columns(2)

    with r_col1:
        st.markdown("#### 📅 월별 누적 수익률 (%)")
        monthly_df = df.groupby('YearMonth')['Daily_Return'].sum().reset_index()
        monthly_df['YearMonth_Str'] = monthly_df['YearMonth'].astype(str)

        fig_m = px.bar(
            monthly_df,
            x='YearMonth_Str',
            y='Daily_Return',
            labels={'YearMonth_Str': '년-월', 'Daily_Return': '수익률 (%)'},
            color='Daily_Return',
            color_continuous_scale=['#EF4444', '#E2E8F0', '#2563EB'],
            color_continuous_midpoint=0
        )
        fig_m.update_layout(height=400, template="plotly_white", coloraxis_showscale=False)
        st.plotly_chart(fig_m, use_container_width=True)

    with r_col2:
        st.markdown("#### 🗓️ 요일별 평균 수익률 & 변동성 (표준편차)")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        day_kr = {'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일', 'Thursday': '목요일', 'Friday': '금요일'}
        
        day_stats = df.groupby('DayOfWeek')['Daily_Return'].agg(['mean', 'std']).reindex(day_order).reset_index()
        day_stats['Day_KR'] = day_stats['DayOfWeek'].map(day_kr)

        fig_d = px.bar(
            day_stats,
            x='Day_KR',
            y='std',
            text=day_stats['std'].apply(lambda x: f"{x:.2f}%"),
            labels={'Day_KR': '요일', 'std': '변동성 (표준편차 %)'},
            color_discrete_sequence=['#8B5CF6']
        )
        fig_d.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig_d, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📉 일일 수익률 분포 (Histogram & KDE)")
    
    fig_hist = px.histogram(
        df.dropna(subset=['Daily_Return']),
        x='Daily_Return',
        nbins=40,
        marginal='box',
        title="일일 수익률 (%) 분포 현황",
        labels={'Daily_Return': '일일 수익률 (%)'},
        color_discrete_sequence=['#3B82F6']
    )
    fig_hist.update_layout(height=380, template="plotly_white")
    st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------------------------
# Tab 3: 시계열 성분 분해
# ------------------------------------------
with tab3:
    st.subheader("🔍 시계열 성분 분해 (Seasonal Decomposition)")
    
    decomp_period = st.radio("분해 주기(Period) 선택", options=[5, 10, 20, 30], index=2, horizontal=True, help="20일은 보통 1개월 영업일 주기를 의미합니다.")

    if len(df) < decomp_period * 2:
        st.error("성분 분해를 수행하기에 선택된 기간의 데이터 포인트가 부족합니다. 더 긴 기간을 선택해주세요.")
    else:
        ts_df = df.set_index('Date')['Close'].dropna()
        decomposition = seasonal_decompose(ts_df, model='additive', period=decomp_period)

        fig_decomp = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            subplot_titles=("1. 관측치 (Observed Price)", "2. 추세 성분 (Trend)", "3. 계절성 성분 (Seasonal)", "4. 잔차 / 노이즈 (Residuals)")
        )

        fig_decomp.add_trace(go.Scatter(x=ts_df.index, y=decomposition.observed, mode='lines', color='#2563EB'), row=1, col=1)
        fig_decomp.add_trace(go.Scatter(x=ts_df.index, y=decomposition.trend, mode='lines', color='#F59E0B'), row=2, col=1)
        fig_decomp.add_trace(go.Scatter(x=ts_df.index, y=decomposition.seasonal, mode='lines', color='#10B981'), row=3, col=1)
        fig_decomp.add_trace(go.Scatter(x=ts_df.index, y=decomposition.resid, mode='markers', marker=dict(size=4, color='#EF4444')), row=4, col=1)

        fig_decomp.update_layout(height=750, template="plotly_white", showlegend=False)
        st.plotly_chart(fig_decomp, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.success("📈 **추세 (Trend)**\n\n장기적인 방향성을 의미하며 노이즈가 제거된 주가의 본질적 흐름을 나타냅니다.")
        with c2:
            st.info("🔄 **계절성 (Seasonal)**\n\n지정된 주기(Period) 동안 반복적으로 나타나는 순환적 파동 패턴입니다.")
        with c3:
            st.warning("⚡ **잔차 (Resid)**\n\n추세와 계절성으로 설명되지 않는 돌발 이벤트 및 노이즈 변동성입니다.")

# ------------------------------------------
# Tab 4: 30일 예측 시뮬레이션
# ------------------------------------------
with tab4:
    st.subheader("🔮 30일 이동평균 베이스라인 예측 시뮬레이션")
    st.write("사이드바의 **[예측 기간]**, **[추세 기준 일수]**, **[추세 가중치]** 조절 슬라이더를 통해 향후 시나리오를 가상 테스트할 수 있습니다.")

    if len(df) < trend_window:
        st.error(f"최소 {trend_window}일 이상의 데이터가 필요합니다.")
    else:
        last_date = df['Date'].max()
        last_close = df['Close'].iloc[-1]
        
        # 최근 N일 추세 계산
        recent_subset = df.tail(trend_window)
        slope = (recent_subset['Close'].iloc[-1] - recent_subset['Close'].iloc[0]) / trend_window
        adjusted_slope = slope + (trend_bias * (last_close * 0.001))
        
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days, freq='B')
        forecast_values = [last_close + (adjusted_slope * (i + 1)) for i in range(forecast_days)]
        
        # 상/하한 신뢰 구간 가상 생성 (일일 변동성 기준)
        daily_std = df['Daily_Return'].std() * 0.01 * last_close
        upper_bound = [v + (1.96 * daily_std * np.sqrt(i + 1)) for i, v in enumerate(forecast_values)]
        lower_bound = [v - (1.96 * daily_std * np.sqrt(i + 1)) for i, v in enumerate(forecast_values)]

        forecast_df = pd.DataFrame({
            'Date': future_dates,
            'Forecast_Close': forecast_values,
            'Upper_Bound': upper_bound,
            'Lower_Bound': lower_bound
        })

        # 시각화
        recent_history = df.tail(90)
        fig_fc = go.Figure()

        fig_fc.add_trace(go.Scatter(
            x=recent_history['Date'],
            y=recent_history['Close'],
            mode='lines',
            name="과거 실제 주가 (Recent Close)",
            line=dict(color='#2563EB', width=2.5)
        ))

        fig_fc.add_trace(go.Scatter(
            x=forecast_df['Date'],
            y=forecast_df['Forecast_Close'],
            mode='lines+markers',
            name=f"향후 {forecast_days}일 예측 추세선",
            line=dict(color='#EC4899', width=2.5, dash='dash')
        ))

        fig_fc.add_trace(go.Scatter(
            x=forecast_df['Date'],
            y=forecast_df['Upper_Bound'],
            mode='lines',
            name="신뢰구간 상한 (+95%)",
            line=dict(color='rgba(236, 72, 153, 0.3)', width=1, dash='dot')
        ))

        fig_fc.add_trace(go.Scatter(
            x=forecast_df['Date'],
            y=forecast_df['Lower_Bound'],
            mode='lines',
            name="신뢰구간 하한 (-95%)",
            line=dict(color='rgba(236, 72, 153, 0.3)', width=1, dash='dot'),
            fill='tonexty',
            fillcolor='rgba(236, 72, 153, 0.1)'
        ))

        fig_fc.update_layout(
            height=500,
            title=f"삼성전자 향후 {forecast_days} 영업일 베이스라인 시뮬레이션 (일일 추세 기울기: {adjusted_slope:+.1f} 원/일)",
            xaxis_title="날짜 (Date)",
            yaxis_title="주가 (KRW)",
            template="plotly_white",
            hovermode="x unified"
        )

        st.plotly_chart(fig_fc, use_container_width=True)

        st.markdown("#### 📄 예측 데이터 명세표")
        st.dataframe(
            forecast_df.style.format({
                'Forecast_Close': '{:,.0f} 원',
                'Upper_Bound': '{:,.0f} 원',
                'Lower_Bound': '{:,.0f} 원'
            }),
            use_container_width=True
        )

        # 예측 결과 CSV 다운로드
        csv_forecast = forecast_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 30일 예측 시뮬레이션 데이터 CSV 다운로드",
            data=csv_forecast,
            file_name="samsung_stock_30d_forecast_simulation.csv",
            mime="text/csv"
        )

# ------------------------------------------
# Tab 5: 데이터 탐색 & 다운로드
# ------------------------------------------
with tab5:
    st.subheader("📋 전체 시계열 데이터 탐색")
    
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        st.markdown("##### 🔍 선택 기간 데이터셋 테이블")
        st.dataframe(
            df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'SMA_20', 'SMA_50', 'Daily_Return']].style.format({
                'Open': '{:,.0f}',
                'High': '{:,.0f}',
                'Low': '{:,.0f}',
                'Close': '{:,.0f}',
                'Volume': '{:,.0f}',
                'SMA_20': '{:,.1f}',
                'SMA_50': '{:,.1f}',
                'Daily_Return': '{:+.2f}%'
            }),
            use_container_width=True,
            height=450
        )
    with col_d2:
        st.markdown("##### 📊 요약 통계량")
        st.dataframe(
            df[['Close', 'Volume', 'Daily_Return']].describe().style.format('{:,.2f}'),
            use_container_width=True
        )

    # 필터링 데이터 CSV 다운로드
    csv_filtered = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 필터링된 주가 데이터 전체 CSV 다운로드",
        data=csv_filtered,
        file_name=f"samsung_stock_{start_date}_{end_date}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("© 2026 Samsung Stock Time Series Analytics Dashboard | Powered by Streamlit & Plotly")
