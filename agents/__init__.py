# agents/__init__.py
"""
Multi-Agent Investment Advisor System

This package contains specialized agents for investment analysis and recommendation.

Architecture Layers:
- Layer 1 & 3: User Intelligence (user_agents.py)
- Layer 2: Data Ingestion (data_agents.py)
- Layer 4: Analytical Scoring (analytical_agents.py)
- Layer 6: Portfolio Construction (portfolio_agents.py)
"""

from .data_agents import (
    StockDataAgent,
    MutualFundDataAgent,
    MacroeconomicAgent,
    NewsAgent
)

from .user_agents import (
    UserProfilingAgent,
    ExpenseTrackingAgent
)

from .analytical_agents import (
    ValuationAgent,
    MomentumAgent,
    QualityAgent,
    RiskAgent,
    MutualFundScoringAgent
)

from .portfolio_agents import (
    PortfolioConstructionAgent,
    MetaController,
    RebalancingAgent
)

__version__ = '2.0.0'
__author__ = 'AI Investment Advisor Team'

__all__ = [
    # Data Agents
    'StockDataAgent',
    'MutualFundDataAgent',
    'MacroeconomicAgent',
    'NewsAgent',
    
    # User Agents
    'UserProfilingAgent',
    'ExpenseTrackingAgent',
    
    # Analytical Agents
    'ValuationAgent',
    'MomentumAgent',
    'QualityAgent',
    'RiskAgent',
    'MutualFundScoringAgent',
    
    # Portfolio Agents
    'PortfolioConstructionAgent',
    'MetaController',
    'RebalancingAgent'
]

# Agent metadata for monitoring
AGENT_REGISTRY = {
    'data_collection': [
        'StockDataAgent',
        'MutualFundDataAgent',
        'MacroeconomicAgent',
        'NewsAgent'
    ],
    'user_intelligence': [
        'UserProfilingAgent',
        'ExpenseTrackingAgent'
    ],
    'analytical_scoring': [
        'ValuationAgent',
        'MomentumAgent',
        'QualityAgent',
        'RiskAgent',
        'MutualFundScoringAgent'
    ],
    'portfolio_construction': [
        'PortfolioConstructionAgent',
        'MetaController',
        'RebalancingAgent'
    ]
}

def get_agent_count():
    """Get total number of active agents"""
    return sum(len(agents) for agents in AGENT_REGISTRY.values())

def get_agents_by_layer(layer: str):
    """Get agents for a specific layer"""
    return AGENT_REGISTRY.get(layer, [])