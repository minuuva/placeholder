"""
Result Summarizer - Generates natural language summaries of simulation results.

Uses LLM to create human-readable analysis of risk metrics and trajectories.
"""

from pathlib import Path
from typing import Optional
import numpy as np

from .llm_client import LLMClient
from .simulation_runner import SimulationOutput


class ResultSummarizer:
    """Generates AI-powered summaries of simulation results."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize result summarizer.
        
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
    
    def summarize(
        self,
        output: SimulationOutput,
        focus_areas: Optional[list[str]] = None,
        max_length: int = 500
    ) -> str:
        """
        Generate natural language summary of simulation results.
        
        Args:
            output: SimulationOutput from simulation
            focus_areas: Optional list of areas to emphasize
            max_length: Maximum words in summary
        
        Returns:
            Natural language summary
        
        Example:
            >>> summarizer = ResultSummarizer()
            >>> summary = summarizer.summarize(output, focus_areas=["risk_drivers"])
            >>> print(summary)
        """
        system_prompt = self._load_prompt("result_summary.txt")
        
        user_prompt = self._build_summarization_prompt(output, focus_areas, max_length)
        
        try:
            summary = self.llm_client.generate(
                system_prompt,
                user_prompt,
                temperature=0.3
            )
            return summary.strip()
        
        except Exception as e:
            print(f"Warning: LLM summarization failed ({e}), using fallback")
            return self._fallback_summary(output)
    
    def _build_summarization_prompt(
        self,
        output: SimulationOutput,
        focus_areas: Optional[list[str]],
        max_length: int
    ) -> str:
        """Build detailed prompt for result summarization."""
        
        trajectory = output.trajectory
        result = output.result
        archetype = output.archetype_used
        
        prompt_parts = []
        
        prompt_parts.append("SIMULATION RESULTS TO SUMMARIZE:")
        prompt_parts.append("")
        
        prompt_parts.append("ARCHETYPE PROFILE:")
        prompt_parts.append(f"  Name: {archetype['name']}")
        prompt_parts.append(f"  Base Income: ${archetype['base_mu']:,.2f}/month")
        prompt_parts.append(f"  Income Volatility (CV): {archetype['coefficient_of_variation']:.1%}")
        prompt_parts.append(f"  Platforms: {', '.join(archetype['platforms'])}")
        prompt_parts.append(f"  Emergency Fund: {archetype['emergency_fund_weeks']} weeks")
        prompt_parts.append(f"  Debt-to-Income: {archetype['debt_to_income_ratio']:.1%}")
        prompt_parts.append("")
        
        prompt_parts.append("RISK METRICS:")
        prompt_parts.append(f"  Default Probability: {result.p_default:.2%}")
        prompt_parts.append(f"  Expected Loss: ${result.expected_loss:,.2f}")
        prompt_parts.append(f"  CVaR 95% (tail risk): ${result.cvar_95:,.2f}")
        prompt_parts.append(f"  Risk Tier: {result.recommended_loan.risk_tier.value.upper()}")
        prompt_parts.append("")
        
        prompt_parts.append("LOAN RECOMMENDATION:")
        prompt_parts.append(f"  Decision: {'APPROVED' if result.recommended_loan.approved else 'DECLINED'}")
        prompt_parts.append(f"  Optimal Amount: ${result.recommended_loan.optimal_amount:,.0f}")
        prompt_parts.append(f"  Optimal Term: {result.recommended_loan.optimal_term_months} months")
        prompt_parts.append(f"  Optimal Rate: {result.recommended_loan.optimal_rate:.2%}")
        if result.recommended_loan.reasoning:
            prompt_parts.append("  Reasoning:")
            for reason in result.recommended_loan.reasoning[:3]:
                prompt_parts.append(f"    - {reason}")
        prompt_parts.append("")
        
        prompt_parts.append("TRAJECTORY SUMMARY:")
        prompt_parts.append(f"  Time Horizon: {trajectory.months} months")
        prompt_parts.append(f"  Life Events: {len(trajectory.events)}")
        
        if trajectory.events:
            major_events = [e for e in trajectory.events
                          if abs(e.income_impact) > 500 or abs(e.expense_impact) > 500]
            if major_events:
                prompt_parts.append(f"  Major Events ({len(major_events)}):")
                for event in major_events[:5]:
                    prompt_parts.append(f"    - Month {event.month}: {event.description}")
        
        if trajectory.portfolio_states:
            initial = trajectory.portfolio_states[0]
            final = trajectory.portfolio_states[-1]
            prompt_parts.append(f"  Platform Evolution: {len(initial.active_platforms)} -> {len(final.active_platforms)}")
            prompt_parts.append(f"  Skill Growth: {initial.skill_multiplier:.2f}x -> {final.skill_multiplier:.2f}x")
        
        if trajectory.macro_shock:
            prompt_parts.append(f"  Macro Shock: {trajectory.macro_shock.scenario_name} (month {trajectory.macro_shock.start_month})")
        
        prompt_parts.append("")
        prompt_parts.append(f"Trajectory Narrative: {trajectory.narrative}")
        prompt_parts.append("")
        
        prompt_parts.append("INCOME STATISTICS:")
        median_income = np.median(result.median_income_by_month)
        p10_income = np.median(result.p10_income_by_month)
        p90_income = np.median(result.p90_income_by_month)
        prompt_parts.append(f"  Median Monthly Income: ${median_income:,.2f}")
        prompt_parts.append(f"  10th Percentile (worst case): ${p10_income:,.2f}")
        prompt_parts.append(f"  90th Percentile (best case): ${p90_income:,.2f}")
        prompt_parts.append("")
        
        if focus_areas:
            prompt_parts.append(f"FOCUS AREAS: {', '.join(focus_areas)}")
            prompt_parts.append("")
        
        prompt_parts.append(f"TARGET LENGTH: Approximately {max_length} words")
        prompt_parts.append("")
        prompt_parts.append("Generate a professional summary following the structure in your system prompt.")
        
        return '\n'.join(prompt_parts)
    
    def _fallback_summary(self, output: SimulationOutput) -> str:
        """Generate rule-based summary when LLM is unavailable."""
        
        result = output.result
        trajectory = output.trajectory
        archetype = output.archetype_used
        
        lines = []
        
        lines.append(f"RISK ASSESSMENT SUMMARY: {archetype['name']}")
        lines.append("")
        
        if result.recommended_loan.approved:
            lines.append(
                f"This borrower is APPROVED with a {result.p_default:.1%} default probability "
                f"over {trajectory.months} months. "
            )
        else:
            lines.append(
                f"This borrower is DECLINED due to high default risk ({result.p_default:.1%}) "
                f"over {trajectory.months} months. "
            )
        
        lines.append("")
        lines.append("KEY METRICS:")
        lines.append(f"- Default Probability: {result.p_default:.2%}")
        lines.append(f"- Expected Loss: ${result.expected_loss:,.2f}")
        lines.append(f"- CVaR 95%: ${result.cvar_95:,.2f}")
        lines.append(f"- Risk Tier: {result.recommended_loan.risk_tier.value.upper()}")
        
        lines.append("")
        lines.append("RISK DRIVERS:")
        
        cv = archetype['coefficient_of_variation']
        if cv > 0.35:
            lines.append(f"- High income volatility (CV={cv:.1%})")
        
        if archetype['emergency_fund_weeks'] < 4:
            lines.append(f"- Limited emergency fund ({archetype['emergency_fund_weeks']} weeks)")
        
        if len(archetype['platforms']) == 1:
            lines.append("- Single platform concentration risk")
        
        if len(trajectory.events) > 8:
            lines.append(f"- Multiple adverse events ({len(trajectory.events)} total)")
        
        if trajectory.macro_shock:
            lines.append(f"- Macro shock: {trajectory.macro_shock.scenario_name}")
        
        lines.append("")
        
        if result.recommended_loan.approved:
            lines.append(
                f"RECOMMENDED TERMS: ${result.recommended_loan.optimal_amount:,.0f} "
                f"over {result.recommended_loan.optimal_term_months} months "
                f"at {result.recommended_loan.optimal_rate:.1%} APR."
            )
        else:
            lines.append(
                f"ALTERNATIVE: Consider smaller loan amount or longer term to reduce monthly payment burden."
            )
        
        return '\n'.join(lines)
    
    def summarize_comparison(
        self,
        output_a: SimulationOutput,
        output_b: SimulationOutput,
        scenario_a_description: str = "Scenario A",
        scenario_b_description: str = "Scenario B"
    ) -> str:
        """
        Generate comparative summary of two scenarios.
        
        Args:
            output_a: First scenario output
            output_b: Second scenario output
            scenario_a_description: Description of first scenario
            scenario_b_description: Description of second scenario
        
        Returns:
            Comparative summary text
        """
        prompt = self._build_comparison_prompt(
            output_a, output_b,
            scenario_a_description, scenario_b_description
        )
        
        system_prompt = (
            "You are a financial analyst comparing two risk assessment scenarios. "
            "Provide a clear comparison highlighting key differences in risk profiles, "
            "outcomes, and recommendations. Focus on which scenario is preferable and why."
        )
        
        try:
            summary = self.llm_client.generate(system_prompt, prompt, temperature=0.3)
            return summary.strip()
        except Exception as e:
            print(f"Warning: LLM comparison failed ({e}), using fallback")
            return self._fallback_comparison(output_a, output_b,
                                            scenario_a_description, scenario_b_description)
    
    def _build_comparison_prompt(
        self,
        output_a: SimulationOutput,
        output_b: SimulationOutput,
        desc_a: str,
        desc_b: str
    ) -> str:
        """Build comparison prompt."""
        
        lines = []
        lines.append(f"Compare these two scenarios:")
        lines.append("")
        
        lines.append(f"{desc_a}:")
        lines.append(f"  P(default): {output_a.result.p_default:.2%}")
        lines.append(f"  Expected Loss: ${output_a.result.expected_loss:,.2f}")
        lines.append(f"  Approved: {output_a.result.recommended_loan.approved}")
        lines.append(f"  Platforms: {len(output_a.trajectory.portfolio_states[0].active_platforms)} -> {len(output_a.trajectory.portfolio_states[-1].active_platforms)}")
        lines.append(f"  Events: {len(output_a.trajectory.events)}")
        lines.append("")
        
        lines.append(f"{desc_b}:")
        lines.append(f"  P(default): {output_b.result.p_default:.2%}")
        lines.append(f"  Expected Loss: ${output_b.result.expected_loss:,.2f}")
        lines.append(f"  Approved: {output_b.result.recommended_loan.approved}")
        lines.append(f"  Platforms: {len(output_b.trajectory.portfolio_states[0].active_platforms)} -> {len(output_b.trajectory.portfolio_states[-1].active_platforms)}")
        lines.append(f"  Events: {len(output_b.trajectory.events)}")
        lines.append("")
        
        delta_default = (output_b.result.p_default - output_a.result.p_default) * 100
        lines.append(f"Delta P(default): {delta_default:+.1f} percentage points")
        lines.append("")
        lines.append("Provide a 200-300 word comparison explaining which scenario is preferable and why.")
        
        return '\n'.join(lines)
    
    def _fallback_comparison(
        self,
        output_a: SimulationOutput,
        output_b: SimulationOutput,
        desc_a: str,
        desc_b: str
    ) -> str:
        """Fallback comparison when LLM unavailable."""
        
        lines = []
        
        lines.append(f"COMPARISON: {desc_a} vs {desc_b}")
        lines.append("")
        
        delta_default = output_b.result.p_default - output_a.result.p_default
        
        if abs(delta_default) < 0.05:
            lines.append("Both scenarios show similar default risk profiles.")
        elif delta_default < 0:
            lines.append(
                f"{desc_b} shows {abs(delta_default):.1%} lower default risk than {desc_a}."
            )
        else:
            lines.append(
                f"{desc_a} shows {abs(delta_default):.1%} lower default risk than {desc_b}."
            )
        
        lines.append("")
        
        if output_a.result.recommended_loan.approved and not output_b.result.recommended_loan.approved:
            lines.append(f"{desc_a} receives loan approval while {desc_b} is declined.")
        elif output_b.result.recommended_loan.approved and not output_a.result.recommended_loan.approved:
            lines.append(f"{desc_b} receives loan approval while {desc_a} is declined.")
        
        return '\n'.join(lines)
    
    def generate_quick_summary(self, output: SimulationOutput) -> str:
        """
        Generate ultra-concise summary (2-3 sentences).
        
        Args:
            output: SimulationOutput
        
        Returns:
            Short summary
        """
        result = output.result
        trajectory = output.trajectory
        archetype = output.archetype_used
        
        approval = "APPROVED" if result.recommended_loan.approved else "DECLINED"
        
        summary = (
            f"{archetype['name']}: {approval} with {result.p_default:.1%} default probability "
            f"over {trajectory.months} months. "
            f"Risk tier: {result.recommended_loan.risk_tier.value}. "
        )
        
        if result.recommended_loan.approved:
            summary += (
                f"Optimal structure: ${result.recommended_loan.optimal_amount:,.0f} "
                f"for {result.recommended_loan.optimal_term_months} months "
                f"at {result.recommended_loan.optimal_rate:.1%}."
            )
        else:
            summary += (
                f"Key concerns: high volatility (CV={archetype['coefficient_of_variation']:.0%}), "
                f"limited buffer ({archetype['emergency_fund_weeks']} weeks emergency fund)."
            )
        
        return summary


def summarize_simulation_results(output: SimulationOutput) -> str:
    """
    Convenience function to generate summary.
    
    Args:
        output: SimulationOutput
    
    Returns:
        Natural language summary
    """
    summarizer = ResultSummarizer()
    return summarizer.summarize(output)
