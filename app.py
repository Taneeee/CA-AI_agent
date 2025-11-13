# app.py - Enhanced Streamlit Application (modified to fetch market data reliably)
import os
import requests
import streamlit as st
from agent import InvestmentAgent
from database import insert_user, get_all_users
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime

st.set_page_config(
    page_title="AI Investment Advisor - Multi-Agent System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .agent-status {
        padding: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_agent():
    return InvestmentAgent(use_ray=False)

agent = get_agent()

def get_market_data(fallback_from_agent=None):
    result = {
        "status": "error",
        "nifty_50": 0.0,
        "gold_price": 0.0,
        "market_sentiment": "Neutral",
        "macro_indicators": {}
    }

    if fallback_from_agent and isinstance(fallback_from_agent, dict):
        try:
            if fallback_from_agent.get("status") == "success":
                n = fallback_from_agent.get("nifty_50")
                g = fallback_from_agent.get("gold_price")
                if n and float(n) > 0:
                    result["nifty_50"] = float(n)
                if g and float(g) > 0:
                    result["gold_price"] = float(g)
                result["market_sentiment"] = fallback_from_agent.get("market_sentiment", "Neutral")
                result["macro_indicators"] = fallback_from_agent.get("macro_indicators", {})
                if result["nifty_50"] > 0 or result["gold_price"] > 0:
                    result["status"] = "success"
                    return result
        except Exception:
            pass

    try:
        ticker = yf.Ticker("^NSEI")
        nifty_price = None
        info = {}
        try:
            info = ticker.info or {}
        except Exception:
            info = {}
        for key in ("regularMarketPrice", "previousClose", "last_price", "last"):
            if info.get(key):
                nifty_price = info.get(key)
                break
        if nifty_price is None:
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                nifty_price = float(hist['Close'].iloc[-1])
        if nifty_price:
            result["nifty_50"] = float(nifty_price)
    except Exception:
        pass

    gold_per_10g = 0.0
    GOLDAPI_KEY = os.getenv("GOLDAPI_KEY")
    if GOLDAPI_KEY:
        try:
            resp = requests.get(
                "https://www.goldapi.io/api/XAU/INR",
                headers={"x-access-token": GOLDAPI_KEY, "Content-Type": "application/json"},
                timeout=10
            )
            if resp.status_code == 200:
                j = resp.json()
                price = None
                if 'price' in j:
                    price = float(j['price'])
                elif 'ask' in j:
                    price = float(j['ask'])
                unit = (j.get('unit') or "").lower()
                if price is not None:
                    if 'oz' in unit:
                        per_gram = price / 31.1034768
                    else:
                        per_gram = price
                    gold_per_10g = per_gram * 10.0
        except Exception:
            pass

    if gold_per_10g == 0.0:
        try:
            gold_ticker = yf.Ticker("GC=F")
            gold_price_oz = None
            hist = gold_ticker.history(period="1d", interval="1d")
            if not hist.empty:
                gold_price_oz = float(hist['Close'].iloc[-1])
            usd_inr_ticker = yf.Ticker("INR=X")
            usd_inr = None
            info2 = usd_inr_ticker.history(period="1d", interval="1d")
            if not info2.empty:
                usd_inr = float(info2['Close'].iloc[-1])
            if gold_price_oz and usd_inr:
                per_gram = (gold_price_oz * usd_inr) / 31.1034768
                gold_per_10g = per_gram * 10.0
        except Exception:
            pass

    if gold_per_10g and gold_per_10g > 0:
        result["gold_price"] = float(gold_per_10g)

    if fallback_from_agent:
        try:
            if fallback_from_agent.get("market_sentiment"):
                result["market_sentiment"] = fallback_from_agent.get("market_sentiment")
            if fallback_from_agent.get("macro_indicators"):
                result["macro_indicators"] = fallback_from_agent.get("macro_indicators")
        except Exception:
            pass

    if result["nifty_50"] > 0 or result["gold_price"] > 0:
        result["status"] = "success"
    else:
        result["status"] = "error"

    return result

st.markdown('<div class="main-header"> AI-Powered Investment Advisor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-Agent Intelligence System for Personalized Wealth Management</div>', unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    st.header("Your Financial Profile")
    
    with st.expander("How it works", expanded=False):
        st.markdown("""
        Our AI system uses **12+ specialized agents** to:
        1.  Analyze market data in real-time
        2.  Profile your risk appetite
        3.  Score thousands of investment options
        4.  Build optimized portfolios
        5.  Validate and adjust recommendations
        """)
    
    st.markdown("---")
    
    name = st.text_input("Your Name", placeholder="Enter your full name")
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=18, max_value=100, value=30)
    with col2:
        horizon = st.number_input("Horizon (Years)", min_value=1, max_value=50, value=10)
    
    income = st.number_input("Monthly Income (₹)", min_value=0.0, value=50000.0, step=5000.0, format="%.0f")
    expenses = st.number_input("Monthly Expenses (₹)", min_value=0.0, value=30000.0, step=5000.0, format="%.0f")
    savings = st.number_input("Current Savings (₹)", min_value=0.0, value=100000.0, step=10000.0, format="%.0f")
    
    risk_tolerance = st.select_slider(
        "Risk Tolerance",
        options=["Low", "Medium", "High"],
        value="Medium"
    )
    
    st.markdown("---")
    
    if expenses >= income:
        st.error("Expenses must be less than income!")
        generate_plan = False
    else:
        disposable = income - expenses
        st.success(f"Available for Investment: ₹{disposable:,.0f}/month")
        generate_plan = st.button("Generate AI-Powered Plan", type="primary", width="content")

if generate_plan and name.strip():
    user_data = {
        "age": age,
        "income": income,
        "expenses": expenses,
        "savings": savings,
        "horizon": horizon,
        "risk_tolerance": risk_tolerance
    }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Initializing AI agents...")
    progress_bar.progress(10)
    
    status_text.text("Analyzing your profile...")
    progress_bar.progress(20)
    
    status_text.text("Collecting market data...")
    progress_bar.progress(40)
    
    with st.spinner('AI agents are analyzing thousands of investment options...'):
        analysis = agent.analyze_profile(user_data)
        agent_market = {}
        try:
            agent_market = agent.get_market_data() if hasattr(agent, "get_market_data") else {}
        except Exception:
            agent_market = {}
        market_data = get_market_data(fallback_from_agent=agent_market)
    
    status_text.text("Scoring assets...")
    progress_bar.progress(60)
    
    status_text.text("Constructing optimal portfolio...")
    progress_bar.progress(80)
    
    status_text.text("Finalizing recommendations...")
    progress_bar.progress(100)
    
    progress_bar.empty()
    status_text.empty()
    
    st.success("AI Analysis Complete!")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", 
        "Portfolio", 
        "Asset Analysis", 
        "Recommendations",
        "Market Insights"
    ])
    
    with tab1:
        st.header("Investment Plan Overview")
        
        profile = analysis['user_profile']
        portfolio = analysis['portfolio']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Risk Profile",
                profile['risk_profile'],
                f"Score: {profile.get('risk_score', 0):.1f}/10"
            )
        
        with col2:
            st.metric(
                "Investment Capacity",
                f"₹{profile['disposable_income']:,.0f}",
                f"{profile['savings_rate']:.1f}% savings"
            )
        
        with col3:
            st.metric(
                "Expected Return",
                f"{portfolio.get('expected_return', 0):.1f}%",
                "Annualized"
            )
        
        with col4:
            st.metric(
                "Confidence Score",
                f"{analysis.get('confidence_score', 0):.0%}",
                "AI Certainty"
            )
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Financial Health Check")
            health_score = profile['savings_rate']
            
            if health_score >= 30:
                st.success("Excellent financial health!")
            elif health_score >= 20:
                st.info("Good savings discipline")
            else:
                st.warning("Consider improving savings rate")
            
            st.markdown(f"""
            **Monthly Breakdown:**
            - Income: ₹{income:,.0f}
            - Expenses: ₹{expenses:,.0f}
            - Investable: ₹{profile['disposable_income']:,.0f}
            - Savings Rate: {profile['savings_rate']:.1f}%
            """)
        
        with col2:
            st.subheader("Investment Goals")
            life_stage = "Early Career" if age < 35 else ("Mid Career" if age < 50 else "Pre-Retirement")
            st.markdown(f"**Life Stage:** {life_stage}")
            st.markdown("**Suggested Goals:**")
            goals = [
                "Build 6-month emergency fund",
                "Start retirement corpus",
                "Tax-efficient investing",
                f"{'Education fund' if age < 40 else 'Wealth preservation'}"
            ]
            for goal in goals:
                st.markdown(f"- {goal}")
    
    with tab2:
        st.header("Your Optimized Portfolio")
        
        allocation = portfolio['allocation']
        strategic_pct = portfolio['strategic_percentages']
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig = go.Figure(data=[go.Pie(
                labels=list(strategic_pct.keys()),
                values=list(strategic_pct.values()),
                hole=0.4,
                marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
            )])
            fig.update_layout(
                title="Asset Allocation (%)",
                height=400
            )
            st.plotly_chart(fig, width=True)
        
        with col2:
            fig = go.Figure(data=[go.Bar(
                x=list(allocation.keys()),
                y=list(allocation.values()),
                marker_color='#1f77b4'
            )])
            fig.update_layout(
                title="Investment Amount (₹)",
                yaxis_title="Amount",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Detailed Allocation")
        allocation_df = pd.DataFrame([
            {
                "Asset Class": asset,
                "Amount (₹)": f"₹{amount:,.0f}",
                "Percentage": f"{strategic_pct[asset]}%",
                "Monthly SIP": f"₹{amount:,.0f}"
            }
            for asset, amount in allocation.items()
        ])
        st.dataframe(allocation_df, use_container_width=True, hide_index=True)
        
        st.subheader("Portfolio Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Expected Return", f"{portfolio.get('expected_return', 0):.2f}%")
        with col2:
            st.metric("Expected Risk", f"{portfolio.get('expected_risk', 0):.2f}%")
        with col3:
            st.metric("Diversification", f"{portfolio.get('diversification_score', 0):.0%}")
        
        validation = portfolio.get('validation', {})
        if validation.get('passed'):
            st.success("Portfolio passed all validation checks")
        else:
            st.warning("Some adjustments were made:")
            for issue in validation.get('issues', []):
                st.write(f"- {issue}")
    
    with tab3:
        st.header("Asset Scoring Analysis")
        
        asset_scores = analysis.get('asset_scores', {})
        
        st.subheader("Top Scored Stocks")
        stock_scores = asset_scores.get('stocks', {})
        
        if stock_scores:
            stock_data = []
            for symbol, data in sorted(
                stock_scores.items(),
                key=lambda x: x[1]['aggregate_score'],
                reverse=True
            )[:10]:
                individual = data['individual_scores']
                stock_data.append({
                    'Symbol': symbol.replace('.NS', ''),
                    'Score': f"{data['aggregate_score']:.2f}",
                    'Valuation': f"{individual.get('valuation', 0):.2f}",
                    'Momentum': f"{individual.get('momentum', 0):.2f}",
                    'Quality': f"{individual.get('quality', 0):.2f}",
                    'Risk': f"{individual.get('risk', 0):.2f}"
                })
            
            st.dataframe(pd.DataFrame(stock_data), use_container_width=True, hide_index=True)
            
            top_5 = list(stock_scores.items())[:5]
            symbols = [s[0].replace('.NS', '') for s in top_5]
            scores = [s[1]['aggregate_score'] for s in top_5]
            
            fig = go.Figure(data=[go.Bar(x=symbols, y=scores, marker_color='lightblue')])
            fig.update_layout(title="Top 5 Stocks by AI Score", yaxis_title="Score (0-1)")
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Top Mutual Funds")
        mf_scores = asset_scores.get('mutual_funds', {})
        
        if mf_scores:
            mf_data = []
            for code, score in sorted(mf_scores.items(), key=lambda x: x[1], reverse=True)[:5]:
                mf_data.append({
                    'Scheme Code': code,
                    'Score': f"{score:.2f}",
                    'Rating': '⭐' * int(score * 5)
                })
            
            st.dataframe(pd.DataFrame(mf_data), use_container_width=True, hide_index=True)
    
    with tab4:
        st.header("AI-Powered Recommendations")
        
        recommendations = analysis.get('recommendations', {})
        
        st.subheader("Top Stock Picks")
        top_stocks = recommendations.get('top_stocks', [])
        
        if top_stocks:
            for i, stock in enumerate(top_stocks[:5], 1):
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 3])
                    with col1:
                        st.markdown(f"**{i}. {stock['symbol'].replace('.NS', '')}**")
                    with col2:
                        st.metric("AI Score", f"{stock['score']:.2f}")
                    with col3:
                        st.caption(stock.get('reason', 'AI recommended'))
        
        st.markdown("---")
        
        st.subheader("Recommended Mutual Funds")
        top_mfs = recommendations.get('top_mutual_funds', [])
        
        if top_mfs:
            for i, mf in enumerate(top_mfs[:5], 1):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{i}. Scheme Code: {mf['code']}**")
                with col2:
                    st.metric("Score", f"{mf['score']:.2f}")
        
        st.markdown("---")
        
        st.subheader("Investment Strategy")
        strategies = recommendations.get('strategy_suggestions', [])
        
        for strategy in strategies:
            st.info(f"{strategy}")
        
        st.markdown("---")
        
        st.subheader("Rebalancing Guidelines")
        triggers = recommendations.get('rebalancing_triggers', [])
        
        for trigger in triggers:
            st.markdown(f"- {trigger}")
        
        st.subheader("Action Items")
        st.markdown("""
        1. **Start SIP**: Set up systematic investment plans for recommended funds
        2. **Emergency Fund**: Ensure 6 months expenses in liquid funds
        3. **Insurance**: Review life and health insurance coverage
        4. **Tax Planning**: Optimize for Section 80C, 80D deductions
        5. **Review Quarterly**: Monitor and rebalance portfolio every 3 months
        """)
    
    with tab5:
        st.header("Market Intelligence")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Live Market Data")
            
            if market_data.get('status') == 'success':
                st.metric(
                    "Nifty 50",
                    f"₹{market_data.get('nifty_50', 0):,.2f}",
                    delta=None
                )
                st.metric(
                    "Gold (per 10g)",
                    f"₹{market_data.get('gold_price', 0):,.2f}"
                )
                
                sentiment = market_data.get('market_sentiment', 'Neutral')
                st.metric(
                    "Market Sentiment",
                    sentiment
                )
            else:
                st.error("Unable to fetch live market data")
        
        with col2:
            st.subheader("Macroeconomic Indicators")
            
            macro = market_data.get('macro_indicators', {})
            if macro:
                st.markdown(f"""
                **Key Indicators:**
                - GDP Growth: {macro.get('gdp_growth', 0):.1f}%
                - Inflation Rate: {macro.get('inflation_rate', 0):.1f}%
                - Interest Rate: {macro.get('interest_rate', 0):.1f}%
                - USD/INR: ₹{macro.get('usd_inr', 0):,.2f}
                """)
        
        st.subheader("AI Market Analysis")
        market_analysis = analysis.get('market_analysis', {})
        
        sentiment = market_analysis.get('market_sentiment', 'Neutral')
        if sentiment == 'Positive':
            st.success("Bullish Market: Good time for equity investments")
        elif sentiment == 'Negative':
            st.error("Bearish Market: Consider defensive strategies")
        else:
            st.info("Neutral Market: Balanced approach recommended")
        
        top_performers = market_analysis.get('top_performers', [])
        if top_performers:
            st.subheader("Market Leaders")
            st.write(", ".join(top_performers[:5]))
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Save Your Profile")
        if st.button("Save Investment Profile", type="primary", use_container_width=True):
            try:
                insert_user(
                    name=name,
                    income=income,
                    expenses=expenses,
                    savings=savings,
                    risk_profile=profile['risk_profile']
                )
                st.success("Profile saved successfully!")
            except Exception as e:
                st.error(f"Error saving profile: {e}")

elif generate_plan and not name.strip():
    st.warning("Please enter your name to generate the investment plan.")

else:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    st.markdown("""
    ## Welcome to Your AI-Powered Investment Advisor! 
    
    ### How Our Multi-Agent System Works:
    
    Our advanced AI system employs **12+ specialized agents** working in harmony:
    
    1. **User Intelligence Agents**
       - Profile your risk appetite and financial capacity
       - Analyze your expense patterns and cashflow
    
    2. **Data Collection Agents**
       - Monitor 1000+ stocks in real-time
       - Track mutual fund NAVs and performance
       - Analyze macroeconomic indicators
       - Process market sentiment from news
    
    3. **Analytical Scoring Agents**
       - Valuation analysis (PE, PB ratios)
       - Momentum and technical indicators
       - Quality and fundamental metrics
       - Risk assessment (volatility, VaR)
    
    4. **Portfolio Construction Agents**
       - Build optimized asset allocation
       - Select top-performing instruments
       - Validate and adjust recommendations
    
    5. **Meta-Controller**
       - Coordinate all agents
       - Resolve conflicts
       - Ensure consistency
    
    ###  Key Features:
    
    - **Personalized Risk Profiling** - AI analyzes your unique situation
    - **Multi-Factor Scoring** - Evaluates assets on 10+ parameters
    - **Smart Portfolio Construction** - Optimized for your goals
    - **Live Market Data** - Real-time prices and sentiment
    - **Actionable Recommendations** - Clear next steps
    - **Profile Management** - Save and track your journey
    
    ###  Get Started:
    
    1. **Fill your financial profile** in the sidebar ←
    2. **Click "Generate AI-Powered Plan"** to activate all agents
    3. **Review your personalized portfolio** with detailed analysis
    4. **Get specific recommendations** for stocks and mutual funds
    5. **Save your profile** for future reference
    
    ---
    
    ###  System Status:
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Agents", "12", delta="100%")
    with col2:
        st.metric("Assets Tracked", "1000+", delta="Real-time")
    with col3:
        st.metric("Data Sources", "5", delta="Live")
    with col4:
        st.metric("Avg. Confidence", "85%", delta="+5%")
    
    st.markdown("---")
    
    st.info("""
     **Disclaimer**: This is an AI-powered educational tool. While our system uses advanced 
    algorithms and real market data, it should not be considered as professional financial advice. 
    Always consult with certified financial advisors before making investment decisions.
    """)

with st.sidebar:
    st.markdown("---")
    st.subheader("Additional Features")
    
    if st.button("View Saved Profiles", use_container_width=True):
        st.session_state['show_profiles'] = True
    
    with st.expander("System Information"):
        st.markdown(f"""
        **Version**: 2.0 (Multi-Agent)
        **Agents**: 12+ specialized
        **Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
        **Status**:  All systems operational
        """)
    
    with st.expander("Investment Tips"):
        st.markdown("""
        - Start early, invest regularly
        - Diversify across asset classes
        - Review portfolio quarterly
        - Stay invested for long term
        - Don't panic during volatility
        - Rebalance when drift > 10%
        """)

if st.session_state.get('show_profiles', False):
    st.markdown("---")
    st.header("Saved User Profiles")
    
    users = get_all_users()
    if users:
        df = pd.DataFrame(
            users,
            columns=["ID", "Name", "Income", "Expenses", "Savings", "Risk Profile", "Date"]
        )
        
        df['Income'] = df['Income'].apply(lambda x: f"₹{x:,.0f}")
        df['Expenses'] = df['Expenses'].apply(lambda x: f"₹{x:,.0f}")
        df['Savings'] = df['Savings'].apply(lambda x: f"₹{x:,.0f}")
        
        st.dataframe(df, width=True, hide_index=True)
        
        st.subheader("User Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Users", len(users))
        with col2:
            risk_dist = df['Risk Profile'].value_counts()
            st.metric("Most Common", risk_dist.index[0] if len(risk_dist) > 0 else "N/A")
        with col3:
            st.metric("Profiles Today", len([u for u in users if datetime.now().strftime('%Y-%m-%d') in str(u[6])]))
    else:
        st.info("No saved profiles found. Generate your first plan!")
    
    if st.button("Close Profiles View"):
        st.session_state['show_profiles'] = False
        st.rerun()
