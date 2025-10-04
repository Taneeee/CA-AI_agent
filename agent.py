# agent.py - Enhanced Multi-Agent System
from tools import InvestmentTools
from agents.data_agents import StockDataAgent, MutualFundDataAgent, MacroeconomicAgent, NewsAgent
from agents.analytical_agents import ValuationAgent, MomentumAgent, QualityAgent, RiskAgent
from agents.user_agents import UserProfilingAgent, ExpenseTrackingAgent
from agents.portfolio_agents import PortfolioConstructionAgent, MetaController
import json
import ray
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvestmentAgent:
    """Enhanced investment advisor agent with multi-agent architecture"""
    
    def __init__(self, use_ray: bool = False):
        self.tools = InvestmentTools()
        self.use_ray = use_ray
        
        # Initialize Ray if enabled
        if self.use_ray and not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
        
        # Initialize agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agent components"""
        try:
            # Data ingestion agents (Layer 2)
            self.stock_agent = StockDataAgent()
            self.mf_agent = MutualFundDataAgent()
            self.macro_agent = MacroeconomicAgent()
            self.news_agent = NewsAgent()
            
            # User intelligence agents (Layer 1 & 3)
            self.user_profiler = UserProfilingAgent()
            self.expense_tracker = ExpenseTrackingAgent()
            
            # Analytical scoring agents (Layer 4)
            self.valuation_agent = ValuationAgent()
            self.momentum_agent = MomentumAgent()
            self.quality_agent = QualityAgent()
            self.risk_agent = RiskAgent()
            
            # Portfolio construction agents (Layer 6)
            self.portfolio_constructor = PortfolioConstructionAgent()
            self.meta_controller = MetaController()
            
            logger.info("All agents initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise
    
    def analyze_profile(self, user_data: dict) -> dict:
        """Enhanced analysis with multi-agent coordination"""
        
        try:
            # Extract user data
            age = user_data.get('age')
            income = user_data.get('income')
            expenses = user_data.get('expenses')
            savings = user_data.get('savings')
            horizon = user_data.get('horizon')
            risk_tolerance = user_data.get('risk_tolerance')
            
            # Phase 1: User Profiling (Layer 1)
            logger.info("Phase 1: User profiling...")
            expense_analysis = self.expense_tracker.analyze_expenses(income, expenses)
            user_profile = self.user_profiler.create_profile(
                age=age,
                income=income,
                horizon=horizon,
                risk_tolerance=risk_tolerance,
                savings=savings
            )
            
            # Phase 2: Data Collection (Layer 2)
            logger.info("Phase 2: Collecting market data...")
            market_data = self._collect_market_data()
            
            # Phase 3: Asset Scoring (Layer 4)
            logger.info("Phase 3: Scoring assets...")
            asset_scores = self._score_assets(market_data, user_profile)
            
            # Phase 4: Portfolio Construction (Layer 6)
            logger.info("Phase 4: Constructing portfolio...")
            portfolio = self._construct_portfolio(
                user_profile=user_profile,
                asset_scores=asset_scores,
                disposable_income=expense_analysis['disposable_income']
            )
            
            # Phase 5: Meta-control & Recommendations
            logger.info("Phase 5: Generating recommendations...")
            recommendations = self._generate_recommendations(
                user_profile=user_profile,
                portfolio=portfolio,
                asset_scores=asset_scores
            )
            
            # Compile comprehensive results
            analysis_result = {
                "user_profile": {
                    "risk_profile": user_profile['risk_profile'],
                    "risk_score": user_profile.get('risk_score', 0),
                    "disposable_income": expense_analysis['disposable_income'],
                    "savings_rate": expense_analysis['savings_rate'],
                    "investment_capacity": expense_analysis['disposable_income']
                },
                "market_analysis": {
                    "market_sentiment": market_data.get('sentiment', 'Neutral'),
                    "macro_indicators": market_data.get('macro_indicators', {}),
                    "top_performers": market_data.get('top_stocks', [])
                },
                "portfolio": portfolio,
                "asset_scores": asset_scores,
                "recommendations": recommendations,
                "analysis_summary": self._generate_summary(user_profile, expense_analysis, portfolio),
                "confidence_score": self._calculate_confidence(asset_scores)
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in analyze_profile: {e}")
            raise
    
    def _collect_market_data(self) -> Dict:
        """Collect data from multiple sources using data agents"""
        market_data = {}
        
        try:
            # Stock data
            stock_symbols = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']
            market_data['stocks'] = self.stock_agent.fetch_multiple_stocks(stock_symbols)
            
            # Mutual fund data
            mf_codes = ['120503', '119551', '118989']  # Sample MF codes
            market_data['mutual_funds'] = self.mf_agent.fetch_multiple_funds(mf_codes)
            
            # Macroeconomic indicators
            market_data['macro_indicators'] = self.macro_agent.get_indicators()
            
            # Market sentiment
            market_data['sentiment'] = self.news_agent.get_market_sentiment()
            
            # Index data
            market_data['nifty_data'] = self.stock_agent.fetch_stock_data('^NSEI')
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error collecting market data: {e}")
            return {}
    
    def _score_assets(self, market_data: Dict, user_profile: Dict) -> Dict:
        """Score assets using analytical agents"""
        scores = {
            'stocks': {},
            'mutual_funds': {},
            'aggregated': {}
        }
        
        try:
            # Score stocks
            for symbol, stock_data in market_data.get('stocks', {}).items():
                stock_scores = {
                    'valuation': self.valuation_agent.score(stock_data),
                    'momentum': self.momentum_agent.score(stock_data),
                    'quality': self.quality_agent.score(stock_data),
                    'risk': self.risk_agent.score(stock_data)
                }
                
                # Weighted aggregate based on user risk profile
                weights = self._get_scoring_weights(user_profile['risk_profile'])
                aggregate_score = sum(
                    stock_scores[key] * weights[key] 
                    for key in weights
                )
                
                scores['stocks'][symbol] = {
                    'individual_scores': stock_scores,
                    'aggregate_score': aggregate_score
                }
            
            # Score mutual funds
            for code, mf_data in market_data.get('mutual_funds', {}).items():
                mf_score = self._score_mutual_fund(mf_data)
                scores['mutual_funds'][code] = mf_score
            
            return scores
            
        except Exception as e:
            logger.error(f"Error scoring assets: {e}")
            return scores
    
    def _get_scoring_weights(self, risk_profile: str) -> Dict:
        """Get scoring weights based on risk profile"""
        weights = {
            'Conservative': {
                'valuation': 0.3,
                'momentum': 0.2,
                'quality': 0.3,
                'risk': 0.2
            },
            'Balanced': {
                'valuation': 0.25,
                'momentum': 0.25,
                'quality': 0.25,
                'risk': 0.25
            },
            'Aggressive': {
                'valuation': 0.2,
                'momentum': 0.35,
                'quality': 0.25,
                'risk': 0.2
            }
        }
        return weights.get(risk_profile, weights['Balanced'])
    
    def _score_mutual_fund(self, mf_data: Dict) -> float:
        """Score a mutual fund based on performance metrics"""
        try:
            score = 0.0
            
            # Returns (40%)
            returns = mf_data.get('returns_3y', 0)
            score += min(returns / 20, 0.4)  # Normalize to 0-0.4
            
            # Consistency (30%)
            consistency = mf_data.get('consistency', 0.5)
            score += consistency * 0.3
            
            # Risk-adjusted returns (30%)
            sharpe = mf_data.get('sharpe_ratio', 0)
            score += min(sharpe / 3, 0.3)  # Normalize to 0-0.3
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error scoring mutual fund: {e}")
            return 0.5
    
    def _construct_portfolio(self, user_profile: Dict, asset_scores: Dict, 
                            disposable_income: float) -> Dict:
        """Construct optimized portfolio using portfolio construction agent"""
        try:
            portfolio = self.portfolio_constructor.construct(
                user_profile=user_profile,
                asset_scores=asset_scores,
                investment_amount=disposable_income
            )
            
            # Apply meta-controller for validation and adjustment
            validated_portfolio = self.meta_controller.validate_and_adjust(
                portfolio=portfolio,
                user_profile=user_profile
            )
            
            return validated_portfolio
            
        except Exception as e:
            logger.error(f"Error constructing portfolio: {e}")
            # Fallback to basic allocation
            return self.tools.recommend_allocation(
                user_profile['risk_profile'], 
                disposable_income
            )
    
    def _generate_recommendations(self, user_profile: Dict, portfolio: Dict, 
                                 asset_scores: Dict) -> Dict:
        """Generate specific investment recommendations"""
        recommendations = {
            'top_stocks': [],
            'top_mutual_funds': [],
            'strategy_suggestions': [],
            'rebalancing_triggers': []
        }
        
        try:
            # Top stocks based on scores
            stock_scores = asset_scores.get('stocks', {})
            sorted_stocks = sorted(
                stock_scores.items(),
                key=lambda x: x[1]['aggregate_score'],
                reverse=True
            )[:5]
            
            recommendations['top_stocks'] = [
                {
                    'symbol': symbol,
                    'score': data['aggregate_score'],
                    'reason': self._generate_stock_reason(data['individual_scores'])
                }
                for symbol, data in sorted_stocks
            ]
            
            # Top mutual funds
            mf_scores = asset_scores.get('mutual_funds', {})
            sorted_mfs = sorted(mf_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            
            recommendations['top_mutual_funds'] = [
                {'code': code, 'score': score}
                for code, score in sorted_mfs
            ]
            
            # Strategy suggestions based on risk profile
            recommendations['strategy_suggestions'] = self._get_strategy_suggestions(
                user_profile['risk_profile']
            )
            
            # Rebalancing triggers
            recommendations['rebalancing_triggers'] = [
                "Review quarterly or when allocation drifts >10%",
                "Rebalance when major life events occur",
                "Consider tax-loss harvesting in March"
            ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return recommendations
    
    def _generate_stock_reason(self, scores: Dict) -> str:
        """Generate explanation for stock recommendation"""
        top_factor = max(scores, key=scores.get)
        return f"Strong {top_factor} score ({scores[top_factor]:.2f})"
    
    def _get_strategy_suggestions(self, risk_profile: str) -> List[str]:
        """Get strategy suggestions based on risk profile"""
        strategies = {
            'Conservative': [
                "Focus on large-cap funds and debt instruments",
                "Use SIP for rupee cost averaging",
                "Maintain 6-month emergency fund",
                "Consider FDs for short-term goals"
            ],
            'Balanced': [
                "Mix of equity and debt through balanced funds",
                "Use SIP for equity exposure",
                "Consider index funds for core holdings",
                "Rebalance annually"
            ],
            'Aggressive': [
                "Higher equity allocation (70-80%)",
                "Include mid and small-cap funds",
                "Consider direct equity for alpha",
                "Use options for hedging (if experienced)"
            ]
        }
        return strategies.get(risk_profile, strategies['Balanced'])
    
    def _calculate_confidence(self, asset_scores: Dict) -> float:
        """Calculate confidence score for recommendations"""
        try:
            all_scores = []
            
            # Collect all aggregate scores
            for stock_data in asset_scores.get('stocks', {}).values():
                all_scores.append(stock_data['aggregate_score'])
            
            for mf_score in asset_scores.get('mutual_funds', {}).values():
                all_scores.append(mf_score)
            
            if not all_scores:
                return 0.5
            
            # Higher average score = higher confidence
            avg_score = sum(all_scores) / len(all_scores)
            
            # Penalize high variance (uncertainty)
            variance = sum((s - avg_score) ** 2 for s in all_scores) / len(all_scores)
            confidence = avg_score * (1 - min(variance, 0.3))
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _generate_summary(self, risk_profile: dict, expense_analysis: dict, 
                         portfolio: dict) -> str:
        """Generate enhanced summary of the investment plan"""
        summary = f"""
Investment Plan Summary
{'=' * 50}

PROFILE CLASSIFICATION
Risk Profile: {risk_profile['risk_profile']}
Risk Score: {risk_profile.get('risk_score', 0):.2f}/10

FINANCIAL CAPACITY
Monthly Investment: ₹{expense_analysis['disposable_income']:,.2f}
Savings Rate: {expense_analysis['savings_rate']:.1f}%

RECOMMENDED ALLOCATION
"""
        
        allocation = portfolio.get('allocation', {})
        for asset, amount in allocation.items():
            percentage = (amount / portfolio.get('total_amount', 1)) * 100
            summary += f"• {asset}: ₹{amount:,.2f} ({percentage:.1f}%)\n"
        
        summary += f"\nTotal Investment: ₹{portfolio.get('total_amount', 0):,.2f}\n"
        
        return summary
    
    def get_market_data(self) -> dict:
        """Fetch enhanced market data"""
        try:
            market_data = self._collect_market_data()
            
            return {
                "nifty_50": market_data.get('nifty_data', {}).get('close', 0),
                "gold_price": self.tools.get_gold_price(),
                "market_sentiment": market_data.get('sentiment', 'Neutral'),
                "macro_indicators": market_data.get('macro_indicators', {}),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def cleanup(self):
        """Cleanup resources"""
        if self.use_ray and ray.is_initialized():
            ray.shutdown()

# Test functionality
if __name__ == "__main__":
    agent = InvestmentAgent(use_ray=False)
    
    # Sample user data
    sample_data = {
        "age": 30,
        "income": 75000,
        "expenses": 45000,
        "savings": 200000,
        "horizon": 15,
        "risk_tolerance": "Medium"
    }
    
    result = agent.analyze_profile(sample_data)
    print("Enhanced Investment Analysis Result:")
    print(json.dumps(result, indent=2, default=str))
    
    agent.cleanup()