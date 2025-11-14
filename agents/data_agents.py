import yfinance as yf
import requests
import json
from bs4 import BeautifulSoup
from typing import Dict, List
from datetime import datetime
import logging
import time
import random
import aiohttp
import asyncio
from fake_useragent import UserAgent
import brotli


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StockDataAgent:
    """Fetch stock data safely with caching and rate-limit protection"""

    def __init__(self, cache_duration: int = 300, max_retries: int = 3):
        self.cache = {}
        self.cache_duration = cache_duration
        self.max_retries = max_retries
        self.fallback_urls = [
            "https://query1.finance.yahoo.com",
            "https://query2.finance.yahoo.com"
        ]
        self.nse_base_url = "https://www.nseindia.com/api/quote-equity"
        self.alt_sources = {
            "screener": "https://www.screener.in/company/{}/",
            "money_control": "https://www.moneycontrol.com/india/stockpricequote/"
        }
        self.user_agent = UserAgent()
        self.alternative_urls = {
            "investing": "https://in.investing.com/equities/{}-stock",
            "google": "https://www.google.com/finance/quote/{}:NSE",
            "marketwatch": "https://www.marketwatch.com/investing/stock/{}"
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }

    def _clean_symbol(self, symbol: str) -> str:
        """Ensure correct Yahoo format"""
        if not symbol.endswith(".NS") and not symbol.startswith("^"):
            return f"{symbol}.NS"
        return symbol

    def _get_nse_data(self, symbol: str) -> Dict:
        """Fallback to NSE direct API"""
        try:
            clean_symbol = symbol.replace('.NS', '')
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.5",
            }
            session = requests.Session()
            session.get("https://www.nseindia.com/", headers=headers, timeout=10)
            url = f"{self.nse_base_url}?symbol={clean_symbol}"
            r = session.get(url, headers=headers, timeout=10)
            if r.status_code in (401, 403, 429):
                logger.warning(f"NSE blocked or rate-limited for {symbol}: {r.status_code}")
                return {}
            r.raise_for_status()
            data = r.json()
            return {
                "symbol": symbol,
                "current_price": float(data.get("lastPrice", 0)),
                "open": float(data.get("open", 0)),
                "high": float(data.get("dayHigh", 0)),
                "low": float(data.get("dayLow", 0)),
                "volume": int(data.get("totalTradedVolume", 0)),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.debug(f"NSE direct fetch failed for {symbol}: {e}")
            return {}

    def _get_stock_data_screener(self, symbol: str) -> Dict:
        """Fallback to Screener.in"""
        try:
            clean_symbol = symbol.replace('.NS', '')
            url = self.alt_sources["screener"].format(clean_symbol.lower())
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code in (401, 403, 429):
                logger.warning(f"Screener.in blocked or rate-limited for {symbol}: {r.status_code}")
                return {}
            soup = BeautifulSoup(r.text, 'html.parser')
            price = soup.select_one('.current-price')
            if price:
                return {
                    "symbol": symbol,
                    "current_price": float(price.text.strip().replace(',', '')),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.debug(f"Screener fetch failed: {e}")
        return {}

    def _get_yf_direct(self, symbol: str) -> Dict:
        """Directly scrape Yahoo Finance"""
        try:
            yf_symbol = self._clean_symbol(symbol)
            url = f"https://finance.yahoo.com/quote/{yf_symbol}"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code in (401, 403, 429):
                logger.warning(f"Yahoo direct blocked or rate-limited for {symbol}: {r.status_code}")
                return {}
            soup = BeautifulSoup(r.text, 'html.parser')
            price_elem = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
            if not price_elem:
                return {}
            price = float(price_elem.get('value', 0))
            return {
                "symbol": yf_symbol,
                "current_price": price,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.debug(f"YF direct scraping failed: {e}")
            return {}

    def _get_random_headers(self):
        """Generate random headers to avoid detection"""
        return {
            "User-Agent": self.user_agent.random,
            "Accept": "text/html,application/json,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }

    async def _fetch_url(self, url: str, timeout: int = 10) -> str:
        """Fetch URL with proper error handling and compression support"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status in (429, 403, 401):
                        logger.warning(f"Rate limited: {url} ({response.status})")
                        return ""
                    
                    content = await response.read()
                    
 
                    encoding = response.headers.get('Content-Encoding', '').lower()
                    if encoding == 'br':
                        content = brotli.decompress(content)
                    elif encoding == 'gzip':
                        content = await response.read()
                    
               
                    try:
                        return content.decode('utf-8')
                    except UnicodeDecodeError:
                        return content.decode('latin-1')
                        
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
            return ""

    def _parse_price_from_html(self, html: str, source: str) -> float:
        """Extract price from HTML based on source"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            if source == "investing":
                price_elem = soup.select_one("span[data-test='instrument-price-last']")
            elif source == "google":
                price_elem = soup.select_one("div[data-last-price]")
            elif source == "marketwatch":
                price_elem = soup.select_one(".intraday__price .value")
            return float(price_elem.text.replace(',', '')) if price_elem else 0
        except Exception:
            return 0

    def fetch_stock_data(self, symbol: str) -> Dict:
        """Fetch single stock data with retries and fallbacks"""
        if not symbol or not isinstance(symbol, str):
            logger.error(f"Invalid symbol: {symbol}")
            return {}


        if symbol in self.cache:
            cached, timestamp = self.cache[symbol]
            if (datetime.now() - timestamp).seconds < self.cache_duration:
                logger.debug(f"Cache hit for {symbol}")
                return cached

        clean_symbol = symbol.replace('.NS', '').lower()
        

        sources = [
            (self.alternative_urls["marketwatch"], "marketwatch", f"{clean_symbol}"),
            (self.alternative_urls["google"], "google", f"{clean_symbol}"),
            (self.alternative_urls["investing"], "investing", clean_symbol.replace(" ", "-")),
        ]
        
        for attempt in range(self.max_retries):
            try:
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                urls = [(url_template.format(slug), source) for url_template, source, slug in sources]
                responses = loop.run_until_complete(
                    asyncio.gather(
                        *[self._fetch_url(url) for url, _ in urls]
                    )
                )
                loop.close()
                
                
                for html, (_, source) in zip(responses, urls):
                    if html:
                        price = self._parse_price_from_html(html, source)
                        if price > 0:
                            data = {
                                "symbol": symbol,
                                "current_price": price,
                                "timestamp": datetime.now().isoformat()
                            }
                            self.cache[symbol] = (data, datetime.now())
                            logger.info(f" Fetched {symbol} via {source}")
                            return data
                            
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(min(5 * (2 ** attempt), 60))
                continue
            
            time.sleep(min(10 * (2 ** attempt), 90))
        
        logger.error(f" All attempts failed for {symbol}")
        return {}

    def fetch_multiple_stocks(self, symbols: List[str]) -> Dict:
        """Batch fetch multiple stocks (with polite delay between requests)"""
        results = {}
        for symbol in symbols:
            data = self.fetch_stock_data(symbol)
            if data:
                results[symbol] = data
            time.sleep(random.uniform(2, 4))
        return results

class MutualFundDataAgent:
    """Fetch Indian mutual fund NAVs from MFAPI"""

    def __init__(self):
        self.base_url = "https://api.mfapi.in/mf"

    def fetch_fund_data(self, scheme_code: str) -> Dict:
        """Fetch NAV history for a mutual fund"""
        try:
            url = f"{self.base_url}/{scheme_code}"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            r.raise_for_status()
            data = r.json()

            nav_history = data.get("data", [])[:365]
            if not nav_history:
                return {}

            navs = [float(d["nav"]) for d in nav_history]

            return {
                "scheme_code": scheme_code,
                "scheme_name": data.get("meta", {}).get("scheme_name", ""),
                "current_nav": navs[0],
                "nav_history": navs,
                "returns_1y": ((navs[0] - navs[-1]) / navs[-1] * 100)
                if len(navs) > 1
                else 0,
                "volatility": self._calculate_volatility(navs),
                "consistency": self._calculate_consistency(navs),
                "sharpe_ratio": self._calculate_sharpe(navs),
                "category": data.get("meta", {}).get("scheme_category", ""),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error fetching mutual fund {scheme_code}: {e}")
            return {}

    def fetch_multiple_funds(self, scheme_codes: List[str]) -> Dict:
        """Fetch multiple mutual funds"""
        results = {}
        for code in scheme_codes:
            data = self.fetch_fund_data(code)
            if data:
                results[code] = data
            time.sleep(random.uniform(1, 3))
        return results

    # ---- metrics ----
    @staticmethod
    def _calculate_volatility(navs: List[float]) -> float:
        try:
            returns = [(navs[i] - navs[i + 1]) / navs[i + 1] for i in range(len(navs) - 1)]
            mean = sum(returns) / len(returns)
            variance = sum((r - mean) ** 2 for r in returns) / len(returns)
            return (variance ** 0.5) * 100
        except:
            return 0

    @staticmethod
    def _calculate_consistency(navs: List[float]) -> float:
        try:
            returns = [(navs[i] - navs[i + 1]) / navs[i + 1] for i in range(len(navs) - 1)]
            return sum(1 for r in returns if r > 0) / len(returns)
        except:
            return 0.5

    @staticmethod
    def _calculate_sharpe(navs: List[float], risk_free_rate=6.5) -> float:
        try:
            returns = [(navs[i] - navs[i + 1]) / navs[i + 1] * 100 for i in range(len(navs) - 1)]
            avg_return = sum(returns) / len(returns) * 365
            mean = sum(returns) / len(returns)
            variance = sum((r - mean) ** 2 for r in returns) / len(returns)
            std_dev = (variance ** 0.5) * (365 ** 0.5)
            return (avg_return - risk_free_rate) / std_dev if std_dev else 0
        except:
            return 0


class MacroeconomicAgent:
    """Fetch live macro data (currently simulated for India)"""

    def __init__(self):
        self.worldbank_base = "https://api.worldbank.org/v2/country/IN/indicator"

    def get_indicators(self) -> Dict:
        """Return sample or live macroeconomic indicators"""
        try:
            return {
                "gdp_growth": 6.5,
                "inflation_rate": 5.2,
                "interest_rate": 6.5,
                "unemployment_rate": 7.8,
                "industrial_production": 4.2,
                "fiscal_deficit": 5.9,
                "forex_reserves": 625.0,
                "usd_inr": 83.25,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Macro data error: {e}")
            return {}

    def get_market_regime(self) -> str:
        data = self.get_indicators()
        if data["gdp_growth"] > 7 and data["inflation_rate"] < 6:
            return "Bullish"
        elif data["gdp_growth"] < 5 or data["inflation_rate"] > 7:
            return "Bearish"
        return "Neutral"


class NewsAgent:
    """Fetch market news and sentiment (NewsAPI demo)"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or "YOUR_NEWSAPI_KEY"
        self.base_url = "https://newsapi.org/v2/everything"

    def get_market_sentiment(self) -> str:
        """Simple market sentiment based on NIFTY movement"""
        try:
            nifty = yf.Ticker("^NSEI")
            hist = nifty.history(period="5d")
            
            if hist.empty:
                return "Neutral"
            change = (hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0] * 100
            if change > 2:
                return "Positive"
            elif change < -2:
                return "Negative"
            return "Neutral"
        except Exception as e:
            logger.error(f"Sentiment fetch failed: {e}")
            return "Neutral"

    def get_news_summary(self, topic: str = "indian stock market") -> List[Dict]:
        """Fetch market news summaries (requires API key)"""
        try:
            params = {"q": topic, "sortBy": "publishedAt", "language": "en", "apiKey": self.api_key}
            r = requests.get(self.base_url, params=params, timeout=10)
            r.raise_for_status()
            articles = r.json().get("articles", [])[:5]
            return [
                {"title": a["title"], "source": a["source"]["name"], "timestamp": a["publishedAt"]}
                for a in articles
            ]
        except Exception as e:
            logger.error(f"News fetch failed: {e}")
            return []
