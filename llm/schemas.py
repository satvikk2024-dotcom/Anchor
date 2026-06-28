import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class CompleteRequest(BaseModel):
    prompt: str
    system: str | None = None
    system_prompt_name: str | None = None
    json_mode: bool = False
    model: str | None = None


class CompleteResponse(BaseModel):
    text: str
    model: str
    cached: bool


class SlackNotifyRequest(BaseModel):
    text: str


class SlackNotifyResponse(BaseModel):
    sent: bool


class LocationType(str, Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    unknown = "unknown"


class JDParserOutput(BaseModel):
    """Structured-output contract for the JD Parser agent (prompts/jd_parser.md)."""

    company_name: str
    role_title: str
    team_or_org: str | None = None
    must_haves: list[str] = []
    nice_to_haves: list[str] = []
    responsibilities: list[str] = []
    tech_stack: list[str] = []
    culture_signals: list[str] = []
    comp_range: str | None = None
    location_type: LocationType


class CompanyType(str, Enum):
    startup = "startup"
    enterprise = "enterprise"
    unknown = "unknown"


class CompanySynthesizerOutput(BaseModel):
    """Structured-output contract for the Company Synthesizer agent (prompts/company_synthesizer.md)."""

    what_they_do: str
    recent_developments: list[str] = []
    tech_signals: list[str] = []
    company_type: CompanyType
    culture_signals: list[str] = []
    likely_role_context: str


class ResumeCriticOutput(BaseModel):
    """Structured-output contract for the Resume Critic agent (prompts/resume_critic.md)."""

    strengths_for_this_role: list[str] = []
    weaknesses_to_address: list[str] = []
    gaps_unfixable_in_this_application: list[str] = []
    suggested_angle: str


class MatchTier(str, Enum):
    hot = "hot"
    warm = "warm"
    cold = "cold"


class GapSeverity(str, Enum):
    minor = "minor"
    significant = "significant"
    dealbreaker = "dealbreaker"


class MatchGap(BaseModel):
    gap: str
    severity: GapSeverity


class MatchScorerOutput(BaseModel):
    """Structured-output contract for the Match Scorer agent (prompts/match_scorer.md)."""

    score: int = Field(ge=0, le=100)
    tier: MatchTier
    reasoning: str
    top_strengths: list[str] = []
    top_gaps: list[MatchGap] = []
    red_flags: list[str] = []


class ResumeEntryCategory(str, Enum):
    experience = "experience"
    project = "project"
    skill = "skill"
    education = "education"
    achievement = "achievement"


class TailoredResumeLine(BaseModel):
    master_resume_entry_id: str
    text: str


class TailoredResumeSection(BaseModel):
    category: ResumeEntryCategory
    lines: list[TailoredResumeLine]


class ResumeTailorerOutput(BaseModel):
    """Structured-output contract for the Resume Tailorer agent (prompts/resume_tailorer.md).

    Hard constraint: every line must carry the master_resume_entry_id it was
    drawn from. The Grounding Critic checks that the tailored text doesn't
    invent claims beyond that entry.
    """

    summary: str
    sections: list[TailoredResumeSection]


class GroundingCriticOutput(BaseModel):
    """Structured-output contract for the Grounding Critic agent (prompts/grounding_critic.md)."""

    passes: bool
    violations: list[str] = []


class BaselineResumeLine(BaseModel):
    text: str


class BaselineResumeSection(BaseModel):
    category: ResumeEntryCategory
    lines: list[BaselineResumeLine]


class BaselineTailorOutput(BaseModel):
    """Structured-output contract for the single-prompt eval baseline (prompts/baseline_tailor.md).

    Unlike ResumeTailorerOutput, lines carry no master_resume_entry_id —
    this is the naive "tailor this resume to this JD" baseline that Anchor's
    Resume Tailorer + Grounding Critic is compared against (planning doc
    §10.1). The Grounding Critic is run post-hoc against these lines, checked
    against the candidate's full resume rather than a single cited entry.
    """

    summary: str
    sections: list[BaselineResumeSection]
    cover_letter_paragraphs: list[str]


# qwen2.5:7b reliably ignores the prompt instruction not to inline grounding
# citations (e.g. "(id=<uuid>)", "(from <uuid>)") into cover letter prose, so
# strip them here as a backstop.
_INLINE_CITATION_RE = re.compile(
    r"\s*[\(\[]\s*(?:ids?\s*[:=]\s*[\w-]+|from\s+[\w]+-[\w-]+)"
    r"(?:\s*,\s*(?:ids?\s*[:=]\s*)?[\w-]+)*"
    r"\s*[\)\]]",
    re.IGNORECASE,
)


class CoverLetterOutput(BaseModel):
    """Structured-output contract for the Cover Letter Generator agent (prompts/cover_letter.md)."""

    paragraphs: list[str]
    master_resume_entry_ids: list[str] = []
    company_detail_referenced: str

    @field_validator("paragraphs")
    @classmethod
    def strip_inline_citations(cls, paragraphs: list[str]) -> list[str]:
        cleaned = []
        for p in paragraphs:
            p = _INLINE_CITATION_RE.sub("", p)
            p = re.sub(r"\s{2,}", " ", p)
            p = re.sub(r"\s+([.,;:])", r"\1", p)
            cleaned.append(p.strip())
        return cleaned


class LinkedInDrafterOutput(BaseModel):
    """Structured-output contract for the LinkedIn Drafter agent (prompts/linkedin_drafter.md)."""

    message: str
    company_detail_referenced: str


class RequirementCategory(str, Enum):
    must_have = "must_have"
    nice_to_have = "nice_to_have"


class SkillGap(BaseModel):
    requirement: str
    category: RequirementCategory
    severity: GapSeverity
    how_to_close: str


class SkillGapVerdict(str, Enum):
    apply_now = "apply_now"
    address_gap_first = "address_gap_first"
    not_recommended = "not_recommended"


class SkillGapAnalyzerOutput(BaseModel):
    """Structured-output contract for the Skill Gap Analyzer agent (prompts/skill_gap_analyzer.md)."""

    gaps: list[SkillGap] = []
    verdict: SkillGapVerdict


class FollowUpDecision(str, Enum):
    send_now = "send_now"
    wait = "wait"


class FollowUpDecisionOutput(BaseModel):
    """Structured-output contract for the Follow-up Decision agent (prompts/follow_up_decision.md)."""

    decision: FollowUpDecision
    reasoning: str
    nudge_paragraphs: list[str] = []


class PatternConfidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Pattern(BaseModel):
    observation: str
    evidence: str
    suggested_action: str
    confidence: PatternConfidence


class PatternDetectorOutput(BaseModel):
    """Structured-output contract for the Pattern Detector agent (prompts/pattern_detector.md).

    Hard constraint: if the input's min-N=5 guard says the sample size isn't
    reached, `patterns` must be empty and `summary` says so plainly rather
    than fabricating a pattern from too little data.
    """

    patterns: list[Pattern] = []
    summary: str
