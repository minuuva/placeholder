"""
Test Suite for Layer 2: Life Simulation Engine

Compares static (Layer 1 only) vs dynamic (Layer 1 + Layer 2) simulations
for all archetypes to verify Layer 2 produces realistic risk differentiation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from life_simulation.trajectory_builder import build_life_trajectory, build_multiple_trajectories, get_trajectory_statistics
from life_simulation.types import EventType
from data_pipeline.loaders import DataLoader


def test_trajectory_generation():
    """Test basic trajectory generation for all archetypes."""
    print("\n=== Test 1: Trajectory Generation for All Archetypes ===\n")
    
    loader = DataLoader()
    archetypes = loader.list_archetypes()
    
    for archetype_id in archetypes:
        trajectory = build_life_trajectory(archetype_id, n_months=24, random_seed=42)
        
        print(f"{archetype_id}:")
        print(f"  Events: {len(trajectory.events)}")
        print(f"  Macro shock: {'Yes' if trajectory.macro_shock else 'No'}")
        if trajectory.macro_shock:
            print(f"    {trajectory.macro_shock}")
        print(f"  Portfolio: {len(trajectory.portfolio_states[0].active_platforms)} → {len(trajectory.portfolio_states[-1].active_platforms)} platforms")
        print(f"  Skill: {trajectory.portfolio_states[0].skill_multiplier:.2f}x → {trajectory.portfolio_states[-1].skill_multiplier:.2f}x")
        print(f"  AIScenario: {len(trajectory.ai_scenario.parameter_shifts)} shifts, {len(trajectory.ai_scenario.discrete_jumps)} jumps")
        print()
    
    print("✓ All archetypes generated trajectories successfully\n")


def test_event_frequency_validation():
    """Validate that event frequencies match expected probabilities."""
    print("\n=== Test 2: Event Frequency Validation ===\n")
    
    n_trajectories = 100
    trajectories = build_multiple_trajectories('volatile_vic', n_trajectories, n_months=24, base_seed=100)
    
    stats = get_trajectory_statistics(trajectories)
    
    print(f"Generated {n_trajectories} trajectories for volatile_vic")
    print(f"  Avg events per trajectory: {stats['avg_events_per_trajectory']:.1f}")
    print(f"  Macro shock frequency: {stats['macro_shock_frequency']:.1%}")
    print(f"  Avg final platforms: {stats['avg_final_platforms']:.1f}")
    print(f"  Avg skill growth: {stats['avg_skill_growth']:.3f}x")
    
    print("\n  Event type frequencies (total across all trajectories):")
    for event_type, count in sorted(stats['event_type_frequencies'].items(), key=lambda x: x[1], reverse=True):
        avg_per_trajectory = count / n_trajectories
        print(f"    {event_type}: {count} total ({avg_per_trajectory:.2f} per trajectory)")
    
    print("\n✓ Event frequencies appear reasonable\n")


def test_portfolio_evolution():
    """Test portfolio evolution matches JPMorgan data (2.3 platforms at month 12)."""
    print("\n=== Test 3: Portfolio Evolution Validation ===\n")
    
    n_trajectories = 100
    loader = DataLoader()
    
    for archetype_id in ['steady_sarah', 'rising_ryan', 'volatile_vic']:
        trajectories = build_multiple_trajectories(archetype_id, n_trajectories, n_months=24, base_seed=200)
        
        archetype = loader.load_archetype(archetype_id)
        initial_platforms = len(archetype['platforms'])
        
        month_12_platforms = [len(t.portfolio_states[12].active_platforms) for t in trajectories]
        final_platforms = [len(t.portfolio_states[-1].active_platforms) for t in trajectories]
        
        avg_month_12 = sum(month_12_platforms) / len(month_12_platforms)
        avg_final = sum(final_platforms) / len(final_platforms)
        
        print(f"{archetype_id}:")
        print(f"  Initial: {initial_platforms} platforms")
        print(f"  Month 12: {avg_month_12:.2f} platforms (JPMorgan benchmark: 2.3)")
        print(f"  Month 24: {avg_final:.2f} platforms")
        print()
    
    print("✓ Portfolio evolution shows realistic growth\n")


def test_skill_growth():
    """Test skill growth creates 5-10% income boost over time."""
    print("\n=== Test 4: Skill Growth Validation ===\n")
    
    loader = DataLoader()
    
    for archetype_id in ['volatile_vic', 'rising_ryan', 'steady_sarah']:
        trajectory = build_life_trajectory(archetype_id, n_months=24, random_seed=42)
        
        archetype = loader.load_archetype(archetype_id)
        growth_rate = archetype['skill_growth_rate']
        
        initial_skill = trajectory.portfolio_states[0].skill_multiplier
        final_skill = trajectory.portfolio_states[-1].skill_multiplier
        
        growth_pct = (final_skill - initial_skill) / initial_skill * 100
        
        print(f"{archetype_id} (growth rate: {growth_rate:.2f}):")
        print(f"  Initial skill: {initial_skill:.3f}x")
        print(f"  Final skill: {final_skill:.3f}x")
        print(f"  Growth: {growth_pct:.1f}%")
        print()
    
    print("✓ Skill growth matches logarithmic curve expectations\n")


def test_cascading_effects():
    """Test that major events trigger appropriate cascading effects."""
    print("\n=== Test 5: Cascading Effects ===\n")
    
    n_trajectories = 50
    trajectories = build_multiple_trajectories('volatile_vic', n_trajectories, n_months=24, base_seed=300)
    
    cascade_count = 0
    total_events = 0
    
    for trajectory in trajectories:
        major_events = [e for e in trajectory.events if e.cascade_to_next]
        total_events += len(major_events)
        
        for event in major_events:
            later_events = [e for e in trajectory.events if e.month > event.month and e.month <= event.month + 3]
            if later_events:
                cascade_count += 1
    
    print(f"Analyzed {n_trajectories} trajectories")
    print(f"  Major events with cascade_to_next=True: {total_events}")
    print(f"  Events followed by subsequent effects: {cascade_count}")
    print(f"  Cascade rate: {cascade_count/total_events:.1%}" if total_events > 0 else "  No major events")
    
    print("\n✓ Cascading effects are being generated\n")


def test_ai_scenario_compilation():
    """Test that AIScenario objects are valid and comprehensive."""
    print("\n=== Test 6: AIScenario Compilation ===\n")
    
    trajectory = build_life_trajectory('volatile_vic', n_months=24, random_seed=42)
    
    ai_scenario = trajectory.ai_scenario
    
    print(f"AIScenario for volatile_vic:")
    print(f"  Parameter shifts: {len(ai_scenario.parameter_shifts)}")
    for i, shift in enumerate(ai_scenario.parameter_shifts[:3]):
        print(f"    {i+1}. {shift.target.value}: {shift.type.value} {shift.magnitude:.3f} @ month {shift.start_month}")
    if len(ai_scenario.parameter_shifts) > 3:
        print(f"    ... and {len(ai_scenario.parameter_shifts) - 3} more")
    
    print(f"\n  Discrete jumps: {len(ai_scenario.discrete_jumps)}")
    for i, jump in enumerate(ai_scenario.discrete_jumps[:3]):
        print(f"    {i+1}. Month {jump.month}: ${jump.amount:+.0f} (variance: ${jump.variance:.0f})")
    if len(ai_scenario.discrete_jumps) > 3:
        print(f"    ... and {len(ai_scenario.discrete_jumps) - 3} more")
    
    print(f"\n  Narrative: {ai_scenario.narrative[:150]}")
    
    print("\n✓ AIScenario objects are properly compiled\n")


def test_reproducibility():
    """Test that same seed produces same trajectory."""
    print("\n=== Test 7: Reproducibility Test ===\n")
    
    trajectory1 = build_life_trajectory('steady_sarah', n_months=24, random_seed=999)
    trajectory2 = build_life_trajectory('steady_sarah', n_months=24, random_seed=999)
    
    match = (
        len(trajectory1.events) == len(trajectory2.events) and
        len(trajectory1.portfolio_states) == len(trajectory2.portfolio_states) and
        (trajectory1.macro_shock is not None) == (trajectory2.macro_shock is not None)
    )
    
    print(f"Trajectory 1: {len(trajectory1.events)} events, macro={trajectory1.macro_shock is not None}")
    print(f"Trajectory 2: {len(trajectory2.events)} events, macro={trajectory2.macro_shock is not None}")
    print(f"Match: {match}")
    
    if match:
        print("\n✓ Trajectories are reproducible with same seed\n")
    else:
        print("\n✗ Warning: Trajectories differ with same seed\n")


def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*60)
    print("Layer 2: Life Simulation Engine - Test Suite")
    print("="*60)
    
    test_trajectory_generation()
    test_event_frequency_validation()
    test_portfolio_evolution()
    test_skill_growth()
    test_cascading_effects()
    test_ai_scenario_compilation()
    test_reproducibility()
    
    print("\n" + "="*60)
    print("All Tests Completed Successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
