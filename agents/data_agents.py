# agents/data_agents.py - Layer 2: Data Ingestion Agents
import yfinance as yf
import requests
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StockDataAgent:
    """Agent 3: Stock Market Data Collection"""
    
    def __init__(self, cache_duration: int = 300):
        self.cache = {}
        self.cache_duration = cache_duration
    
    def fetch_stock_data(self, symbol: str) -> Dict:
        """Fetch comprehensive stock data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            info = ticker.info
            
            if hist.empty:
                return {}
            
            return {
                'symbol': symbol,
                'current_price': hist['Close'].iloc[-1],
                'open': hist['Open'].iloc[-1],
                'high': hist['High'].iloc[-1],
                'low': hist['Low'].iloc[-1],
                'volume': hist['Volume'].iloc[-1],
                'historical_prices': hist['Close'].tolist(),
                'returns_1y': ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / 
                              hist['Close'].iloc[0] * 100),
                'volatility': hist['Close'].pct_change().std() * 100,
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'sector': info.get('sector', 'Unknown'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return {}
    
    def fetch_multiple_stocks(self, symbols: List[str]) -> Dict:
        """Fetch data for multiple stocks"""
        results = {}
        for symbol in symbols:
            data = self.fetch_stock_data(symbol)
            if data:
                results[symbol] = data
        return results


class MutualFundDataAgent:
    """Agent 4: Mutual Fund Data Collection"""
    
    def __init__(self):
        self.base_url = "https://api.mfapi.in/mf"
    
    def fetch_fund_data(self, scheme_code: str) -> Dict:
        """Fetch mutual fund data from AMFI"""
        try:
            url = f"{self.base_url}/{scheme_code}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse historical data
            nav_history = data.get('data', [])[:365]  # Last 1 year
            
            if not nav_history:
                return {}
            
            navs = [float(d['nav']) for d in nav_history]
            
            return {
                'scheme_code': scheme_code,
                'scheme_name': data.get('meta', {}).get('scheme_name', ''),
                'current_nav': float(nav_history[0]['nav']),
                'nav_history': navs,
                'returns_1y': ((navs[0] - navs[-1]) / navs[-1] * 100) if len(navs) > 1 else 0,
                'returns_3y': self._calculate_cagr(navs, 3) if len(navs) >= 1095 else 0,
                'volatility': self._calculate_volatility(navs),
                'consistency': self._calculate_consistency(navs),
                'sharpe_ratio': self._calculate_sharpe(navs),
                'fund_category': data.get('meta', {}).get('scheme_category', ''),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching MF data for {scheme_code}: {e}")
            return {}
    
    def fetch_multiple_funds(self, scheme_codes: List[str]) -> Dict:
        """Fetch data for multiple mutual funds"""
        results = {}
        for code in scheme_codes:
            data = self.fetch_fund_data(code)
            if data:
                results[code] = data
        return results
    
    @staticmethod
    def _calculate_cagr(navs: List[float], years: int) -> float:
        """Calculate CAGR"""
        try:
            days = years * 365
            if len(navs) < days:
                return 0
            return ((navs[0] / navs[days]) ** (1/years) - 1) * 100
        except:
            return 0
    
    @staticmethod
    def _calculate_volatility(navs: List[float]) -> float:
        """Calculate volatility (standard deviation of returns)"""
        try:
            returns = [(navs[i] - navs[i+1]) / navs[i+1] for i in range(len(navs)-1)]
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            return (variance ** 0.5) * 100
        except:
            return 0
    
    @staticmethod
    def _calculate_consistency(navs: List[float]) -> float:
        """Calculate consistency score (0-1)"""
        try:
            # Percentage of positive returns
            returns = [(navs[i] - navs[i+1]) / navs[i+1] for i in range(len(navs)-1)]
            positive_returns = sum(1 for r in returns if r > 0)
            return positive_returns / len(returns) if returns else 0.5
        except:
            return 0.5
    
    @staticmethod
    def _calculate_sharpe(navs: List[float], risk_free_rate: float = 6.5) -> float:
        """Calculate Sharpe ratio"""
        try:
            returns = [(navs[i] - navs[i+1]) / navs[i+1] * 100 for i in range(len(navs)-1)]
            avg_return = sum(returns) / len(returns) * 365  # Annualized
            
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            std_dev = (variance ** 0.5) * (365 ** 0.5)  # Annualized
            
            return (avg_return - risk_free_rate) / std_dev if std_dev > 0 else 0
        except:
            return 0


class MacroeconomicAgent:
    """Agent 5: Macroeconomic Data Collection"""
    
    def __init__(self):
        self.indicators = {}
    
    def get_indicators(self) -> Dict:
        """Get macroeconomic indicators"""
        try:
            # Simulated data - in production, fetch from RBI/FRED APIs
            indicators = {
                'gdp_growth': 6.5,  # %
                'inflation_rate': 5.2,  # CPI
                'interest_rate': 6.5,  # Repo rate
                'unemployment_rate': 7.8,
                'industrial_production': 4.2,
                'fiscal_deficit': 5.9,
                'current_account_deficit': -2.1,
                'forex_reserves': 625.0,  # Billion USD
                'crude_oil_price': 85.0,  # USD per barrel
                'usd_inr': 83.25,
                'sentiment_index': 0.65,  # 0-1 scale
                'timestamp': datetime.now().isoformat()
            }
            
            return indicators
        except Exception as e:
            logger.error(f"Error fetching macro indicators: {e}")
            return {}
    
    def get_market_regime(self) -> str:
        """Determine current market regime"""
        indicators = self.get_indicators()
        
        # Simple regime classification
        if indicators['gdp_growth'] > 7 and indicators['inflation_rate'] < 6:
            return "Bullish"
        elif indicators['gdp_growth'] < 5 or indicators['inflation_rate'] > 7:
            return "Bearish"
        else:
            return "Neutral"


class NewsAgent:
    """Agent 6: News & Sentiment Analysis"""
    
    def __init__(self):
        self.sentiment_cache = {}
    
    def get_market_sentiment(self) -> str:
        """Get overall market sentiment"""
        try:
            # In production: Fetch from news APIs and use FinBERT for sentiment
            # For now, return simulated sentiment
            
            # Simple heuristic based on market movement
            nifty = yf.Ticker("^NSEI")
            hist = nifty.history(period="5d")
            
            if hist.empty:
                return "Neutral"
            
            price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / 
                           hist['Close'].iloc[0] * 100)
            
            if price_change > 2:
                return "Positive"
            elif price_change < -2:
                return "Negative"
            else:
                return "Neutral"
                
        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            return "Neutral"
    
    def get_news_summary(self, topic: str = "indian stock market") -> List[Dict]:
        """Get news summary for a topic"""
        # Placeholder for news fetching
        # In production: Use NewsAPI, RSS feeds, or web scraping
        return [
            {
                'title': 'Market Update',
                'sentiment': 'Neutral',
                'source': 'Economic Times',
                'timestamp': datetime.now().isoformat()
            }
        ]