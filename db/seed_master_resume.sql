-- =====================================================================
-- Anchor — master resume + user profile seed data
--
-- Satvik Krishna's real resume content (uploaded 2026-06-16).
-- This is the actual candidate data; the previous genericized
-- "friend's resume" placeholder content has been replaced.
--
-- Idempotent: safe to re-run. DELETE + re-INSERT.
-- material_grounding rows that reference master_resume_entry.id
-- will need to be cleared first if any exist (FK constraint).
-- =====================================================================

DELETE FROM material_grounding;
DELETE FROM master_resume_entry;
DELETE FROM user_profile;

-- ---------- master_resume_entry ----------

INSERT INTO master_resume_entry (category, canonical_text, facts, tags, priority) VALUES
-- ---- Education ----
(
    'education',
    'Pursuing a Bachelor of Engineering in Computer Science at RV College of Engineering (RVCE), Bengaluru (2024–2028), with a CGPA of 8.98/10. Relevant coursework: Data Structures, Design and Analysis of Algorithms, Operating Systems, Computer Networks, Discrete Mathematics, Data Science for Engineers, Programming in C.',
    '{"degree": "Bachelor of Engineering in Computer Science", "institution": "RV College of Engineering (RVCE)", "location": "Bengaluru, Karnataka, India", "dates": "2024–2028", "cgpa": "8.98/10", "coursework": ["Data Structures", "Design and Analysis of Algorithms", "Operating Systems", "Computer Networks", "Discrete Mathematics", "Data Science for Engineers", "Programming in C"]}',
    ARRAY['education', 'computer-science', 'rvce', 'bengaluru', 'india'],
    5
),
(
    'education',
    'Completed Class 1–12 at National Public School, Indiranagar, Bengaluru (CBSE, 2009–2023), with PCMC (Physics, Chemistry, Mathematics, Computer Science) specialisation.',
    '{"school": "National Public School, Indiranagar", "location": "Bengaluru, Karnataka", "board": "CBSE", "dates": "2009–2023", "stream": "PCMC (Physics, Chemistry, Mathematics, Computer Science)"}',
    ARRAY['education', 'cbse', 'school', 'india'],
    2
),
-- ---- Experience ----
(
    'experience',
    'As Product & Design Intern at KuKClean, a plant-based D2C e-commerce brand (Bangalore, Jun–Jul 2024), produced end-to-end creative assets across packaging, social-media campaigns, and storefront visuals — delivering 30+ design files in Photoshop, Lightroom, and Figma across an 8-week engagement.',
    '{"role": "Product & Design Intern", "company": "KuKClean", "company_type": "plant-based D2C e-commerce brand", "location": "Bangalore", "dates": "Jun 2024 – Jul 2024", "deliverables": "30+ design files", "tools": ["Photoshop", "Lightroom", "Figma"], "scope": "packaging, social-media campaigns, storefront visuals", "duration": "8 weeks"}',
    ARRAY['experience', 'design', 'figma', 'photoshop', 'lightroom', 'e-commerce', 'intern'],
    4
),
(
    'experience',
    'At KuKClean (Jun–Jul 2024), set up 20+ product listings end-to-end on the e-commerce storefront — writing product copy, optimising on-page descriptions, and photographing the catalog to support go-to-market launch. Also built Figma wireframes and high-fidelity mockups for new product pages, converting founding-team briefs into design-ready specs for web implementation.',
    '{"role": "Product & Design Intern", "company": "KuKClean", "dates": "Jun 2024 – Jul 2024", "deliverables": ["20+ product listings end-to-end", "Figma wireframes and high-fidelity mockups"], "activities": ["writing product copy", "optimising on-page descriptions", "photographing catalog", "converting briefs to design-ready specs"]}',
    ARRAY['experience', 'product', 'e-commerce', 'figma', 'copywriting', 'photography', 'intern'],
    3
),
-- ---- Projects ----
(
    'project',
    'Designed and shipped Meridian, a 4-agent orchestration system (financial, market, leadership, sentiment) that produces cited due-diligence memos on NSE/BSE companies in ~75 seconds, pulling from yfinance, Wikipedia, Reddit JSON, and Google News RSS in parallel via asyncio. Stack: Python, FastAPI, Next.js, asyncio, Ollama (qwen2.5:7b), Server-Sent Events, Pydantic, SQLite.',
    '{"name": "Meridian", "type": "Multi-Agent Due Diligence System", "tech_stack": ["Python", "FastAPI", "Next.js", "asyncio", "Ollama (qwen2.5:7b)", "Server-Sent Events", "Pydantic", "SQLite"], "agents": 4, "agent_types": ["financial", "market", "leadership", "sentiment"], "latency": "~75 seconds", "data_sources": ["yfinance", "Wikipedia", "Reddit JSON", "Google News RSS"], "parallelism": "asyncio"}',
    ARRAY['project', 'python', 'fastapi', 'asyncio', 'ollama', 'pydantic', 'sqlite', 'nextjs', 'multi-agent', 'llm', 'ai', 'server-sent-events'],
    5
),
(
    'project',
    'In Meridian, built a citation-grounded schema where every memo claim links to evidence rows by database constraint — eliminating unsourced claims by construction; a content-addressed SHA-256 disk cache makes evals reproducible and dev iterations near-zero-cost. Ran an evaluation across 9 NSE companies and 135 verified ground-truth claims: 15% average hallucination rate (financial agent: 0% across all 9), 79% ground-truth coverage, 11 unique citations per run vs. 0 for a single-prompt baseline.',
    '{"name": "Meridian", "citation_mechanism": "every memo claim linked to evidence rows by DB constraint", "cache": "content-addressed SHA-256 disk cache", "eval_companies": 9, "eval_claims": 135, "avg_hallucination_rate": "15%", "financial_agent_hallucination_rate": "0%", "ground_truth_coverage": "79%", "citations_per_run": 11, "baseline_citations_per_run": 0}',
    ARRAY['project', 'meridian', 'llm-eval', 'hallucination', 'citation', 'grounding', 'cache', 'evaluation'],
    5
),
(
    'project',
    'Built Anchor, a 5-workflow n8n orchestration system that turns a job-posting URL into a researched, factually-grounded application packet — Playwright-driven JD scraping and parsing, multi-source company research, match scoring, tailored-material generation, and cron-based follow-up scheduling with Wait/Resume human-in-loop gates. Stack: n8n, Postgres, Playwright, Notion API, Google Drive API, Slack Web API, OAuth2.',
    '{"name": "Anchor", "type": "Personal AI Application Pipeline", "tech_stack": ["n8n", "Postgres", "Playwright", "Notion API", "Google Drive API", "Slack Web API", "OAuth2"], "workflows": 5, "capabilities": ["JD scraping and parsing", "multi-source company research", "match scoring", "tailored-material generation", "cron follow-up scheduling"], "patterns": ["Wait/Resume human-in-loop gates", "LLM evaluation", "prompt engineering"]}',
    ARRAY['project', 'n8n', 'postgres', 'playwright', 'notion', 'slack', 'oauth2', 'orchestration', 'ai', 'llm', 'prompt-engineering'],
    5
),
(
    'project',
    'In Anchor, designed a master-resume schema where every tailored line links to a structured master entry by foreign-key constraint, with an adversarial Grounding Critic enforcing factual grounding before any material ships; full observability layer logs every agent run to Postgres (input hash, structured output, latency, critic verdict) — queryable audit trail across the pipeline.',
    '{"name": "Anchor", "grounding": "FK-constrained master-resume schema + adversarial Grounding Critic", "observability": "every agent run logged to Postgres: input hash, structured output, latency, critic verdict", "principle": "tailoring is selection + rephrasing, never invention"}',
    ARRAY['project', 'anchor', 'grounding', 'observability', 'postgres', 'llm-eval', 'prompt-engineering', 'agent-orchestration'],
    4
),
(
    'project',
    'Built CrowdSense, a real-time crowd-monitoring platform combining CSRNet density estimation for dense scenes with YOLOv8 detection for sparse-to-medium density, dynamically switching between models based on scene density to balance accuracy and compute. Stack: PyTorch, OpenCV, CSRNet, YOLOv8, optical flow, RAG-based density estimation, ShanghaiTech Dataset, React, FastAPI, SQLite.',
    '{"name": "CrowdSense", "type": "Real-Time Crowd Intelligence Platform", "tech_stack": ["PyTorch", "OpenCV", "CSRNet", "YOLOv8", "optical flow", "RAG", "ShanghaiTech Dataset", "React", "FastAPI", "SQLite"], "approach": "dynamic model switching based on scene density: CSRNet for dense scenes, YOLOv8 for sparse-to-medium"}',
    ARRAY['project', 'pytorch', 'opencv', 'yolov8', 'csrnet', 'computer-vision', 'ml', 'fastapi', 'react', 'sqlite', 'rag'],
    4
),
(
    'project',
    'In CrowdSense, implemented zone-wise risk detection using OpenCV optical flow for privacy-preserving movement analysis and published crowd-safety thresholds (5–6 persons/m² warning, 7–8 critical) for stampede-risk alerts; React + FastAPI dashboard surfaces live density heatmaps and zone occupancy.',
    '{"name": "CrowdSense", "risk_detection": "zone-wise using OpenCV optical flow", "privacy": "privacy-preserving movement analysis (no face recognition)", "safety_thresholds": {"warning": "5-6 persons/m²", "critical": "7-8 persons/m²"}, "dashboard": "React + FastAPI, live density heatmaps and zone occupancy"}',
    ARRAY['project', 'crowdsense', 'opencv', 'optical-flow', 'risk-detection', 'safety', 'react', 'fastapi', 'dashboard'],
    3
),
-- ---- Skills ----
(
    'skill',
    'Programming languages: Python, C, SQL, HTML, CSS.',
    '{"languages": ["Python", "C", "SQL", "HTML", "CSS"]}',
    ARRAY['python', 'c', 'sql', 'html', 'css', 'programming-languages'],
    5
),
(
    'skill',
    'Python libraries: scikit-learn, pandas, NumPy, Matplotlib, Scrapy, FastAPI, Pydantic, asyncio, Playwright. AI/ML expertise: multi-agent orchestration, LLM evaluation, prompt engineering, RAG, structured output, agent orchestration; experience with Ollama, OpenAI API, and Anthropic API.',
    '{"python_libraries": ["scikit-learn", "pandas", "NumPy", "Matplotlib", "Scrapy", "FastAPI", "Pydantic", "asyncio", "Playwright"], "ai_ml_expertise": ["multi-agent orchestration", "LLM evaluation", "prompt engineering", "RAG", "structured output", "agent orchestration"], "llm_apis": ["Ollama", "OpenAI API", "Anthropic API"]}',
    ARRAY['python', 'fastapi', 'pydantic', 'asyncio', 'playwright', 'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'scrapy', 'ollama', 'openai', 'anthropic', 'llm', 'rag', 'prompt-engineering', 'multi-agent', 'ai-ml'],
    5
),
(
    'skill',
    'Tools and platforms: n8n, Make.com, Next.js, React, Tailwind CSS, Postgres, SQLite, Docker, Git, GitHub Copilot, Claude Code, Google Cloud, Google Looker Studio, Figma, Lovable, Adobe Photoshop, Adobe Lightroom, Blender, DaVinci Resolve.',
    '{"workflow_automation": ["n8n", "Make.com"], "frontend": ["Next.js", "React", "Tailwind CSS"], "databases": ["Postgres", "SQLite"], "devops": ["Docker", "Git"], "ai_tools": ["GitHub Copilot", "Claude Code"], "cloud": ["Google Cloud", "Google Looker Studio"], "design": ["Figma", "Lovable", "Adobe Photoshop", "Adobe Lightroom", "Blender", "DaVinci Resolve"]}',
    ARRAY['n8n', 'nextjs', 'react', 'tailwind', 'postgres', 'sqlite', 'docker', 'git', 'google-cloud', 'figma', 'design-tools'],
    4
),
-- ---- Achievements ----
(
    'achievement',
    'Completed Data Science for Engineers from IIT Madras (2026). Pursuing Machine Learning Specialization from Stanford Online + DeepLearning.AI (in progress) and CCNA: Networking Fundamentals from Infosys Springboard (in progress).',
    '{"certifications": [{"name": "Data Science for Engineers", "issuer": "IIT Madras", "year": 2026, "status": "completed"}, {"name": "Machine Learning Specialization", "issuer": "Stanford Online + DeepLearning.AI", "status": "in progress"}, {"name": "CCNA: Networking Fundamentals", "issuer": "Infosys Springboard", "status": "in progress"}]}',
    ARRAY['certification', 'machine-learning', 'data-science', 'networking', 'stanford', 'iit-madras'],
    3
);

-- ---------- user_profile ----------
-- Singleton table. Loaded by Resume Critic, Match Scorer, Role Evaluator.

INSERT INTO user_profile (long_term_goals, target_role_types) VALUES (
    'Computer Science sophomore at RV College of Engineering (CGPA 8.98/10), '
    'building towards ML engineering and AI systems work. My projects — '
    'Meridian (multi-agent research system with a 135-claim grounding eval: '
    '15% avg hallucination rate, financial agent 0%) and Anchor '
    '(n8n-orchestrated job-pipeline with FK-constrained Grounding Critic) — '
    'reflect a preference for building systems where correctness is verifiable, '
    'not assumed. I want to join a team doing serious work at the intersection '
    'of ML/AI and backend systems — whether that''s ML infrastructure, data '
    'pipelines, LLM applications, or AI-powered products — as a Summer 2026 intern.',
    ARRAY[
        'ML engineering intern',
        'AI/ML intern',
        'software engineering intern',
        'backend engineering intern',
        'AI infrastructure intern',
        'data engineering intern'
    ]
);
