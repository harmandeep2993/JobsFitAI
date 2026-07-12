# tests/test_matcher.py
"""
Unit tests for the deterministic matcher: alias resolution, full-resume
evidence search, graded skill credit, similarity calibration, and the
None-sentinel handling for sections the JD says nothing about.

These tests load the local embedding model (a few seconds on first import)
but make no network or LLM calls.
"""

from services.matcher import engine
from services.matcher.skill_aliases import (
    build_evidence_corpus,
    found_in_corpus,
    normalize_skill,
)
from services.matcher.scores.skills import score_required_skills
from services.matcher.scores.certifications import score_certifications
from services.matcher.scores.responsibilities import score_responsibilities
from services.matcher.scoring_utils import calibrate_similarity


RESUME = {
    "skills": ["Python", "k8s", "Power BI"],
    "experience_entries": [
        {
            "title": "Data Analyst",
            "company": "Acme GmbH",
            "responsibilities": [
                "Deployed ML models with Docker on AWS",
                "Built SQL dashboards for management reporting",
            ],
        }
    ],
    "projects": [],
    "education": [{"degree": "BSc", "field": "Computer Science"}],
    "languages": [],
    "certifications": [],
}


def test_alias_normalization():
    assert normalize_skill("K8s") == "kubernetes"
    assert normalize_skill(" JS ") == "javascript"
    assert normalize_skill("Machine Learning") == "machine learning"
    assert normalize_skill("PostgreSQL") == "postgresql"


def test_evidence_corpus_finds_buried_skills():
    corpus = build_evidence_corpus(RESUME)
    # In a bullet, not in the skills list
    assert found_in_corpus("docker", corpus)
    assert found_in_corpus("aws", corpus)
    # 'java' must not match inside 'javascript'-like tokens or random text
    assert not found_in_corpus("java", corpus)
    # Ambiguous one-letter skills never match free text
    assert not found_in_corpus("r", corpus)


def test_required_skills_alias_and_evidence():
    jd = {"required_skills": ["Kubernetes", "Docker", "Python", "SQL"]}
    score, matched, partial, missing = score_required_skills(RESUME, jd)
    # kubernetes via alias (k8s), docker+sql via evidence bullets, python direct
    assert "kubernetes" in matched
    assert "docker" in matched
    assert "python" in matched
    assert "sql" in matched
    assert missing == []
    assert score == 100.0


def test_required_skills_unrelated_stays_missing():
    jd = {"required_skills": ["terraform", "react"]}
    score, matched, partial, missing = score_required_skills(RESUME, jd)
    assert "react" in missing
    assert "terraform" not in matched
    assert score < 60


def test_no_required_skills_returns_none():
    score, matched, partial, missing = score_required_skills(RESUME, {})
    assert score is None
    assert matched == [] and partial == [] and missing == []


def test_calibration_band():
    assert calibrate_similarity(0.20) == 0.0
    assert calibrate_similarity(0.35) == 0.0
    assert calibrate_similarity(0.55) == 50.0
    assert calibrate_similarity(0.75) == 100.0
    assert calibrate_similarity(0.95) == 100.0


def test_responsibilities_calibrated_not_capped():
    # A near-identical bullet pair must score close to 100, not ~cosine*100
    jd = {"responsibilities": ["Deploy machine learning models with Docker on AWS"]}
    score = score_responsibilities(RESUME, jd)
    assert score is not None
    assert score > 85, f"near-identical bullets scored only {score}"


def test_responsibilities_none_when_jd_empty():
    assert score_responsibilities(RESUME, {"responsibilities": []}) is None


def test_certifications_none_when_jd_empty():
    assert score_certifications(RESUME, {}) is None


def test_engine_excludes_none_sections_but_keeps_real_sixty(monkeypatch):
    """None sections are excluded from the overall; a legitimate 60.0 is not."""
    monkeypatch.setattr(
        engine, "score_required_skills", lambda r, j: (90.0, ["python"], [], [])
    )
    monkeypatch.setattr(
        engine, "score_preferred_skills", lambda r, j: (None, [], [], [])
    )
    monkeypatch.setattr(engine, "score_responsibilities", lambda r, j: 60.0)
    monkeypatch.setattr(engine, "score_experience", lambda r, j: None)
    monkeypatch.setattr(engine, "score_education", lambda r, j: None)
    monkeypatch.setattr(engine, "score_languages", lambda r, j: (None, [], []))
    monkeypatch.setattr(engine, "score_certifications", lambda r, j: None)

    result = engine.match({"skills": ["python"]}, {"required_skills": ["python"]})

    assert result["section_scores"]["preferred_skills"] is None
    assert result["section_scores"]["responsibilities"] == 60.0
    # Weighted mean of required_skills (0.28 * 90) and responsibilities
    # (0.28 * 60) over their combined weight = 75. The old ==60 sentinel
    # would have dropped responsibilities and returned 90.
    assert result["overall_score"] == 75.0


def test_engine_reports_partial_lists(monkeypatch):
    monkeypatch.setattr(
        engine,
        "score_required_skills",
        lambda r, j: (75.0, ["python"], ["tensorflow"], ["terraform"]),
    )
    monkeypatch.setattr(
        engine, "score_preferred_skills", lambda r, j: (None, [], [], [])
    )
    monkeypatch.setattr(engine, "score_responsibilities", lambda r, j: None)
    monkeypatch.setattr(engine, "score_experience", lambda r, j: None)
    monkeypatch.setattr(engine, "score_education", lambda r, j: None)
    monkeypatch.setattr(engine, "score_languages", lambda r, j: (None, [], []))
    monkeypatch.setattr(engine, "score_certifications", lambda r, j: None)

    result = engine.match({"skills": ["python"]}, {"required_skills": ["python"]})
    assert result["partial_required"] == ["tensorflow"]
    assert result["missing_required"] == ["terraform"]
