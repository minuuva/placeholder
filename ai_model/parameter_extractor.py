"""
Parameter Extractor - Converts natural language queries to simulation parameters.

Uses LLM to parse user intent and extract structured parameters.
"""

from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass

from .llm_client import LLMClient
from .config import Config


@dataclass
class SimulationRequest:
    """Structured simulation request extracted from natural language."""
    
    mode: str
    scenario: dict
    scenario_b: Optional[dict] = None
    extraction_notes: str = ""
    
    def is_comparison(self) -> bool:
        """Check if this is a comparison request."""
        return self.mode == "compare" and self.scenario_b is not None
    
    def get_time_horizon(self) -> int:
        """Get time horizon for scenario."""
        return self.scenario.get("time_horizon_months", Config.DEFAULT_TIME_HORIZON_MONTHS)
    
    def get_n_paths(self) -> int:
        """Get number of Monte Carlo paths."""
        return self.scenario.get("n_paths", Config.DEFAULT_N_PATHS)


class ParameterExtractor:
    """Extracts simulation parameters from natural language queries."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize parameter extractor.
        
        Args:
            llm_client: Optional LLM client (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()
        self.prompts_dir = Path(__file__).parent / "prompts"
    
    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from file."""
        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")
    
    def extract_parameters(self, query: str) -> SimulationRequest:
        """
        Extract simulation parameters from natural language query.
        
        Args:
            query: User's natural language query
        
        Returns:
            SimulationRequest with extracted parameters
        
        Raises:
            RuntimeError: If extraction fails
        
        Example:
            >>> extractor = ParameterExtractor()
            >>> req = extractor.extract_parameters(
            ...     "Show me a 5 year projection for a diversified worker"
            ... )
            >>> print(req.get_time_horizon())
            60
        """
        system_prompt = self._load_prompt("parameter_extraction.txt")
        
        user_prompt = f"Extract parameters from this query:\n\nQUERY: {query}"
        
        try:
            result = self.llm_client.generate_json(system_prompt, user_prompt, temperature=0.0)
            
            return SimulationRequest(
                mode=result.get("mode", "single"),
                scenario=result.get("scenario", {}),
                scenario_b=result.get("scenario_b"),
                extraction_notes=result.get("extraction_notes", "")
            )
        
        except Exception as e:
            print(f"Warning: LLM extraction failed ({e}), using fallback parser")
            return self._fallback_extraction(query)
    
    def _fallback_extraction(self, query: str) -> SimulationRequest:
        """
        Fallback rule-based extraction when LLM fails.
        
        Uses simple keyword matching for basic scenarios.
        """
        query_lower = query.lower()
        
        scenario = {
            "archetype_base": "steady_sarah",
            "time_horizon_months": Config.DEFAULT_TIME_HORIZON_MONTHS,
            "n_paths": Config.DEFAULT_N_PATHS,
            "loan_amount": 5000,
            "loan_term_months": 24,
            "loan_rate": 0.12,
            "forced_events": [],
            "scenario_description": query
        }
        
        if "5 year" in query_lower or "60 month" in query_lower:
            scenario["time_horizon_months"] = 60
        elif "3 year" in query_lower or "36 month" in query_lower:
            scenario["time_horizon_months"] = 36
        elif "2 year" in query_lower or "24 month" in query_lower:
            scenario["time_horizon_months"] = 24
        
        if "diversif" in query_lower or "multiple platform" in query_lower:
            scenario["archetype_base"] = "steady_sarah"
        elif "skill" in query_lower and "growth" in query_lower:
            scenario["archetype_base"] = "rising_ryan"
        elif "volatile" in query_lower or "high risk" in query_lower:
            scenario["archetype_base"] = "volatile_vic"
        elif "part time" in query_lower or "weekend" in query_lower:
            scenario["archetype_base"] = "weekend_warrior"
        
        if "recession" in query_lower:
            scenario["forced_events"].append({
                "type": "recession_2008",
                "start_month": 12
            })
        elif "gas" in query_lower and ("spike" in query_lower or "price" in query_lower):
            scenario["forced_events"].append({
                "type": "gas_spike_moderate",
                "start_month": 6
            })
        
        if "drawdown" in query_lower or "shock" in query_lower:
            if not scenario["forced_events"]:
                scenario["forced_events"].append({
                    "type": "recession_2020",
                    "start_month": 12
                })
        
        mode = "compare" if "compar" in query_lower or " vs " in query_lower else "single"
        
        scenario_b = None
        if mode == "compare":
            scenario_b = scenario.copy()
            if "diversif" in query_lower:
                scenario["archetype_base"] = "rising_ryan"
                scenario_b["archetype_base"] = "volatile_vic"
            elif "skill" in query_lower:
                scenario["archetype_base"] = "rising_ryan"
                scenario_b["archetype_base"] = "steady_sarah"
        
        return SimulationRequest(
            mode=mode,
            scenario=scenario,
            scenario_b=scenario_b,
            extraction_notes="Fallback rule-based extraction (LLM unavailable)"
        )
    
    def extract_with_context(
        self,
        query: str,
        user_data: Optional[dict] = None,
        loan_preferences: Optional[dict] = None
    ) -> SimulationRequest:
        """
        Extract parameters with additional context.
        
        Args:
            query: Natural language query
            user_data: Optional user financial data
            loan_preferences: Optional loan preferences
        
        Returns:
            SimulationRequest with context-enriched parameters
        """
        request = self.extract_parameters(query)
        
        if user_data:
            if "platforms" in user_data:
                request.scenario["custom_params"] = request.scenario.get("custom_params", {})
                request.scenario["custom_params"]["platforms"] = user_data["platforms"]
            
            if "monthly_income_estimate" in user_data:
                income = user_data["monthly_income_estimate"]
                request.scenario["custom_params"] = request.scenario.get("custom_params", {})
                request.scenario["custom_params"]["monthly_income"] = income
        
        if loan_preferences:
            if "amount" in loan_preferences:
                request.scenario["loan_amount"] = loan_preferences["amount"]
            if "term_months" in loan_preferences:
                request.scenario["loan_term_months"] = loan_preferences["term_months"]
            if "max_rate" in loan_preferences:
                request.scenario["loan_rate"] = loan_preferences["max_rate"]
        
        return request


def extract_parameters_from_query(query: str) -> SimulationRequest:
    """
    Convenience function to extract parameters from a query.
    
    Args:
        query: Natural language query
    
    Returns:
        SimulationRequest
    """
    extractor = ParameterExtractor()
    return extractor.extract_parameters(query)
