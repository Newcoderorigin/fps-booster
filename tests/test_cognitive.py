from fps_booster.cognitive import CognitiveCoach, PracticeRecommendation, SessionMetrics


def test_cognitive_coach_baseline_prompt():
    coach = CognitiveCoach()
    recommendation = coach.recommend_practice()
    assert recommendation.focus_area == "baseline"
    assert recommendation.drill_duration == 5


def test_cognitive_coach_focus_selection():
    coach = CognitiveCoach(history=3)
    coach.record_session(SessionMetrics(reaction_time=0.4, accuracy=0.7, stress_index=0.3))
    coach.record_session(SessionMetrics(reaction_time=0.42, accuracy=0.6, stress_index=0.4))
    recommendation = coach.recommend_practice()
    assert isinstance(recommendation, PracticeRecommendation)
    assert recommendation.focus_area == "reflex"
    assert "Time-slice" in recommendation.prompt
