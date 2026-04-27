"""Unit tests for the scoring engine.

These don't touch Postgres or Ollama — they test the pure-Python signal -> score logic.
"""
from app.schemas import ScoringSignals
from app.services.scoring import _component_scores, _overall


def test_all_signals_true_yields_high_overall():
    signals = ScoringSignals(
        sample_size_mentioned=True,
        variables_defined=True,
        method_clear=True,
        controls_present=True,
        limitations_discussed=True,
        data_available=True,
        reproducible_steps=True,
        funding_or_conflicts_mentioned=True,
        statistical_results_present=True,
        direct_evidence_present=True,
    )
    components = _component_scores(signals)
    assert components["methodological_rigor"] == 100
    assert components["evidence_strength"] == 100
    assert components["reproducibility"] == 100
    assert components["clarity"] == 100
    assert components["bias_risk"] == 0
    assert _overall(components) == 100


def test_all_signals_false_yields_low_overall():
    signals = ScoringSignals()
    components = _component_scores(signals)
    assert components["methodological_rigor"] == 0
    assert components["evidence_strength"] == 0
    assert components["reproducibility"] == 0
    assert components["clarity"] == 0
    assert components["bias_risk"] == 100
    # bias_risk inverted then weighted at 0.10 -> 0
    assert _overall(components) == 0


def test_partial_signals_intermediate_score():
    signals = ScoringSignals(
        variables_defined=True,
        method_clear=True,
        statistical_results_present=True,
        direct_evidence_present=True,
        limitations_discussed=True,
    )
    components = _component_scores(signals)
    overall = _overall(components)
    assert 30 <= overall <= 80, overall
