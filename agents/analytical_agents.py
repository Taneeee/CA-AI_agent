# agents/analytical_agents.py - Layer 4: Analytical Scoring Agents
from typing import Dict
import logging
import numpy as np

logger = logging.getLogger(__name__)

class ValuationAgent:
    """Agent 8: Valuation Analysis"""
    
    def __init__(self):
        self.sector_pe_benchmarks = {
            'Technology': 25.0,
            'Finance': 15.0,
            'Healthcare': 30.0,
            'Consumer': 40.0,
            'Energy': 12.0,
            'Default': 20.0
        }
    
    def score(self, asset_data: Dict) -> float:
        """Score asset based on valuation metrics (0-1)"""
        try:
            score = 0.0
            weights = {'pe': 0.4, 'pb': 0.3, 'dividend': 0.3}
            
            # PE Ratio scoring (lower is better, relative to sector)
            pe_ratio = asset_data.get('pe_ratio', 0)
            sector = asset_data.get('sector', 'Default')
            benchmark_pe = self.sector_pe_benchmarks.get(sector, 20.0)
            
            if pe_ratio > 0:
                pe_score = max(0, 1 - (pe_ratio / benchmark_pe - 1))
                score += pe_score * weights['pe']
            else:
                score += 0.5 * weights['pe']  # Neutral if PE not available
            
            # PB Ratio scoring (lower is better)
            pb_ratio = asset_data.get('pb_ratio', 0)
            if pb_ratio > 0:
                pb_score = max(0, 1 - (pb_ratio / 3))  # 3 as benchmark
                score += pb_score * weights['pb']
            else:
                score += 0.5 * weights['pb']
            
            # Dividend Yield scoring (higher is better)
            dividend_yield = asset_data.get('dividend_yield', 0) * 100
            div_score = min(dividend_yield / 5, 1)  # 5% as excellent
            score += div_score * weights['dividend']
            
            return min(max(score, 0), 1)
            
        except Exception as e:
            logger.error(f"Error in valuation scoring: {e}")
            return 0.5


class MomentumAgent:
    """Agent 9: Momentum & Technical Analysis"""
    
    def __init__(self):
        self.lookback_periods = [5, 10, 20, 50, 200]
    
    def score(self, asset_data: Dict) -> float:
        """Score asset based on momentum indicators (0-1)"""
        try:
            score = 0.0
            
            # Returns-based momentum (40%)
            returns_1y = asset_data.get('returns_1y', 0)
            returns_score = self._score_returns(returns_1y)
            score += returns_score * 0.4
            
            # Price trend analysis (30%)
            historical_prices = asset_data.get('historical_prices', [])
            if historical_prices and len(historical_prices) >= 50:
                trend_score = self._calculate_trend_strength(historical_prices)
                score += trend_score * 0.3
            else:
                score += 0.5 * 0.3
            
            # Volume analysis (15%)
            volume = asset_data.get('volume', 0)
            volume_score = self._score_volume(volume)
            score += volume_score * 0.15
            
            # RSI indicator (15%)
            if historical_prices and len(historical_prices) >= 14:
                rsi = self._calculate_rsi(historical_prices[-14:])
                rsi_score = self._score_rsi(rsi)
                score += rsi_score * 0.15
            else:
                score += 0.5 * 0.15
            
            return min(max(score, 0), 1)
            
        except Exception as e:
            logger.error(f"Error in momentum scoring: {e}")
            return 0.5
    
    def _score_returns(self, returns: float) -> float:
        """Score based on returns"""
        # Normalize returns: >20% = 1.0, <-20% = 0.0
        if returns > 20:
            return 1.0
        elif returns < -20:
            return 0.0
        else:
            return (returns + 20) / 40
    
    def _calculate_trend_strength(self, prices: list) -> float:
        """Calculate trend strength using linear regression"""
        try:
            n = len(prices)
            x = list(range(n))
            y = prices
            
            # Simple linear regression
            x_mean = sum(x) / n
            y_mean = sum(y) / n
            
            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return 0.5
            
            slope = numerator / denominator
            
            # Normalize slope
            normalized_slope = (slope / y_mean) * 100
            
            # Strong uptrend = 1, strong downtrend = 0
            return min(max((normalized_slope + 5) / 10, 0), 1)
            
        except:
            return 0.5
    
    def _score_volume(self, volume: float) -> float:
        """Score based on volume (placeholder)"""
        # In production: Compare with average volume
        return 0.6
    
    def _calculate_rsi(self, prices: list, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        try:
            if len(prices) < period + 1:
                return 50
            
            changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            
            gains = [c if c > 0 else 0 for c in changes]
            losses = [-c if c < 0 else 0 for c in changes]
            
            avg_gain = sum(gains) / len(gains)
            avg_loss = sum(losses) / len(losses)
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except:
            return 50
    
    def _score_rsi(self, rsi: float) -> float:
        """Score based on RSI value"""
        # RSI 40-60 is neutral (score 0.5)
        # RSI > 70 is overbought (lower score)
        # RSI < 30 is oversold (lower score)
        if 40 <= rsi <= 60:
            return 1.0
        elif rsi > 70:
            return max(0, 1 - (rsi - 70) / 30)
        elif rsi < 30:
            return max(0, rsi / 30)
        else:
            return 0.8


class QualityAgent:
    """Agent 10: Quality & Fundamental Analysis"""
    
    def __init__(self):
        pass
    
    def score(self, asset_data: Dict) -> float:
        """Score asset based on quality metrics (0-1)"""
        try:
            score = 0.0
            
            # Market cap (30%) - prefer large/mid caps
            market_cap = asset_data.get('market_cap', 0)
            cap_score = self._score_market_cap(market_cap)
            score += cap_score * 0.3
            
            # Sector strength (25%)
            sector = asset_data.get('sector', 'Unknown')
            sector_score = self._score_sector(sector)
            score += sector_score * 0.25
            
            # Growth metrics (25%)
            returns_1y = asset_data.get('returns_1y', 0)
            growth_score = min(max(returns_1y / 30, 0), 1)  # 30% = excellent
            score += growth_score * 0.25
            
            # Stability (20%) - inverse of volatility
            volatility = asset_data.get('volatility', 20)
            stability_score = max(0, 1 - (volatility / 40))
            score += stability_score * 0.2
            
            return min(max(score, 0), 1)
            
        except Exception as e:
            logger.error(f"Error in quality scoring: {e}")
            return 0.5
    
    def _score_market_cap(self, market_cap: float) -> float:
        """Score based on market capitalization"""
        if market_cap > 1e12:  # > 1 trillion (Large cap)
            return 1.0
        elif market_cap > 5e11:  # > 500 billion (Large cap)
            return 0.9
        elif market_cap > 1e11:  # > 100 billion (Mid cap)
            return 0.7
        elif market_cap > 5e10:  # > 50 billion (Mid cap)
            return 0.6
        else:  # Small cap
            return 0.4
    
    def _score_sector(self, sector: str) -> float:
        """Score based on sector outlook"""
        # Current sector preferences (example)
        sector_scores = {
            'Technology': 0.9,
            'Finance': 0.8,
            'Healthcare': 0.85,
            'Consumer': 0.75,
            'Energy': 0.7,
            'Industrials': 0.7,
            'Utilities': 0.6,
            'Default': 0.65
        }
        return sector_scores.get(sector, 0.65)


class RiskAgent:
    """Agent 11: Risk Assessment"""
    
    def __init__(self):
        pass
    
    def score(self, asset_data: Dict) -> float:
        """Score asset based on risk metrics (0-1, higher = lower risk)"""
        try:
            score = 0.0
            
            # Volatility (40%) - lower is better
            volatility = asset_data.get('volatility', 20)
            vol_score = max(0, 1 - (volatility / 50))  # 50% vol = very high risk
            score += vol_score * 0.4
            
            # Beta (30%) - closer to 1 is better
            # For now, estimate beta from volatility
            estimated_beta = volatility / 20  # Rough estimate
            beta_score = max(0, 1 - abs(estimated_beta - 1))
            score += beta_score * 0.3
            
            # Drawdown resistance (30%)
            historical_prices = asset_data.get('historical_prices', [])
            if historical_prices and len(historical_prices) >= 30:
                max_drawdown = self._calculate_max_drawdown(historical_prices)
                drawdown_score = max(0, 1 - (abs(max_drawdown) / 30))
                score += drawdown_score * 0.3
            else:
                score += 0.5 * 0.3
            
            return min(max(score, 0), 1)
            
        except Exception as e:
            logger.error(f"Error in risk scoring: {e}")
            return 0.5
    
    def _calculate_max_drawdown(self, prices: list) -> float:
        """Calculate maximum drawdown percentage"""
        try:
            if not prices or len(prices) < 2:
                return 0
            
            peak = prices[0]
            max_dd = 0
            
            for price in prices:
                if price > peak:
                    peak = price
                dd = ((price - peak) / peak) * 100
                if dd < max_dd:
                    max_dd = dd
            
            return max_dd
            
        except:
            return 0
    
    def calculate_var(self, returns: list, confidence: float = 0.95) -> float:
        """Calculate Value at Risk"""
        try:
            if not returns:
                return 0
            
            sorted_returns = sorted(returns)
            index = int((1 - confidence) * len(sorted_returns))
            return sorted_returns[index]
            
        except:
            return 0


class MutualFundScoringAgent:
    """Agent 12: Mutual Fund Scoring"""
    
    def __init__(self):
        pass
    
    def score(self, mf_data: Dict) -> float:
        """Score mutual fund comprehensively"""
        try:
            score = 0.0
            
            # Returns (35%)
            returns_3y = mf_data.get('returns_3y', 0)
            returns_score = min(returns_3y / 20, 1)  # 20% = excellent
            score += returns_score * 0.35
            
            # Risk-adjusted returns - Sharpe ratio (30%)
            sharpe = mf_data.get('sharpe_ratio', 0)
            sharpe_score = min(sharpe / 2, 1)  # Sharpe > 2 = excellent
            score += sharpe_score * 0.30
            
            # Consistency (20%)
            consistency = mf_data.get('consistency', 0.5)
            score += consistency * 0.20
            
            # Volatility (15%) - lower is better
            volatility = mf_data.get('volatility', 15)
            vol_score = max(0, 1 - (volatility / 30))
            score += vol_score * 0.15
            
            return min(max(score, 0), 1)
            
        except Exception as e:
            logger.error(f"Error scoring mutual fund: {e}")
            return 0.5