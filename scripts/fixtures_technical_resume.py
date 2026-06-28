"""
Second set of realistic (non-template) master_resume_entry fixtures, in the
same shape as demo_realistic_resume.py's DEMO_ENTRIES/DEMO_PROFILE.

IMPORTANT - privacy: genericized from a second friend's resume, offered "for
testing." No name/email/phone/LinkedIn/GitHub/specific institution or company
names are included anywhere below - only the substantive content (degree,
internship, projects, skills). Not wired into any script or seed data; kept
here as an alternative fixture set (more technical/ML/backend-heavy than
demo_realistic_resume.py's more generalist/leadership-heavy profile) for
future test runs that want a different applicant profile.

Usage: import DEMO_ENTRIES / DEMO_PROFILE from this module in place of the
ones in demo_realistic_resume.py (e.g. to demo against a more technical JD).
"""

DEMO_ENTRIES = [
    {
        "id": "tech-edu-1",
        "category": "education",
        "canonical_text": (
            "Pursuing a Bachelor of Engineering in Computer Science at an "
            "engineering college in Bangalore (2024 - 2028, expected), with "
            "a CGPA of 9.75/10."
        ),
        "tags": ["education", "computer-science", "bangalore"],
        "priority": 5,
    },
    {
        "id": "tech-edu-2",
        "category": "education",
        "canonical_text": (
            "Scored 99% in a Class XII state board examination (2022-2024) "
            "and 96.3% in a Class X board examination (2022), reflecting a "
            "strong and consistent academic record prior to university."
        ),
        "tags": ["education", "academic-record"],
        "priority": 2,
    },
    {
        "id": "tech-exp-1",
        "category": "experience",
        "canonical_text": (
            "As a Backend Developer Intern at a software company (Jun-Jul "
            "2025), developed RESTful APIs using .NET Core and C# for a "
            "fluid management system application, including endpoints for "
            "user profile management covering data retrieval and preference "
            "updates."
        ),
        "tags": ["backend", "dotnet", "csharp", "rest-api", "internship"],
        "priority": 5,
    },
    {
        "id": "tech-exp-2",
        "category": "experience",
        "canonical_text": (
            "In the same Backend Developer Intern role, implemented "
            "JWT-based authentication and claim-based authorization for "
            "secure user access, and designed Ad-Hoc test-creation APIs "
            "using DTOs and a service-layer architecture."
        ),
        "tags": ["authentication", "security", "api-design", "dotnet"],
        "priority": 4,
    },
    {
        "id": "tech-proj-1",
        "category": "project",
        "canonical_text": (
            "Leading a team of 4 to build a patent-intelligence platform "
            "(2026-present) that evaluates the novelty and strength of "
            "user-submitted ideas, designing an end-to-end system that "
            "combines NLP, knowledge graphs, and graph neural networks for "
            "patent similarity analysis."
        ),
        "tags": ["project", "team-lead", "nlp", "knowledge-graphs", "gnn", "patent-intelligence"],
        "priority": 5,
    },
    {
        "id": "tech-proj-2",
        "category": "project",
        "canonical_text": (
            "For the same patent-intelligence platform, implemented "
            "semantic-similarity and graph-based scoring to assess idea "
            "novelty and solution-space density, and built a retrieval "
            "pipeline integrating vector search with LLM-based reasoning "
            "for contextual patent comparison."
        ),
        "tags": ["project", "vector-search", "llm", "semantic-search", "scoring"],
        "priority": 5,
    },
    {
        "id": "tech-proj-3",
        "category": "project",
        "canonical_text": (
            "Co-authored a research project (2025) on multi-stage cloud "
            "attack detection using machine learning and synthetic log "
            "data, building a synthetic log-generation pipeline to simulate "
            "attacks such as brute-force, privilege escalation, and data "
            "exfiltration."
        ),
        "tags": ["project", "machine-learning", "security", "cloud", "research"],
        "priority": 4,
    },
    {
        "id": "tech-proj-4",
        "category": "project",
        "canonical_text": (
            "For the same cloud intrusion detection project, implemented "
            "and ensembled supervised and unsupervised anomaly-detection "
            "models (Random Forest, XGBoost, Isolation Forest, and "
            "Autoencoder) to improve detection robustness across attack "
            "stages."
        ),
        "tags": ["project", "xgboost", "random-forest", "isolation-forest", "autoencoder", "ensemble"],
        "priority": 4,
    },
    {
        "id": "tech-proj-5",
        "category": "project",
        "canonical_text": (
            "Built a real-time pothole-detection system (2025) using "
            "deep-learning object detection (SSD MobileNet V2), with a "
            "full-stack Flutter application that captures camera feed and "
            "sends detected pothole images to the backend; optimized the "
            "model for low-latency edge deployment."
        ),
        "tags": ["project", "computer-vision", "tensorflow", "flutter", "edge-ml"],
        "priority": 4,
    },
    {
        "id": "tech-proj-6",
        "category": "project",
        "canonical_text": (
            "For the same pothole-detection system, integrated location "
            "tracking with detected images and built a backend pipeline "
            "that generates geospatial heatmaps to visualize pothole "
            "density across an area."
        ),
        "tags": ["project", "geospatial", "data-visualization", "backend"],
        "priority": 3,
    },
    {
        "id": "tech-skill-1",
        "category": "skill",
        "canonical_text": "Programming languages: Python, C/C++, and R.",
        "tags": ["python", "c", "cpp", "r", "programming-languages"],
        "priority": 5,
    },
    {
        "id": "tech-skill-2",
        "category": "skill",
        "canonical_text": (
            "Frameworks and libraries for full-stack and ML development: "
            "React, Node.js, Flutter, FastAPI, pandas, NumPy, and "
            "Matplotlib."
        ),
        "tags": ["react", "nodejs", "flutter", "fastapi", "pandas", "numpy"],
        "priority": 4,
    },
    {
        "id": "tech-skill-3",
        "category": "skill",
        "canonical_text": (
            "Developer tooling: Git, Docker, Google Cloud Platform, VS "
            "Code, Visual Studio, and PyCharm."
        ),
        "tags": ["git", "docker", "gcp", "tools"],
        "priority": 3,
    },
]

DEMO_PROFILE = {
    "long_term_goals": (
        "Computer Science undergraduate (CGPA 9.75/10) with a strong "
        "backend and machine-learning foundation, currently leading a "
        "4-person team building an NLP/knowledge-graph/GNN platform for "
        "patent intelligence. Comfortable across the stack from .NET/C# "
        "backend APIs to ML pipelines (XGBoost, autoencoders, computer "
        "vision) and full-stack apps (React, Flutter, FastAPI), with the "
        "goal of contributing to a Summer 2026 internship on a backend or "
        "ML engineering team and growing into a software engineer who "
        "builds production ML-powered systems."
    ),
    "target_role_types": [
        "software engineering intern",
        "machine learning engineering intern",
        "backend engineering intern",
    ],
}
