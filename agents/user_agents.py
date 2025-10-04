# agents/user_agents.py - Layer 1 & 3: User Intelligence Agents
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class UserProfilingAgent:
    """Agent 1: User Profile Analysis and Classification"""
    
    def __init__(self):
        self.profile_cache = {}
    
    def create_profile(self, age: int, income: float, horizon: int, 
                      risk_tolerance: str, savings: float) -> Dict:
        """Create comprehensive user profile"""
        try:
            # Calculate risk score (0-10 scale)
            risk_score = self._calculate_risk_score(age, horizon, risk_tolerance)
            
            # Determine risk profile
            risk_profile = self._classify_risk_profile(risk_score)
            
            # Calculate investment capacity
            life_stage = self._determine_life_stage(age)
            
            # Generate investment goals
            goals = self._suggest_goals(age, horizon, income)
            
            profile = {
                'age': age,
                'income': income,
                'horizon': horizon,
                'risk_tolerance': risk_tolerance,
                'savings': savings,
                'risk_score': risk_score,
                'risk_profile': risk_profile,
                'life_stage': life_stage,
                'suggested_goals': goals,
                'max_equity_allocation': self._max_equity_allocation(age, risk_score),
                'recommended_sip': income * 0.2,  # 20% of income
                'emergency_fund_target': income * 6,
                'timestamp': None
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return {}
    
    def _calculate_risk_score(self, age: int, horizon: int, 
                             risk_tolerance: str) -> float:
        """Calculate numerical risk score (0-10)"""
        score = 0.0
        
        # Age factor (younger = higher risk capacity)
        if age < 30:
            score += 3.5
        elif age < 40:
            score += 2.5
        elif age < 50:
            score += 1.5
        else:
            score += 0.5
        
        # Horizon factor
        if horizon > 15:
            score += 3.5
        elif horizon > 10:
            score += 2.5
        elif horizon > 5:
            score += 1.5
        else:
            score += 0.5
        
        # Risk tolerance factor
        tolerance_scores = {
            'Low': 1.0,
            'Medium': 2.0,
            'High': 3.0
        }
        score += tolerance_scores.get(risk_tolerance, 2.0)
        
        return min(score, 10.0)
    
    def _classify_risk_profile(self, risk_score: float) -> str:
        """Classify into risk category"""
        if risk_score >= 7.5:
            return "Aggressive"
        elif risk_score >= 4.5:
            return "Balanced"
        else:
            return "Conservative"
    
    def _determine_life_stage(self, age: int) -> str:
        """Determine life stage"""
        if age < 30:
            return "Early Career"
        elif age < 45:
            return "Mid Career"
        elif age < 60:
            return "Pre-Retirement"
        else:
            return "Retirement"
    
    def _suggest_goals(self, age: int, horizon: int, income: float) -> List[str]:
        """Suggest investment goals based on profile"""
        goals = []
        
        if age < 35:
            goals.extend([
                "Build emergency fund (6 months expenses)",
                "Start retirement corpus building",
                "Plan for home down payment"
            ])
        elif age < 50:
            goals.extend([
                "Children's education fund",
                "Accelerate retirement savings",
                "Plan for home upgrade/vacation property"
            ])
        else:
            goals.extend([
                "Maximize retirement corpus",
                "Create passive income streams",
                "Estate planning"
            ])
        
        if horizon > 10:
            goals.append("Long-term wealth creation")
        
        return goals
    
    def _max_equity_allocation(self, age: int, risk_score: float) -> float:
        """Calculate maximum recommended equity allocation"""
        # Rule: 100 - age, adjusted by risk score
        base_allocation = max(100 - age, 20)
        
        # Adjust based on risk score
        adjustment = (risk_score - 5) * 5  # +/- 25% max
        
        return min(max(base_allocation + adjustment, 20), 80)


class ExpenseTrackingAgent:
    """Agent 2: Expense Analysis and Cashflow Tracking"""
    
    def __init__(self):
        self.categories = [
            'Housing', 'Food', 'Transportation', 'Healthcare',
            'Insurance', 'Entertainment', 'Education', 'Others'
        ]
    
    def analyze_expenses(self, income: float, expenses: float) -> Dict:
        """Analyze expense patterns"""
        try:
            disposable_income = income - expenses
            savings_rate = (disposable_income / income * 100) if income > 0 else 0
            
            # Calculate expense ratios
            expense_ratio = (expenses / income * 100) if income > 0 else 0
            
            # Determine financial health
            health_status = self._assess_financial_health(savings_rate)
            
            # Provide recommendations
            recommendations = self._generate_expense_recommendations(
                savings_rate, expense_ratio
            )
            
            analysis = {
                'monthly_income': income,
                'monthly_expenses': expenses,
                'disposable_income': disposable_income,
                'savings_rate': savings_rate,
                'expense_ratio': expense_ratio,
                'financial_health': health_status,
                'recommendations': recommendations,
                'ideal_savings_rate': 30.0,  # Target
                'surplus_deficit': disposable_income,
                'message': f"You have ₹{disposable_income:,.2f} available for investments ({savings_rate:.1f}% savings rate)"
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing expenses: {e}")
            return {}
    
    def _assess_financial_health(self, savings_rate: float) -> str:
        """Assess financial health based on savings rate"""
        if savings_rate >= 30:
            return "Excellent"
        elif savings_rate >= 20:
            return "Good"
        elif savings_rate >= 10:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _generate_expense_recommendations(self, savings_rate: float, 
                                         expense_ratio: float) -> List[str]:
        """Generate expense management recommendations"""
        recommendations = []
        
        if savings_rate < 20:
            recommendations.append(
                "⚠️ Try to increase savings rate to at least 20% by reducing discretionary expenses"
            )
        
        if expense_ratio > 80:
            recommendations.append(
                "💡 High expense ratio detected. Review and categorize expenses to identify savings opportunities"
            )
        
        if savings_rate >= 30:
            recommendations.append(
                "✅ Excellent savings rate! Consider increasing investment contributions"
            )
        
        # General recommendations
        recommendations.extend([
            "📊 Use the 50-30-20 rule: 50% needs, 30% wants, 20% savings",
            "🏦 Build emergency fund covering 6 months of expenses",
            "📱 Track expenses regularly using budgeting apps"
        ])
        
        return recommendations
    
    def categorize_expense(self, description: str, amount: float) -> str:
        """Categorize an expense (placeholder for ML model)"""
        # In production: Use ML model to categorize expenses
        # For now, return 'Others'
        return 'Others'
    
    def calculate_monthly_surplus(self, income: float, fixed_expenses: float,
                                  variable_expenses: float) -> Dict:
        """Calculate detailed monthly surplus"""
        total_expenses = fixed_expenses + variable_expenses
        surplus = income - total_expenses
        
        return {
            'income': income,
            'fixed_expenses': fixed_expenses,
            'variable_expenses': variable_expenses,
            'total_expenses': total_expenses,
            'surplus': surplus,
            'surplus_percentage': (surplus / income * 100) if income > 0 else 0
        }