# tools.py
import yfinance as yf
import requests

class InvestmentTools:
    """Collection of investment analysis tools"""
    
    @staticmethod
    def expense_analyzer(monthly_income: float, monthly_expenses: float) -> dict:
        """Calculate disposable income and savings rate."""
        disposable_income = monthly_income - monthly_expenses
        savings_rate = (disposable_income / monthly_income) * 100 if monthly_income > 0 else 0
        return {
            "disposable_income": disposable_income,
            "savings_rate": savings_rate,
            "message": f"You have ₹{disposable_income:,.2f} left to save/invest each month (a {savings_rate:.1f}% savings rate)."
        }

    @staticmethod
    def risk_profiler(age: int, investment_horizon: int, risk_tolerance: str) -> str:
        """Classify user's risk profile based on age, horizon, and stated tolerance."""
        score = 0
        
        # Age scoring
        if age < 30:
            score += 3
        elif age < 40:
            score += 2
        elif age < 55:
            score += 1
        
        # Horizon scoring
        if investment_horizon > 10:
            score += 3
        elif investment_horizon > 5:
            score += 2
        elif investment_horizon > 2:
            score += 1
        
        # Risk tolerance scoring
        if risk_tolerance.lower() == "high":
            score += 3
        elif risk_tolerance.lower() == "medium":
            score += 2
        elif risk_tolerance.lower() == "low":
            score += 1
        
        # Final classification
        if score >= 7:
            return "Aggressive"
        elif score >= 4:
            return "Balanced"
        else:
            return "Conservative"

    @staticmethod
    def get_stock_price(symbol: str) -> float:
        """Fetch the current stock price for a given ticker symbol."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return round(data['Close'].iloc[-1], 2)
            else:
                return 0.0
        except Exception as e:
            print(f"Error fetching stock price for {symbol}: {e}")
            return 0.0

    @staticmethod
    def get_mf_nav(scheme_code: str) -> float:
        """Fetch the latest NAV for a mutual fund by its AMFI scheme code."""
        try:
            url = f"https://api.mfapi.in/mf/{scheme_code}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data['data'][0]['nav'])
        except Exception as e:
            print(f"Error fetching MF NAV for {scheme_code}: {e}")
            return 0.0

    @staticmethod
    def get_gold_price() -> float:
        """Fetch the current price of gold per 10 grams in INR using Gold ETF as proxy."""
        try:
            # Using GOLDBEES (Gold ETF) as a proxy for gold price
            gold_etf_price = InvestmentTools.get_stock_price("GOLDBEES.NS")
            if gold_etf_price > 0:
                # Convert ETF price to approximate gold price per 10g
                return round(gold_etf_price * 10, 2)
            else:
                # Fallback static price if API fails
                return 65000.0
        except Exception as e:
            print(f"Error fetching gold price: {e}")
            return 65000.0

    @staticmethod
    def recommend_allocation(risk_profile: str, disposable_income: float) -> dict:
        """Suggest investment allocation based on risk profile and amount available."""
        portfolios = {
            "Conservative": {
                "Equity Mutual Funds (SIP)": 20,
                "Debt Funds/FD": 60,
                "Gold ETF": 10,
                "Emergency Fund": 10
            },
            "Balanced": {
                "Equity Mutual Funds (SIP)": 50,
                "Debt Funds/FD": 30,
                "Gold ETF": 15,
                "Emergency Fund": 5
            },
            "Aggressive": {
                "Equity Mutual Funds (SIP)": 60,
                "Direct Stocks": 15,
                "Debt Funds": 15,
                "Gold ETF": 5,
                "Emergency Fund": 5
            }
        }

        chosen_portfolio = portfolios.get(risk_profile, portfolios["Balanced"])
        allocation = {asset: round((percent / 100) * disposable_income, 2) 
                     for asset, percent in chosen_portfolio.items()}
        
        return {
            "allocation": allocation,
            "total_amount": disposable_income,
            "portfolio_type": risk_profile,
            "percentages": chosen_portfolio
        }

    @staticmethod
    def get_investment_recommendations(risk_profile: str) -> dict:
        """Get specific investment recommendations based on risk profile."""
        recommendations = {
            "Conservative": {
                "equity_funds": ["SBI Bluechip Fund", "HDFC Top 100 Fund", "ICICI Pru Bluechip Fund"],
                "debt_funds": ["SBI Magnum Income Fund", "HDFC Corporate Bond Fund", "ICICI Pru Corporate Bond Fund"],
                "gold_options": ["HDFC Gold ETF", "SBI Gold ETF", "Digital Gold"],
                "emergency_fund": ["High-yield Savings Account", "Liquid Funds", "Ultra Short Duration Funds"]
            },
            "Balanced": {
                "equity_funds": ["Parag Parikh Flexi Cap Fund", "HDFC Hybrid Equity Fund", "SBI Equity Hybrid Fund"],
                "debt_funds": ["HDFC Short Term Debt Fund", "SBI Short Term Debt Fund"],
                "gold_options": ["GOLDBEES ETF", "HDFC Gold ETF"],
                "emergency_fund": ["Liquid Funds", "Ultra Short Duration Funds"]
            },
            "Aggressive": {
                "equity_funds": ["Parag Parikh Flexi Cap", "Mirae Asset Emerging Bluechip", "Axis Small Cap Fund"],
                "direct_stocks": ["Reliance", "TCS", "HDFC Bank", "Infosys", "ICICI Bank"],
                "debt_funds": ["HDFC Ultra Short Term Fund"],
                "gold_options": ["GOLDBEES ETF"]
            }
        }
        
        return recommendations.get(risk_profile, recommendations["Balanced"])