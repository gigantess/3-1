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

from analysis_utils import load_and_preprocess_data, simple_baseline_forecast

# Streamlit 페이지 설정
st.set_page_config(
    page_title="삼성전자 주가 시계열 분석 & 초보자 가이드 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일링 (UX & readability 대폭 개선)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }
    
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    
    /* 신호 진단 배너 카드 */
    .signal-banner {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
        border-left: 6px solid #0284C7;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .signal-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0369A1;
        margin-bottom: 6px;
    }
    .signal-desc {
        font-size: 0.95rem;
        color: #334155;
        line-height: 1.5;
    }
    
    /* 쉬운 가이드 박스 */
    .easy-guide-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .easy-guide-title {
        font-size: 1.0rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 8px;
    }
    
    /* 탭 헤더 스타일링 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 16px;
        font-weight: 700;
        font-size: 0.95rem;
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
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)
    df['DayOfWeek'] = df['Date'].dt.day_name()
    return df


df_raw = load_data()

# ==========================================
# 사이드바 컨트롤 파널 (초보자 친화적 설명 포함)
# ==========================================
st.sidebar.header("🎛️ 분석 조건 설정")

# 1. 날짜 범위 선택
min_date = df_raw['Date'].min().date()
max_date = df_raw['Date'].max().date()

start_date, end_date = st.sidebar.date_input(
    "🗓️ 분석 기간 선택",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="원하는 주가 분석 시작일과 종료일을 지정하세요."
)

# 날짜 필터링 적용
mask = (df_raw['Date'].dt.date >= start_date) & (df_raw['Date'].dt.date <= end_date)
df = df_raw.loc[mask].copy().reset_index(drop=True)

st.sidebar.markdown("---")

# 2. 이동평균선 선택
st.sidebar.subheader("📈 평균선(MA) 표시 선택")
selected_mas = st.sidebar.multiselect(
    "차트에 겹쳐볼 평균선 선택",
    options=['SMA 10일 (단기)', 'SMA 20일 (한 달)', 'SMA 50일 (분기)', 'SMA 120일 (반년)', 'EMA 20일 (지수평균)'],
    default=['SMA 20일 (한 달)', 'SMA 50일 (분기)']
)

# 3. 보조 지표 옵션
st.sidebar.subheader("🛡️ 차트 지표 옵션")
show_bollinger = st.sidebar.checkbox("볼린저 밴드 (적정 가격 범위 띠) 표시", value=True)
show_volume = st.sidebar.checkbox("하단 거래량 (매수/매도량) 표시", value=True)
chart_type = st.sidebar.radio("차트 모드", options=["선 그래프 (쉬운 보기)", "캔들스틱 (전문가 보기)"], index=0)

st.sidebar.markdown("---")

# 4. 베이스라인 예측 시뮬레이션 설정
st.sidebar.subheader("🔮 30일 예측 조건 조절")
forecast_method = st.sidebar.selectbox(
    "예측 알고리즘 선택",
    options=["선형 회귀 추세선 (OLS Linear Regression)", "이동평균 추세 (Moving Average slope)"],
    index=0,
    help="최소자승 선형 회귀(OLS)는 과거 N일 데이터 전체의 우상향/우하향 모멘텀을 반영하여 평행선 오류를 방지합니다."
)
forecast_days = st.sidebar.slider("향후 예측 영업일수", min_value=5, max_value=60, value=30, step=5)
trend_window = st.sidebar.slider("추세 판단에 사용할 과거 일수", min_value=10, max_value=60, value=30, step=5)
trend_bias = st.sidebar.slider("추세 가중치 (시뮬레이션 조절)", min_value=-2.0, max_value=2.0, value=0.0, step=0.1, help="(+)로 올리면 긍정적 시나리오, (-)로 내리면 보수적 시나리오가 반영됩니다.")

# 초보자용 용어 설명 가이드 (사이드바 하단)
with st.sidebar.expander("❓ 주식 용어가 어려우신가요? (초보자 가이드)"):
    st.markdown("""
    - **종가**: 해당 날짜 장 마감 시 최종 주가입니다.
    - **이동평균선(MA)**: 최근 N일간 주가의 평균 흐름입니다. 주가의 진행 방향을 보여줍니다.
    - **볼린저 밴드**: 주가가 보통 이 밴드(범위) 안에서 움직입니다. 하단에 닿으면 **단기 저점(싸짐)**, 상단에 닿으면 **단기 고점** 신호로 해석합니다.
    - **거래량**: 하루 동안 거래된 주식 수입니다. 주가가 오를 때 거래량이 커지면 상승 힘이 강합니다.
    """)

# ==========================================
# 메인 헤더 & AI 주가 종합 진단 바
# ==========================================
st.markdown('<div class="main-title">📊 삼성전자 (005930.KS) 시계열 분석 & 예측 대시보드</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">선택 기간: <b>{start_date.strftime("%Y년 %m월 %d일")}</b> ~ <b>{end_date.strftime("%Y년 %m월 %d일")}</b> (총 {len(df)}개 거래일 데이터)</div>', unsafe_allow_html=True)

if len(df) > 0:
    first_close = df['Close'].iloc[0]
    last_close = df['Close'].iloc[-1]
    change_val = last_close - first_close
    change_pct = (change_val / first_close) * 100 if first_close != 0 else 0
    
    max_price = df['High'].max()
    min_price = df['Low'].min()
    avg_vol = df['Volume'].mean()
    volatility = df['Daily_Return'].std()

    # 동적 주가 진단 메시지 생성 (초보자를 위한 직관적 해석)
    last_sma20 = df['SMA_20'].iloc[-1] if pd.notna(df['SMA_20'].iloc[-1]) else last_close
    last_upper = df['Upper_Band'].iloc[-1] if pd.notna(df['Upper_Band'].iloc[-1]) else last_close
    last_lower = df['Lower_Band'].iloc[-1] if pd.notna(df['Lower_Band'].iloc[-1]) else last_close
    
    if last_close > last_upper:
        status_icon = "🟠"
        status_title = "단기 과매수(고점) 위험 구간 감지"
        status_desc = f"현재 주가(<b>{last_close:,.0f}원</b>)가 적정 가격 범위 상한선({last_upper:,.0f}원)을 상회하고 있습니다. 단기 조정(과열 식힘) 가능성에 유의하세요."
    elif last_close < last_lower:
        status_icon = "🔵"
        status_title = "단기 과매도(저점) 반등 기대 구간 감지"
        status_desc = f"현재 주가(<b>{last_close:,.0f}원</b>)가 적정 가격 범위 하한선({last_lower:,.0f}원) 아래로 과도하게 낮아졌습니다. 저가 매수세에 의한 기술적 반등 가능성이 높습니다."
    elif last_close > last_sma20:
        status_icon = "🟢"
        status_title = "단기 우상향 상승 흐름 유지 중"
        status_desc = f"현재 주가(<b>{last_close:,.0f}원</b>)가 한 달 평균선({last_sma20:,.0f}원) 위에 위치하여 긍정적인 단기 상승 세력을 유지하고 있습니다."
    else:
        status_icon = "🟡"
        status_title = "단기 조정 및 관망 구간"
        status_desc = f"현재 주가(<b>{last_close:,.0f}원</b>)가 한 달 평균선({last_sma20:,.0f}원) 밑에 위치하고 있어 신중한 접근이 필요한 횡보/조정 구간입니다."

    st.markdown(f"""
    <div class="signal-banner">
        <div class="signal-title">{status_icon} AI 주가 종합 현황: {status_title}</div>
        <div class="signal-desc">{status_desc}</div>
    </div>
    """, unsafe_allow_html=True)

    # Key Metrics Cards (5 columns)
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="📌 최근 종가",
            value=f"{last_close:,.0f} 원",
            delta=f"{change_pct:+.2f}% (기간 대비)",
            delta_color="normal"
        )
    with col2:
        st.metric(
            label="🔺 기간 최고가",
            value=f"{max_price:,.0f} 원"
        )
    with col3:
        st.metric(
            label="🔻 기간 최저가",
            value=f"{min_price:,.0f} 원"
        )
    with col4:
        st.metric(
            label="📊 일평균 거래량",
            value=f"{avg_vol/1e6:.2f} 백만주"
        )
    with col5:
        st.metric(
            label="⚡ 일일 변동성 (위험도)",
            value=f"{volatility:.2f}%" if pd.notna(volatility) else "N/A",
            help="하루 동안 주가가 변하는 평균적인 등락 폭입니다. 높을수록 위험성이 큽니다."
        )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 탭 구성 (직관적인 이름과 수식어 부여)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 [1] 주가 차트 & 매매 신호",
    "📊 [2] 월별/요일별 수익률 패턴",
    "🔍 [3] 주가 흐름 3단계 쪼개기",
    "🔮 [4] 미래 30일 예측 시뮬레이션",
    "📋 [5] 전체 주가 데이터 표"
])

# ------------------------------------------
# Tab 1: 주가 차트 & 매매 신호
# ------------------------------------------
with tab1:
    st.subheader("📈 인터랙티브 주가 추이 및 평균선 분석")

    # 초보자를 위한 쉽게 보기 상자
    st.markdown("""
    <div class="easy-guide-box">
        <div class="easy-guide-title">💡 이 차트를 읽는 3가지 꿀팁</div>
        <div style="font-size: 0.9rem; color: #475569; line-height: 1.6;">
            1. <b>파란선(주가)</b>이 <b>초록선(20일 평균선)</b> 위에 있으면 주가가 상승세입니다.<br>
            2. <b>회색 음영 영역(볼린저 밴드)</b> 바닥에 주가가 닿을 때 사면 며칠 뒤 반등할 확률이 높습니다.<br>
            3. 하단의 <b>거래량 바 차트</b>가 평소보다 길게 솟구치면 큰 뉴스나 기관/외국인의 대량 매매가 발생한 날입니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if len(df) == 0:
        st.warning("선택한 날짜 범위에 데이터가 없습니다.")
    else:
        # Subplots 생성 (주가 + 거래량)
        if show_volume:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.75, 0.25])
        else:
            fig = make_subplots(rows=1, cols=1)

        # 메인 주가 차트
        if chart_type == "캔들스틱 (전문가 보기)":
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="주가 (시가/고가/저가/종가)",
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
                    name="주가 (종가)",
                    line=dict(color='#2563EB', width=2.5)
                ),
                row=1, col=1
            )

        # 이동평균선 오버레이
        ma_mapping = {
            'SMA 10일 (단기)': ('SMA_10', '#F59E0B', 'dash'),
            'SMA 20일 (한 달)': ('SMA_20', '#10B981', 'solid'),
            'SMA 50일 (분기)': ('SMA_50', '#8B5CF6', 'dashdot'),
            'SMA 120일 (반년)': ('SMA_120', '#EC4899', 'longdash'),
            'EMA 20일 (지수평균)': ('EMA_20', '#06B6D4', 'dot')
        }

        for ma_label in selected_mas:
            if ma_label in ma_mapping:
                col_name, color_code, dash_style = ma_mapping[ma_label]
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df[col_name],
                        mode='lines',
                        name=ma_label,
                        line=dict(color=color_code, width=1.8, dash=dash_style)
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
                    name="적정 범위 상한선 (고점 영역)",
                    line=dict(color='rgba(148, 163, 184, 0.6)', width=1.2, dash='dot')
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Lower_Band'],
                    mode='lines',
                    name="적정 범위 하한선 (저점 영역)",
                    line=dict(color='rgba(148, 163, 184, 0.6)', width=1.2, dash='dot'),
                    fill='tonexty',
                    fillcolor='rgba(148, 163, 184, 0.12)'
                ),
                row=1, col=1
            )

        # 최고가 / 최저가 주석 강조
        max_idx = df['High'].idxmax()
        min_idx = df['Low'].idxmin()
        
        fig.add_annotation(
            x=df['Date'].iloc[max_idx], y=df['High'].iloc[max_idx],
            text=f"최고가: {df['High'].iloc[max_idx]:,.0f}원",
            showarrow=True, arrowhead=2, ax=0, ay=-30,
            bgcolor="#FEF3C7", bordercolor="#F59E0B", font=dict(size=11, color="#B45309"), row=1, col=1
        )
        
        fig.add_annotation(
            x=df['Date'].iloc[min_idx], y=df['Low'].iloc[min_idx],
            text=f"최저가: {df['Low'].iloc[min_idx]:,.0f}원",
            showarrow=True, arrowhead=2, ax=0, ay=30,
            bgcolor="#DBEAFE", bordercolor="#3B82F6", font=dict(size=11, color="#1E40AF"), row=1, col=1
        )

        # 하단 거래량 차트
        if show_volume:
            colors = ['#22C55E' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#EF4444' for i in range(len(df))]
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['Volume'],
                    name="하루 거래량 (주)",
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

        fig.update_yaxes(title_text="주가 (원)", row=1, col=1)
        if show_volume:
            fig.update_yaxes(title_text="거래량 (주)", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# Tab 2: 월별/요일별 수익률 패턴
# ------------------------------------------
with tab2:
    st.subheader("📊 어느 달, 무슨 요일에 주가가 많이 움직일까?")
    
    st.markdown("""
    <div class="easy-guide-box">
        <div class="easy-guide-title">💡 계절 및 요일 패턴 인사이트</div>
        <div style="font-size: 0.9rem; color: #475569; line-height: 1.6;">
            - <b>월별 수익률</b>: 빨간색 바는 주가가 떨어진 달, 파란색 바는 주가가 오른 달입니다.<br>
            - <b>요일별 변동성</b>: 주말(토/일) 사이 발생하는 미국 증시 뉴스와 글로벌 이슈 때문에 보통 <b>월요일과 금요일</b>의 변동성이 큽니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

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
        fig_m.update_layout(height=380, template="plotly_white", coloraxis_showscale=False)
        st.plotly_chart(fig_m, use_container_width=True)

    with r_col2:
        st.markdown("#### 🗓️ 요일별 평균 주가 흔들림 (변동성 %)")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        day_kr = {'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일', 'Thursday': '목요일', 'Friday': '금요일'}
        
        day_stats = df.groupby('DayOfWeek')['Daily_Return'].agg(['mean', 'std']).reindex(day_order).reset_index()
        day_stats['Day_KR'] = day_stats['DayOfWeek'].map(day_kr)
        day_stats['std'] = day_stats['std'].fillna(0)

        fig_d = px.bar(
            day_stats,
            x='Day_KR',
            y='std',
            text=day_stats['std'].apply(lambda x: f"{x:.2f}%"),
            labels={'Day_KR': '요일', 'std': '변동성 (표준편차 %)'},
            color_discrete_sequence=['#8B5CF6']
        )
        fig_d.update_layout(height=380, template="plotly_white")
        st.plotly_chart(fig_d, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📉 하루 주가 상승/하락 폭 분포 (히스토그램)")
    
    valid_returns = df.dropna(subset=['Daily_Return'])
    if len(valid_returns) > 0:
        fig_hist = px.histogram(
            valid_returns,
            x='Daily_Return',
            nbins=40,
            marginal='box',
            labels={'Daily_Return': '일일 수익률 (%)'},
            color_discrete_sequence=['#3B82F6']
        )
        fig_hist.update_layout(height=360, template="plotly_white")
        st.plotly_chart(fig_hist, use_container_width=True)

# ------------------------------------------
# Tab 3: 주가 흐름 3단계 쪼개기
# ------------------------------------------
with tab3:
    st.subheader("🔍 실제 주가를 '진짜 추세 + 반복 파동 + 돌발 소음'으로 분해하기")
    
    st.markdown("""
    <div class="easy-guide-box">
        <div class="easy-guide-title">💡 주가 분해란 무엇인가요?</div>
        <div style="font-size: 0.9rem; color: #475569; line-height: 1.6;">
            주가는 매일 어지럽게 흔들리지만, 그 내부에는 3가지 성분이 섞여 있습니다.<br>
            1. 📈 <b>추세 (Trend)</b>: 일시적 등락을 제거한 주가의 진짜 장기 방향성<br>
            2. 🔄 <b>계절성 (Seasonal)</b>: 약 1달(20일) 주기로 반복해서 일어나는 순환 파동<br>
            3. ⚡ <b>잔차 / 노이즈 (Residual)</b>: 실적 발표, 뉴스 등 예상치 못한 돌발 변수로 인해 튄 구간
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    decomp_period = st.radio("분해 기준 주기 선택", options=[5, 10, 20, 30], index=2, horizontal=True, help="20일은 보통 1개월 영업일 주기를 의미합니다.")

    ts_df = df.set_index('Date')['Close'].dropna()

    if len(ts_df) < decomp_period * 2:
        st.error(f"성분 분해를 수행하기에 선택한 기간의 데이터 포인트가 부족합니다. 최소 {decomp_period * 2}일 이상을 지정해주세요.")
    else:
        try:
            decomposition = seasonal_decompose(ts_df, model='additive', period=decomp_period)

            fig_decomp = make_subplots(
                rows=4, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.06,
                subplot_titles=(
                    "1. 실제 관측 주가 (Observed)",
                    "2. 📈 진짜 추세 성분 (Trend - 잡음 제거)",
                    "3. 🔄 주기적 순환 파동 (Seasonal)",
                    "4. ⚡ 돌발 소음 / 잔차 (Residual)"
                )
            )

            fig_decomp.add_trace(go.Scatter(x=ts_df.index, y=decomposition.observed, mode='lines', line=dict(color='#2563EB', width=1.5)), row=1, col=1)
            fig_decomp.add_trace(go.Scatter(x=ts_df.index, y=decomposition.trend, mode='lines', line=dict(color='#F59E0B', width=2.0)), row=2, col=1)
            fig_decomp.add_trace(go.Scatter(x=ts_df.index, y=decomposition.seasonal, mode='lines', line=dict(color='#10B981', width=1.5)), row=3, col=1)
            fig_decomp.add_trace(go.Scatter(x=ts_df.index, y=decomposition.resid, mode='markers', marker=dict(size=4, color='#EF4444')), row=4, col=1)

            fig_decomp.update_layout(height=720, template="plotly_white", showlegend=False)
            st.plotly_chart(fig_decomp, use_container_width=True)

        except Exception as err:
            st.error(f"시계열 분해 처리 중 오류가 발생했습니다: {err}")

# ------------------------------------------
# Tab 4: 30일 예측 시뮬레이션
# ------------------------------------------
with tab4:
    st.subheader("🔮 향후 30 영업일 주가 추세 베이스라인 예측")
    
    st.markdown("""
    <div class="easy-guide-box">
        <div class="easy-guide-title">💡 예측 차트 쉽게 이해하기</div>
        <div style="font-size: 0.9rem; color: #475569; line-height: 1.6;">
            - <b>점선 분홍선</b>: 최근 주가 기울기를 바탕으로 계산된 미래 예상 주가입니다.<br>
            - <b>분홍색 연한 띠</b>: 95% 신뢰 구간입니다. 특별한 악재나 호재가 없다면 주가가 이 띠 범위 안에 머물 가능성이 높습니다.<br>
            - 사이드바의 <b>[추세 가중치]</b> 슬라이더를 조절하여 상방/하방 가상 시나리오를 자유롭게 테스트해보세요!
        </div>
    </div>
    """, unsafe_allow_html=True)

    if len(df) < trend_window:
        st.error(f"예측을 위해 최소 {trend_window}일 이상의 과거 데이터가 필요합니다.")
    else:
        method_code = 'linear' if '선형' in forecast_method else 'ma'
        forecast_df = simple_baseline_forecast(
            df, 
            forecast_days=forecast_days, 
            trend_window=trend_window, 
            method=method_code, 
            trend_bias=trend_bias
        )
        
        last_date = df['Date'].max()
        last_close = df['Close'].iloc[-1]
        
        fc_end_price = forecast_df['Forecast_Close'].iloc[-1]
        fc_change_pct = ((fc_end_price - last_close) / last_close) * 100
        adjusted_slope = (fc_end_price - last_close) / forecast_days
        slope_pct = (adjusted_slope / last_close) * 100

        # 추세 상태 진단
        if adjusted_slope > last_close * 0.0005:
            trend_status = "📈 우상향 (상승 추세)"
            trend_color = "🟢"
        elif adjusted_slope < -last_close * 0.0005:
            trend_status = "📉 우하향 (하락 추세)"
            trend_color = "🔴"
        else:
            trend_status = "➡️ 횡보 (보합 추세)"
            trend_color = "🟡"

        # 요약 예측 메트릭 (4개 컬럼)
        fc_col1, fc_col2, fc_col3, fc_col4 = st.columns(4)
        with fc_col1:
            st.metric("🎯 30일 뒤 예상 주가", f"{fc_end_price:,.0f} 원", delta=f"{fc_change_pct:+.2f}%")
        with fc_col2:
            st.metric("📐 일일 추세 기울기", f"{adjusted_slope:+.1f} 원/일", delta=f"{slope_pct:+.2f}%/일")
        with fc_col3:
            st.metric("📈 예상 최고 한계선", f"{forecast_df['Upper_Bound'].iloc[-1]:,.0f} 원")
        with fc_col4:
            st.metric("📉 예상 최저 지지선", f"{forecast_df['Lower_Bound'].iloc[-1]:,.0f} 원")

        st.info(f"{trend_color} **산출 추세 방향성**: {trend_status} | 적용 알고리즘: **{forecast_method}** (과거 {trend_window}일 모멘텀 수집)")

        st.markdown("<br>", unsafe_allow_html=True)

        # 최근 90일 히스토리 시각화
        recent_history = df.tail(90)
        fig_fc = go.Figure()

        fig_fc.add_trace(go.Scatter(
            x=recent_history['Date'],
            y=recent_history['Close'],
            mode='lines',
            name="실제 주가 (Recent Close)",
            line=dict(color='#2563EB', width=2.5)
        ))

        fig_fc.add_trace(go.Scatter(
            x=pd.to_datetime(forecast_df['Date']),
            y=forecast_df['Forecast_Close'],
            mode='lines+markers',
            name=f"향후 {forecast_days}일 예측 추세선",
            line=dict(color='#EC4899', width=2.5, dash='dash')
        ))

        fig_fc.add_trace(go.Scatter(
            x=pd.to_datetime(forecast_df['Date']),
            y=forecast_df['Upper_Bound'],
            mode='lines',
            name="예상 범위 상한 (+95%)",
            line=dict(color='rgba(236, 72, 153, 0.3)', width=1, dash='dot')
        ))

        fig_fc.add_trace(go.Scatter(
            x=pd.to_datetime(forecast_df['Date']),
            y=forecast_df['Lower_Bound'],
            mode='lines',
            name="예상 범위 하한 (-95%)",
            line=dict(color='rgba(236, 72, 153, 0.3)', width=1, dash='dot'),
            fill='tonexty',
            fillcolor='rgba(236, 72, 153, 0.1)'
        ))

        # Y축 자동 범위 조율 (최근 90일 및 예측 구간 포커스)
        vis_prices = list(recent_history['Close']) + list(forecast_df['Forecast_Close']) + list(forecast_df['Upper_Bound']) + list(forecast_df['Lower_Bound'])
        min_p = min(vis_prices)
        max_p = max(vis_prices)
        p_margin = (max_p - min_p) * 0.1 if max_p != min_p else min_p * 0.05

        fig_fc.update_layout(
            height=500,
            title=f"삼성전자 향후 {forecast_days} 영업일 주가 예측 (일일 추세 기울기: {adjusted_slope:+.1f} 원/일)",
            xaxis_title="날짜 (Date)",
            yaxis_title="주가 (원)",
            yaxis=dict(range=[min_p - p_margin, max_p + p_margin]),
            template="plotly_white",
            hovermode="x unified"
        )

        st.plotly_chart(fig_fc, use_container_width=True)

        # 예측 결과 CSV 다운로드
        csv_forecast = forecast_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 30일 예측 결과 데이터 다운로드 (CSV)",
            data=csv_forecast,
            file_name="samsung_stock_30d_forecast_simulation.csv",
            mime="text/csv"
        )

# ------------------------------------------
# Tab 5: 전체 주가 데이터 표
# ------------------------------------------
with tab5:
    st.subheader("📋 선택 기간 일별 원본 주가 데이터")
    
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        st.markdown("##### 🔍 상세 데이터 테이블")
        disp_df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'SMA_20', 'SMA_50', 'Daily_Return']].copy()
        disp_df['Date'] = disp_df['Date'].dt.strftime('%Y-%m-%d')
        
        # 한국어 컬럼명으로 직관적 변경
        disp_df.columns = ['날짜', '시가(원)', '고가(원)', '저가(원)', '종가(원)', '거래량(주)', '20일평균', '50일평균', '수익률(%)']
        
        st.dataframe(
            disp_df.style.format({
                '시가(원)': '{:,.0f}',
                '고가(원)': '{:,.0f}',
                '저가(원)': '{:,.0f}',
                '종가(원)': '{:,.0f}',
                '거래량(주)': '{:,.0f}',
                '20일평균': '{:,.1f}',
                '50일평균': '{:,.1f}',
                '수익률(%)': '{:+.2f}%'
            }, na_rep='-'),
            use_container_width=True,
            height=450
        )
    with col_d2:
        st.markdown("##### 📊 주요 지표 수치 요약")
        desc_df = df[['Close', 'Volume', 'Daily_Return']].describe()
        desc_df.columns = ['종가(원)', '거래량(주)', '수익률(%)']
        desc_df.index = ['개수', '평균', '표준편차', '최소값', '25%', '50%', '75%', '최대값']
        st.dataframe(
            desc_df.style.format('{:,.2f}', na_rep='-'),
            use_container_width=True
        )

    # 필터링 데이터 CSV 다운로드
    csv_filtered = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 현재 필터링된 주가 데이터 전체 CSV 다운로드",
        data=csv_filtered,
        file_name=f"samsung_stock_{start_date}_{end_date}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("© 2026 Samsung Stock Time Series Analytics Dashboard | User-Friendly UX Edition")
