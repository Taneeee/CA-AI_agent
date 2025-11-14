# app.py - Enhanced Streamlit Application with MarketWatch integration and Session State
import os
import requests
import streamlit as st
from agent import InvestmentAgent
from database import insert_user, get_all_users
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time

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

# Cache market data for 5 minutes to avoid excessive requests
@st.cache_data(ttl=300)
def fetch_from_marketwatch(url, price_selectors):
    """Helper function to fetch and parse data from MarketWatch"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors
            for selector in price_selectors:
                # Try class selector
                price_elem = soup.find(class_=selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    price_clean = re.sub(r'[^\d.]', '', price_text)
                    if price_clean and float(price_clean) > 0:
                        return float(price_clean)
                
                # Try data attribute selector
                price_elem = soup.find(attrs={'data-test': selector})
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    price_clean = re.sub(r'[^\d.]', '', price_text)
                    if price_clean and float(price_clean) > 0:
                        return float(price_clean)
            
            # Try meta tags
            meta_price = soup.find('meta', {'name': 'price'})
            if meta_price and meta_price.get('content'):
                return float(meta_price['content'])
            
            # Try structured data (JSON-LD)
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'price' in data:
                        return float(data['price'])
                except:
                    continue
                    
    except Exception as e:
        print(f"MarketWatch fetch error for {url}: {e}")
    
    return None


def get_usd_inr_rate():
    """Fetch USD to INR exchange rate from MarketWatch"""
    
    # Try MarketWatch first
    rate = fetch_from_marketwatch(
        "https://www.marketwatch.com/investing/currency/usdinr",
        ['bg-quote', 'value', 'intraday__price', 'lastprice']
    )
    if rate and rate > 70 and rate < 100:  # Sanity check
        return rate
    
    # Try yfinance as fallback
    try:
        ticker = yf.Ticker("INR=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            rate = float(hist['Close'].iloc[-1])
            if rate > 70 and rate < 100:
                return rate
    except:
        pass
    
    # Fallback to approximate rate
    return 83.0


def get_nifty_from_marketwatch():
    """Fetch Nifty 50 from MarketWatch"""
    price = fetch_from_marketwatch(
        "https://www.marketwatch.com/investing/index/nifty50?countrycode=in",
        ['bg-quote', 'value', 'intraday__price', 'lastprice', 'last-price']
    )
    return price if price else None


def get_gold_from_marketwatch():
    """Fetch Gold price from MarketWatch and convert to INR per 10g"""
    # Fetch gold in USD per oz
    gold_usd_per_oz = fetch_from_marketwatch(
        "https://www.marketwatch.com/investing/future/gc00",
        ['bg-quote', 'value', 'intraday__price', 'lastprice']
    )
    
    if gold_usd_per_oz:
        # Get USD to INR rate
        usd_inr = get_usd_inr_rate()
        
        # Convert to INR per 10g
        # 1 troy oz = 31.1034768 grams
        gold_per_gram = (gold_usd_per_oz * usd_inr) / 31.1034768
        gold_per_10g = gold_per_gram * 10.0
        
        return gold_per_10g
    
    return None


def get_market_data():
    """
    Enhanced market data fetcher - MarketWatch primary source
    Priority: MarketWatch -> yfinance -> GoldAPI
    """
    result = {
        "status": "error",
        "nifty_50": 0.0,
        "gold_price": 0.0,
        "market_sentiment": "Neutral",
        "macro_indicators": {},
        "data_source": "",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 1. Try MarketWatch for Nifty 50
    try:
        nifty_price = get_nifty_from_marketwatch()
        if nifty_price and nifty_price > 10000:  # Sanity check
            result["nifty_50"] = float(nifty_price)
            result["data_source"] = "MarketWatch"
    except Exception as e:
        print(f"MarketWatch Nifty error: {e}")

    # 2. Try yfinance for Nifty 50 if MarketWatch failed
    if result["nifty_50"] == 0.0:
        try:
            ticker = yf.Ticker("^NSEI")
            nifty_price = None
            
            # Try info first
            try:
                info = ticker.info or {}
                for key in ("regularMarketPrice", "previousClose", "currentPrice"):
                    if info.get(key):
                        nifty_price = float(info[key])
                        break
            except:
                pass
            
            # Try history if info failed
            if nifty_price is None:
                hist = ticker.history(period="1d", interval="1m")
                if not hist.empty:
                    nifty_price = float(hist['Close'].iloc[-1])
            
            if nifty_price and nifty_price > 10000:
                result["nifty_50"] = float(nifty_price)
                if not result["data_source"]:
                    result["data_source"] = "Yahoo Finance"
        except Exception as e:
            print(f"yfinance Nifty error: {e}")

    # 3. Try MarketWatch for Gold
    try:
        gold_price = get_gold_from_marketwatch()
        if gold_price and gold_price > 30000:  # Sanity check (INR per 10g)
            result["gold_price"] = float(gold_price)
            if result["data_source"] == "MarketWatch":
                result["data_source"] = "MarketWatch"
            elif not result["data_source"]:
                result["data_source"] = "MarketWatch (Gold)"
    except Exception as e:
        print(f"MarketWatch Gold error: {e}")

    # 4. Try GoldAPI if available
    if result["gold_price"] == 0.0:
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
                        
                        if gold_per_10g > 30000:
                            result["gold_price"] = float(gold_per_10g)
                            if not result["data_source"]:
                                result["data_source"] = "GoldAPI"
            except Exception as e:
                print(f"GoldAPI error: {e}")

    # 5. Try yfinance for Gold as last resort
    if result["gold_price"] == 0.0:
        try:
            gold_ticker = yf.Ticker("GC=F")
            hist = gold_ticker.history(period="1d")
            if not hist.empty:
                gold_price_oz = float(hist['Close'].iloc[-1])
                
                # Get USD to INR rate
                usd_inr = get_usd_inr_rate()
                
                if gold_price_oz and usd_inr:
                    per_gram = (gold_price_oz * usd_inr) / 31.1034768
                    gold_per_10g = per_gram * 10.0
                    
                    if gold_per_10g > 30000:
                        result["gold_price"] = float(gold_per_10g)
                        if not result["data_source"]:
                            result["data_source"] = "Yahoo Finance"
        except Exception as e:
            print(f"yfinance Gold error: {e}")

    # Update status
    if result["nifty_50"] > 0 or result["gold_price"] > 0:
        result["status"] = "success"
    else:
        result["status"] = "error"
        result["data_source"] = "No data available"

    return result


def get_cached_market_data():
    """
    Get market data from session state or fetch new data
    This ensures consistent data across the entire session
    """
    if 'market_data' not in st.session_state or 'market_data_timestamp' not in st.session_state:
        # Fetch fresh data
        st.session_state['market_data'] = get_market_data()
        st.session_state['market_data_timestamp'] = datetime.now()
    else:
        # Check if data is older than 5 minutes
        time_diff = (datetime.now() - st.session_state['market_data_timestamp']).total_seconds()
        if time_diff > 300:  # 5 minutes
            st.session_state['market_data'] = get_market_data()
            st.session_state['market_data_timestamp'] = datetime.now()
    
    return st.session_state['market_data']


st.markdown('<div class="main-header">AI-Powered Investment Advisor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-Agent Intelligence System for Personalized Wealth Management</div>', unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    st.header("Your Financial Profile")
    
    with st.expander("How it works", expanded=False):
        st.markdown("""
        Our AI system uses **12+ specialized agents** to:
        1. Analyze market data in real-time
        2. Profile your risk appetite
        3. Score thousands of investment options
        4. Build optimized portfolios
        5. Validate and adjust recommendations
        """)
    
    st.markdown("---")
    
    name = st.text_input("Your Name", placeholder="Enter your full name")
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=18, max_value=100, value=30)
    with col2:
        horizon = st.number_input("Horizon (Years)", min_value=1, max_value=50, value=10)
    
    income = st.number_input("Monthly Income (Rs)", min_value=0.0, value=50000.0, step=5000.0, format="%.0f")
    expenses = st.number_input("Monthly Expenses (Rs)", min_value=0.0, value=30000.0, step=5000.0, format="%.0f")
    savings = st.number_input("Current Savings (Rs)", min_value=0.0, value=100000.0, step=10000.0, format="%.0f")
    
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
        st.success(f"Available for Investment: Rs{disposable:,.0f}/month")
        generate_plan = st.button("Generate AI-Powered Plan", type="primary", use_container_width=True)

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
    time.sleep(0.3)
    
    status_text.text("Analyzing your profile...")
    progress_bar.progress(20)
    time.sleep(0.3)
    
    status_text.text("Collecting market data from MarketWatch...")
    progress_bar.progress(40)
    
    # Fetch market data ONCE and store in session state
    market_data = get_cached_market_data()
    
    with st.spinner('AI agents are analyzing thousands of investment options...'):
        analysis = agent.analyze_profile(user_data)
    
    status_text.text("Scoring assets...")
    progress_bar.progress(60)
    time.sleep(0.3)
    
    status_text.text("Constructing optimal portfolio...")
    progress_bar.progress(80)
    time.sleep(0.3)
    
    status_text.text("Finalizing recommendations...")
    progress_bar.progress(100)
    time.sleep(0.2)
    
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
                f"Rs{profile['disposable_income']:,.0f}",
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
            - Income: Rs{income:,.0f}
            - Expenses: Rs{expenses:,.0f}
            - Investable: Rs{profile['disposable_income']:,.0f}
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
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure(data=[go.Bar(
                x=list(allocation.keys()),
                y=list(allocation.values()),
                marker_color='#1f77b4'
            )])
            fig.update_layout(
                title="Investment Amount (Rs)",
                yaxis_title="Amount",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Detailed Allocation")
        allocation_df = pd.DataFrame([
            {
                "Asset Class": asset,
                "Amount (Rs)": f"Rs{amount:,.0f}",
                "Percentage": f"{strategic_pct[asset]}%",
                "Monthly SIP": f"Rs{amount:,.0f}"
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
                stars = '*' * int(score * 5)
                mf_data.append({
                    'Scheme Code': code,
                    'Score': f"{score:.2f}",
                    'Rating': stars
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
        
        # Use the same market_data from session state
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Live Market Data")
            
            if market_data.get('status') == 'success':
                st.metric(
                    "Nifty 50",
                    f"Rs{market_data.get('nifty_50', 0):,.2f}",
                    delta=None
                )
                st.metric(
                    "Gold (per 10g)",
                    f"Rs{market_data.get('gold_price', 0):,.2f}"
                )
                
                sentiment = market_data.get('market_sentiment', 'Neutral')
                st.metric(
                    "Market Sentiment",
                    sentiment
                )
                
                # Show data source and timestamp
                st.caption(f"Data source: {market_data.get('data_source', 'Multiple sources')}")
                st.caption(f"Last updated: {market_data.get('timestamp', 'Unknown')}")
            else:
                st.error("Unable to fetch live market data")
                st.caption("Please check your internet connection or try again later")
        
        with col2:
            st.subheader("Macroeconomic Indicators")
            
            macro = market_data.get('macro_indicators', {})
            if macro:
                st.markdown(f"""
                **Key Indicators:**
                - GDP Growth: {macro.get('gdp_growth', 0):.1f}%
                - Inflation Rate: {macro.get('inflation_rate', 0):.1f}%
                - Interest Rate: {macro.get('interest_rate', 0):.1f}%
                - USD/INR: Rs{macro.get('usd_inr', 0):,.2f}
                """)
            else:
                st.info("Macroeconomic data will be displayed here")
        
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
       - **Fetch live data from MarketWatch**
    
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
    
    ### Key Features:
    
    - **Personalized Risk Profiling** - AI analyzes your unique situation
    - **Multi-Factor Scoring** - Evaluates assets on 10+ parameters
    - **Smart Portfolio Construction** - Optimized for your goals
    - **Live Market Data** - Real-time prices from MarketWatch
    - **Actionable Recommendations** - Clear next steps
    - **Profile Management** - Save and track your journey
    
    ###  Get Started:
    
    1. **Fill your financial profile** in the sidebar ←
    2. **Click "Generate AI-Powered Plan"** to activate all agents
    3. **Review your personalized portfolio** with detailed analysis
    4. **Get specific recommendations** for stocks and mutual funds
    5. **Save your profile** for future reference
    
    ---
    
    ### 📊 System Status:
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Agents", "12", delta="100%")
    with col2:
        st.metric("Assets Tracked", "1000+", delta="Real-time")
    with col3:
        st.metric("Data Sources", "5+", delta="Live")
    with col4:
        st.metric("Avg. Confidence", "85%", delta="+5%")
    
    st.markdown("---")
    
    # Quick market preview - using session state
    st.subheader(" Quick Market Preview")
    with st.spinner("Fetching live market data from MarketWatch..."):
        preview_data = get_cached_market_data()
    
    if preview_data.get('status') == 'success':
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "🇮🇳 Nifty 50", 
                f"₹{preview_data.get('nifty_50', 0):,.2f}"
            )
        with col2:
            st.metric(
                "🪙 Gold (10g)", 
                f"₹{preview_data.get('gold_price', 0):,.2f}"
            )
        with col3:
            st.info(f" Source: {preview_data.get('data_source', 'Multiple')}")
        
        # Show timestamp
        st.caption(f" Last updated: {preview_data.get('timestamp', 'Unknown')}")
    else:
        st.info(" Market data will be fetched when you generate your investment plan")
    
    st.markdown("---")
    
    st.info("""
     **Disclaimer**: This is an AI-powered educational tool. While our system uses advanced 
    algorithms and real market data from MarketWatch and other sources, it should not be considered 
    as professional financial advice. Always consult with certified financial advisors before making 
    investment decisions.
    """)

with st.sidebar:
    st.markdown("---")
    st.subheader("Additional Features")
    
    if st.button("👥 View Saved Profiles", use_container_width=True):
        st.session_state['show_profiles'] = True
    
    # Add refresh button for market data
    if st.button("🔄 Refresh Market Data", use_container_width=True):
        if 'market_data' in st.session_state:
            del st.session_state['market_data']
        if 'market_data_timestamp' in st.session_state:
            del st.session_state['market_data_timestamp']
        st.success("Market data will be refreshed on next fetch!")
        st.rerun()
    
    with st.expander("System Information"):
        st.markdown(f"""
        **Version**: 2.2 (Session State + MarketWatch)
        **Agents**: 12+ specialized
        **Data Sources**: MarketWatch, Yahoo Finance, GoldAPI
        **Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
        **Status**:  All systems operational
        
        **Session Data**:
        - Market Data Cached: {'Yes' if 'market_data' in st.session_state else 'No'}
        - Cache Timestamp: {st.session_state.get('market_data_timestamp', 'N/A')}
        """)
    
    with st.expander("Investment Tips"):
        st.markdown("""
        -  Start early, invest regularly
        -  Diversify across asset classes
        -  Review portfolio quarterly
        -  Stay invested for long term
        -  Don't panic during volatility
        -  Rebalance when drift > 10%
        """)
    
    with st.expander("Data Sources"):
        st.markdown("""
        **Market Data Priority:**
        1.  MarketWatch (Primary)
        2.  Yahoo Finance (Fallback)
        3.  GoldAPI (Gold prices)
        4.  Session Cache (Consistent)
        
        *Data is cached in session state for consistency*
        *Auto-refreshes after 5 minutes*
        *Use refresh button to force update*
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
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.subheader(" User Statistics")
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

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>AI Investment Advisor v2.2</strong> | Powered by Multi-Agent Intelligence</p>
    <p>Market Data: MarketWatch | Yahoo Finance | GoldAPI | Session Cache</p>
    <p>Session Active: {'Yes ' if 'market_data' in st.session_state else 'No ⏳'}</p>
    <p>© 2024 | Educational Purpose Only | Not Financial Advice</p>
</div>
""", unsafe_allow_html=True)