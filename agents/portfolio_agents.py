# agents/portfolio_agents.py - Layer 6: Portfolio Construction & Control
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class PortfolioConstructionAgent:
    """Agent 17: Portfolio Construction"""
    
    def __init__(self):
        self.min_allocation = 0.05  # Minimum 5% per asset
        self.max_single_stock = 0.15  # Maximum 15% in single stock
    
    def construct(self, user_profile: Dict, asset_scores: Dict, 
                  investment_amount: float) -> Dict:
        """Construct optimized portfolio"""
        try:
            risk_profile = user_profile['risk_profile']
            
            # Get strategic asset allocation
            strategic_allocation = self._get_strategic_allocation(risk_profile)
            
            # Allocate to asset classes
            allocation = {}
            for asset_class, percentage in strategic_allocation.items():
                allocation[asset_class] = investment_amount * (percentage / 100)
            
            # Select specific instruments
            selected_instruments = self._select_instruments(
                asset_scores, 
                allocation,
                risk_profile
            )
            
            # Construct final portfolio
            portfolio = {
                'allocation': allocation,
                'strategic_percentages': strategic_allocation,
                'instruments': selected_instruments,
                'total_amount': investment_amount,
                'risk_profile': risk_profile,
                'expected_return': self._estimate_return(strategic_allocation),
                'expected_risk': self._estimate_risk(strategic_allocation),
                'diversification_score': self._calculate_diversification(allocation)
            }
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error constructing portfolio: {e}")
            return {}
    
    def _get_strategic_allocation(self, risk_profile: str) -> Dict:
        """Get strategic asset allocation based on risk profile"""
        allocations = {
            'Conservative': {
                'Equity': 30,
                'Debt': 50,
                'Gold': 15,
                'Cash': 5
            },
            'Balanced': {
                'Equity': 50,
                'Debt': 35,
                'Gold': 10,
                'Cash': 5
            },
            'Aggressive': {
                'Equity': 70,
                'Debt': 20,
                'Gold': 5,
                'Cash': 5
            }
        }
        return allocations.get(risk_profile, allocations['Balanced'])
    
    def _select_instruments(self, asset_scores: Dict, allocation: Dict,
                           risk_profile: str) -> Dict:
        """Select specific instruments for each asset class"""
        instruments = {
            'stocks': [],
            'mutual_funds': [],
            'etfs': [],
            'debt': []
        }
        
        try:
            # Select top stocks based on scores
            stock_scores = asset_scores.get('stocks', {})
            sorted_stocks = sorted(
                stock_scores.items(),
                key=lambda x: x[1]['aggregate_score'],
                reverse=True
            )
            
            equity_amount = allocation.get('Equity', 0)
            
            # Allocate to top 5-7 stocks
            num_stocks = 5 if risk_profile == 'Conservative' else 7
            top_stocks = sorted_stocks[:num_stocks]
            
            if top_stocks:
                amount_per_stock = equity_amount * 0.6 / len(top_stocks)  # 60% in stocks
                for symbol, data in top_stocks:
                    instruments['stocks'].append({
                        'symbol': symbol,
                        'amount': amount_per_stock,
                        'score': data['aggregate_score']
                    })
            
            # Allocate remaining equity to mutual funds
            mf_scores = asset_scores.get('mutual_funds', {})
            sorted_mfs = sorted(mf_scores.items(), key=lambda x: x[1], reverse=True)
            
            num_mfs = 3
            top_mfs = sorted_mfs[:num_mfs]
            
            if top_mfs:
                amount_per_mf = equity_amount * 0.4 / len(top_mfs)  # 40% in MFs
                for code, score in top_mfs:
                    instruments['mutual_funds'].append({
                        'code': code,
                        'amount': amount_per_mf,
                        'score': score
                    })
            
            # Debt allocation
            debt_amount = allocation.get('Debt', 0)
            if debt_amount > 0:
                instruments['debt'].append({
                    'type': 'Debt Mutual Funds',
                    'amount': debt_amount * 0.6,
                    'recommendation': 'HDFC Corporate Bond Fund'
                })
                instruments['debt'].append({
                    'type': 'Fixed Deposits',
                    'amount': debt_amount * 0.4,
                    'recommendation': 'Bank FDs'
                })
            
            # Gold allocation
            gold_amount = allocation.get('Gold', 0)
            if gold_amount > 0:
                instruments['etfs'].append({
                    'type': 'Gold ETF',
                    'symbol': 'GOLDBEES.NS',
                    'amount': gold_amount,
                    'recommendation': 'HDFC Gold ETF'
                })
            
            return instruments
            
        except Exception as e:
            logger.error(f"Error selecting instruments: {e}")
            return instruments
    
    def _estimate_return(self, allocation: Dict) -> float:
        """Estimate expected portfolio return"""
        # Expected returns by asset class (annualized %)
        expected_returns = {
            'Equity': 12.0,
            'Debt': 7.0,
            'Gold': 8.0,
            'Cash': 4.0
        }
        
        weighted_return = sum(
            allocation.get(asset, 0) * expected_returns.get(asset, 0) / 100
            for asset in allocation
        )
        
        return weighted_return
    
    def _estimate_risk(self, allocation: Dict) -> float:
        """Estimate portfolio risk (standard deviation)"""
        # Risk (std dev) by asset class
        asset_risks = {
            'Equity': 18.0,
            'Debt': 5.0,
            'Gold': 12.0,
            'Cash': 1.0
        }
        
        # Simplified risk calculation (ignoring correlations)
        weighted_risk = sum(
            (allocation.get(asset, 0) / 100) ** 2 * asset_risks.get(asset, 0) ** 2
            for asset in allocation
        ) ** 0.5
        
        return weighted_risk
    
    def _calculate_diversification(self, allocation: Dict) -> float:
        """Calculate diversification score (0-1)"""
        try:
            # Use entropy as diversification measure
            total = sum(allocation.values())
            if total == 0:
                return 0
            
            proportions = [v / total for v in allocation.values()]
            entropy = -sum(p * (p ** 0.5) for p in proportions if p > 0)
            
            # Normalize (max entropy for 4 assets = 2)
            normalized_entropy = min(entropy / 2, 1)
            
            return normalized_entropy
            
        except:
            return 0.5


class MetaController:
    """Agent 16: Meta-Controller for ensemble and conflict resolution"""
    
    def __init__(self):
        self.validation_rules = []
    
    def validate_and_adjust(self, portfolio: Dict, user_profile: Dict) -> Dict:
        """Validate portfolio and make adjustments"""
        try:
            # Validation checks
            issues = []
            
            # Check 1: Allocation sums to 100%
            allocation = portfolio.get('allocation', {})
            total_pct = sum(portfolio.get('strategic_percentages', {}).values())
            if abs(total_pct - 100) > 1:
                issues.append(f"Allocation doesn't sum to 100% ({total_pct}%)")
            
            # Check 2: Risk alignment
            risk_profile = user_profile['risk_profile']
            equity_pct = portfolio.get('strategic_percentages', {}).get('Equity', 0)
            
            if risk_profile == 'Conservative' and equity_pct > 40:
                issues.append("Equity allocation too high for Conservative profile")
                # Adjust
                portfolio = self._rebalance_for_risk(portfolio, 'Conservative')
            
            elif risk_profile == 'Aggressive' and equity_pct < 60:
                issues.append("Equity allocation too low for Aggressive profile")
                portfolio = self._rebalance_for_risk(portfolio, 'Aggressive')
            
            # Check 3: Minimum diversification
            div_score = portfolio.get('diversification_score', 0)
            if div_score < 0.3:
                issues.append("Insufficient diversification")
            
            # Check 4: Emergency fund
            cash_amount = allocation.get('Cash', 0)
            monthly_income = user_profile.get('income', 0)
            if cash_amount < monthly_income * 3:
                issues.append("Consider building larger emergency fund")
            
            # Add validation report
            portfolio['validation'] = {
                'passed': len(issues) == 0,
                'issues': issues,
                'adjustments_made': len(issues) > 0
            }
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error in meta-controller: {e}")
            return portfolio
    
    def _rebalance_for_risk(self, portfolio: Dict, target_risk: str) -> Dict:
        """Rebalance portfolio to match risk profile"""
        try:
            # Get target allocation
            target_allocations = {
                'Conservative': {'Equity': 30, 'Debt': 50, 'Gold': 15, 'Cash': 5},
                'Balanced': {'Equity': 50, 'Debt': 35, 'Gold': 10, 'Cash': 5},
                'Aggressive': {'Equity': 70, 'Debt': 20, 'Gold': 5, 'Cash': 5}
            }
            
            target = target_allocations.get(target_risk, target_allocations['Balanced'])
            total_amount = portfolio.get('total_amount', 0)
            
            # Recalculate allocation
            new_allocation = {}
            for asset_class, percentage in target.items():
                new_allocation[asset_class] = total_amount * (percentage / 100)
            
            portfolio['allocation'] = new_allocation
            portfolio['strategic_percentages'] = target
            portfolio['expected_return'] = self._estimate_return(target)
            portfolio['expected_risk'] = self._estimate_risk(target)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio: {e}")
            return portfolio
    
    def _estimate_return(self, allocation: Dict) -> float:
        """Estimate expected return"""
        expected_returns = {
            'Equity': 12.0,
            'Debt': 7.0,
            'Gold': 8.0,
            'Cash': 4.0
        }
        return sum(allocation.get(asset, 0) * expected_returns.get(asset, 0) / 100
                   for asset in allocation)
    
    def _estimate_risk(self, allocation: Dict) -> float:
        """Estimate portfolio risk"""
        asset_risks = {
            'Equity': 18.0,
            'Debt': 5.0,
            'Gold': 12.0,
            'Cash': 1.0
        }
        return sum((allocation.get(asset, 0) / 100) ** 2 * asset_risks.get(asset, 0) ** 2
                   for asset in allocation) ** 0.5
    
    def resolve_conflicts(self, recommendations: List[Dict]) -> Dict:
        """Resolve conflicts between multiple agent recommendations"""
        try:
            # Weighted voting mechanism
            if not recommendations:
                return {}
            
            # Aggregate recommendations
            aggregated = {
                'assets': {},
                'confidence': 0
            }
            
            # Weight by confidence scores
            total_weight = sum(r.get('confidence', 0.5) for r in recommendations)
            
            for rec in recommendations:
                weight = rec.get('confidence', 0.5) / total_weight
                
                for asset, score in rec.get('assets', {}).items():
                    if asset not in aggregated['assets']:
                        aggregated['assets'][asset] = 0
                    aggregated['assets'][asset] += score * weight
            
            # Calculate aggregate confidence
            aggregated['confidence'] = sum(r.get('confidence', 0.5) for r in recommendations) / len(recommendations)
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error resolving conflicts: {e}")
            return {}


class RebalancingAgent:
    """Agent 14: Portfolio Rebalancing (RL-based in production)"""
    
    def __init__(self):
        self.drift_threshold = 0.10  # 10% drift triggers rebalancing
    
    def analyze_rebalancing_need(self, current_portfolio: Dict, 
                                 target_allocation: Dict) -> Dict:
        """Analyze if rebalancing is needed"""
        try:
            rebalancing_needed = False
            drifts = {}
            
            current_total = sum(current_portfolio.values())
            
            for asset_class, target_pct in target_allocation.items():
                current_amount = current_portfolio.get(asset_class, 0)
                current_pct = (current_amount / current_total * 100) if current_total > 0 else 0
                
                drift = abs(current_pct - target_pct)
                drifts[asset_class] = drift
                
                if drift > self.drift_threshold * 100:  # Convert to percentage
                    rebalancing_needed = True
            
            return {
                'rebalancing_needed': rebalancing_needed,
                'drifts': drifts,
                'max_drift': max(drifts.values()) if drifts else 0,
                'recommendation': self._generate_rebalancing_plan(
                    current_portfolio, target_allocation, drifts
                ) if rebalancing_needed else None
            }
            
        except Exception as e:
            logger.error(f"Error analyzing rebalancing: {e}")
            return {'rebalancing_needed': False}
    
    def _generate_rebalancing_plan(self, current: Dict, target: Dict, 
                                   drifts: Dict) -> Dict:
        """Generate specific rebalancing actions"""
        plan = {
            'sell': [],
            'buy': [],
            'estimated_cost': 0
        }
        
        try:
            current_total = sum(current.values())
            
            for asset_class, drift in drifts.items():
                if drift > self.drift_threshold * 100:
                    target_amount = current_total * (target[asset_class] / 100)
                    current_amount = current.get(asset_class, 0)
                    
                    difference = target_amount - current_amount
                    
                    if difference > 0:
                        plan['buy'].append({
                            'asset_class': asset_class,
                            'amount': difference,
                            'reason': f'{drift:.1f}% below target'
                        })
                    else:
                        plan['sell'].append({
                            'asset_class': asset_class,
                            'amount': abs(difference),
                            'reason': f'{drift:.1f}% above target'
                        })
            
            # Estimate transaction costs (0.1% for example)
            total_rebalancing = sum(item['amount'] for item in plan['buy'])
            plan['estimated_cost'] = total_rebalancing * 0.001
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating rebalancing plan: {e}")
            return plan