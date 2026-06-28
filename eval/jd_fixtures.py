"""
20 standalone JD + company-synthesis fixtures for the Material Quality Eval
(planning doc §10.1, roadmap Days 15-16).

Same fixture shapes as scripts/demo_realistic_resume.py's SAMPLE_JD /
SAMPLE_SYNTHESIS (JDParserOutput / CompanySynthesizerOutput), all fictional
companies — no live fetching, no real postings (test postings go stale, per
Day 5's note; standalone fixtures are the established pattern for eval/test
scripts in this repo).

Deliberately spans good/medium/poor fit for the seeded master resume
(scripts/demo_realistic_resume.py's DEMO_ENTRIES/DEMO_PROFILE — a generalist
CS undergrad with web-dev project experience, Python/C/C++/Java, AI-assisted
dev workflows, MySQL, and event-leadership/community experience). The spread
gives the eval realistic variance in match score/tier rather than 20
near-identical "warm" results.

FIXTURES[0:10]  -> Day 15 batch
FIXTURES[10:20] -> Day 16 batch
"""

FIXTURES = [
    # ------------------------------------------------------------------
    # Good fit (1-8)
    # ------------------------------------------------------------------
    {
        "id": "01_fullstack_startup",
        "jd": {
            "company_name": "Brightloop",
            "role_title": "Software Engineering Intern - Full Stack",
            "team_or_org": "Product Engineering",
            "must_haves": [
                "Proficiency in Python or Java",
                "Experience building a web application (course or personal project)",
                "Currently pursuing a B.S./B.Comp. in Computer Science or related field",
            ],
            "nice_to_haves": [
                "Familiarity with relational databases (SQL)",
                "Comfortable working in a small cross-functional team",
                "Exposure to AI-assisted coding tools",
            ],
            "responsibilities": [
                "Ship small features end-to-end across frontend and backend",
                "Write and review pull requests with the product engineering team",
                "Participate in sprint planning and demo new features weekly",
            ],
            "tech_stack": ["Python", "TypeScript", "PostgreSQL", "React"],
            "culture_signals": ["small team", "fast iteration", "mentorship-focused"],
            "comp_range": "$30-38/hr",
            "location_type": "hybrid",
        },
        "synthesis": {
            "what_they_do": "Brightloop builds a scheduling and rostering web app for small healthcare clinics.",
            "recent_developments": ["Closed a seed round to expand the engineering team to 12"],
            "tech_signals": ["Python", "TypeScript", "PostgreSQL", "React"],
            "company_type": "startup",
            "culture_signals": ["small team", "mentorship-focused", "fast iteration"],
            "likely_role_context": "The intern joins a 4-person product engineering pod shipping customer-facing features directly.",
        },
    },
    {
        "id": "02_pm_intern_startup",
        "jd": {
            "company_name": "Tindergrove Labs",
            "role_title": "Product Management Intern",
            "team_or_org": "Product",
            "must_haves": [
                "Strong written and verbal communication skills",
                "Currently pursuing an undergraduate degree (any technical field)",
                "Experience translating user needs into concrete requirements (course project or extracurricular)",
            ],
            "nice_to_haves": [
                "Comfort reading basic technical specs or API docs",
                "Experience running or coordinating a team or event",
                "Familiarity with Figma or similar design tools",
            ],
            "responsibilities": [
                "Gather and synthesize user feedback into feature requests",
                "Draft requirements docs and user stories for the engineering team",
                "Coordinate weekly cross-functional syncs between design, eng, and growth",
            ],
            "tech_stack": ["Notion", "Figma", "Linear"],
            "culture_signals": ["early-stage", "scrappy", "high ownership"],
            "comp_range": "$28-34/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Tindergrove Labs makes a habit-tracking app for university students.",
            "recent_developments": ["Launched v2 of the app with social accountability features"],
            "tech_signals": ["Notion", "Figma", "Linear"],
            "company_type": "startup",
            "culture_signals": ["scrappy", "high ownership", "early-stage"],
            "likely_role_context": "The intern works directly with the 2-person founding team on requirements and coordination.",
        },
    },
    {
        "id": "03_devex_ai_tools",
        "jd": {
            "company_name": "Pathwright",
            "role_title": "Developer Experience Intern",
            "team_or_org": "Developer Tools",
            "must_haves": [
                "Proficiency in Python",
                "Hands-on experience with AI coding assistants (e.g. Claude, ChatGPT, Copilot)",
                "Currently pursuing a B.S./B.Comp. in Computer Science or related field",
            ],
            "nice_to_haves": [
                "Interest in prompt engineering and developer tooling",
                "Experience with VS Code extensions or CLI tools",
                "Familiarity with Docker",
            ],
            "responsibilities": [
                "Prototype internal tools that use LLMs to speed up engineering workflows",
                "Write documentation and examples for the internal developer platform",
                "Collect feedback from engineers and iterate on prompt templates",
            ],
            "tech_stack": ["Python", "Docker", "VS Code", "OpenAI/Anthropic APIs"],
            "culture_signals": ["AI-forward", "experimentation encouraged", "small team"],
            "comp_range": "$32-40/hr",
            "location_type": "remote",
        },
        "synthesis": {
            "what_they_do": "Pathwright builds internal developer-platform tooling for mid-size engineering orgs.",
            "recent_developments": ["Released an internal AI coding assistant pilot to 3 customers"],
            "tech_signals": ["Python", "Docker", "Anthropic API", "VS Code extensions"],
            "company_type": "startup",
            "culture_signals": ["AI-forward", "experimentation encouraged"],
            "likely_role_context": "The intern joins a small developer-tools team prototyping AI-assisted workflows.",
        },
    },
    {
        "id": "04_program_coordinator",
        "jd": {
            "company_name": "Civora Education",
            "role_title": "Technical Program Coordinator Intern",
            "team_or_org": "Programs",
            "must_haves": [
                "Experience planning or coordinating a multi-person event or program",
                "Currently pursuing an undergraduate degree",
                "Strong organizational and communication skills",
            ],
            "nice_to_haves": [
                "Basic familiarity with spreadsheets and scheduling tools",
                "Some exposure to software development concepts",
                "Experience working with volunteers or student groups",
            ],
            "responsibilities": [
                "Coordinate logistics for a summer coding bootcamp cohort",
                "Manage schedules and communications between instructors, mentors, and students",
                "Track program metrics and prepare weekly status updates",
            ],
            "tech_stack": ["Google Workspace", "Airtable"],
            "culture_signals": ["mission-driven", "education-focused", "collaborative"],
            "comp_range": "$22-26/hr",
            "location_type": "hybrid",
        },
        "synthesis": {
            "what_they_do": "Civora Education runs coding bootcamps for underrepresented students.",
            "recent_developments": ["Expanding to a second city for the upcoming summer cohort"],
            "tech_signals": ["Airtable", "Google Workspace"],
            "company_type": "startup",
            "culture_signals": ["mission-driven", "education-focused"],
            "likely_role_context": "The intern supports program operations for a ~40-student summer cohort.",
        },
    },
    {
        "id": "05_qa_testing",
        "jd": {
            "company_name": "Ferrowell Systems",
            "role_title": "Software Testing Intern",
            "team_or_org": "Quality Engineering",
            "must_haves": [
                "Currently pursuing a B.S./B.Comp. in Computer Science or related field",
                "Experience writing test cases or bug reports (course project acceptable)",
                "Familiarity with at least one programming language (Python, Java, or C++)",
            ],
            "nice_to_haves": [
                "Exposure to automated testing frameworks",
                "Experience documenting software behavior for non-technical audiences",
                "Attention to detail across a large feature surface",
            ],
            "responsibilities": [
                "Execute test plans for new feature releases and log defects",
                "Write clear, reproducible bug reports for the engineering team",
                "Help expand automated regression test coverage",
            ],
            "tech_stack": ["Java", "Selenium", "Jira"],
            "culture_signals": ["process-oriented", "established product", "mentorship-focused"],
            "comp_range": "$26-30/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Ferrowell Systems makes inventory management software for mid-size retailers.",
            "recent_developments": ["Rolling out a major UI overhaul over the next two quarters"],
            "tech_signals": ["Java", "Selenium", "Jira"],
            "company_type": "enterprise",
            "culture_signals": ["process-oriented", "established product"],
            "likely_role_context": "The intern joins a QA team validating the upcoming UI overhaul release.",
        },
    },
    {
        "id": "06_web_platform",
        "jd": {
            "company_name": "Reedmark",
            "role_title": "Software Engineering Intern - Web Platform",
            "team_or_org": "Platform",
            "must_haves": [
                "Proficiency in at least one of Python, Java, or JavaScript/TypeScript",
                "Experience building and shipping a web application end-to-end",
                "Currently pursuing a B.S./B.Comp. in Computer Science or related field",
            ],
            "nice_to_haves": [
                "Familiarity with relational databases (SQL)",
                "Experience working in a team with code review",
                "Comfort presenting technical work to a group",
            ],
            "responsibilities": [
                "Build internal-facing features for the content management platform",
                "Collaborate with design and content teams on feature requirements",
                "Present completed work in weekly demo sessions",
            ],
            "tech_stack": ["Java", "MySQL", "React"],
            "culture_signals": ["collaborative", "demo culture", "established team"],
            "comp_range": "$30-36/hr",
            "location_type": "hybrid",
        },
        "synthesis": {
            "what_they_do": "Reedmark builds a content management platform for digital publishers.",
            "recent_developments": ["Onboarded two new major publisher clients this quarter"],
            "tech_signals": ["Java", "MySQL", "React"],
            "company_type": "startup",
            "culture_signals": ["collaborative", "demo culture"],
            "likely_role_context": "The intern joins the platform team building internal CMS features for publisher clients.",
        },
    },
    {
        "id": "07_community_ops",
        "jd": {
            "company_name": "Fernbridge Foundation",
            "role_title": "Community & Operations Intern",
            "team_or_org": "Community Programs",
            "must_haves": [
                "Experience with community organizing, volunteering, or outreach programs",
                "Currently pursuing an undergraduate degree",
                "Comfortable coordinating logistics across multiple stakeholders",
            ],
            "nice_to_haves": [
                "Basic data entry / spreadsheet skills",
                "Experience with social media or newsletter tools",
                "Interest in nonprofit operations",
            ],
            "responsibilities": [
                "Support logistics for community outreach and food-distribution events",
                "Maintain volunteer schedules and track program impact metrics",
                "Draft outreach communications to partner organizations",
            ],
            "tech_stack": ["Google Workspace", "Mailchimp"],
            "culture_signals": ["mission-driven", "community-focused", "small team"],
            "comp_range": "$20-24/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Fernbridge Foundation runs community food-security programs in partnership with local charities.",
            "recent_developments": ["Expanded weekly distribution capacity by 30%"],
            "tech_signals": ["Google Workspace", "Mailchimp"],
            "company_type": "startup",
            "culture_signals": ["mission-driven", "community-focused"],
            "likely_role_context": "The intern supports day-to-day operations for weekly community distribution events.",
        },
    },
    {
        "id": "08_ai_tools_eng",
        "jd": {
            "company_name": "Lucenta AI",
            "role_title": "AI Tools Engineering Intern",
            "team_or_org": "Applied AI",
            "must_haves": [
                "Proficiency in Python",
                "Hands-on experience with LLM-based tools (Claude, ChatGPT, or similar)",
                "Currently pursuing a B.S./B.Comp. in Computer Science or related field",
            ],
            "nice_to_haves": [
                "Experience with prompt engineering for structured outputs",
                "Familiarity with relational databases",
                "Comfort working independently with ambiguous requirements",
            ],
            "responsibilities": [
                "Build internal prototypes that use LLMs to automate research and writing tasks",
                "Iterate on prompts and evaluate output quality against a rubric",
                "Document findings and present to the applied AI team",
            ],
            "tech_stack": ["Python", "Postgres", "Anthropic API"],
            "culture_signals": ["research-adjacent", "fast iteration", "small team"],
            "comp_range": "$34-42/hr",
            "location_type": "remote",
        },
        "synthesis": {
            "what_they_do": "Lucenta AI builds applied-AI prototypes and internal tools for enterprise clients.",
            "recent_developments": ["Raised a Series A to grow the applied AI team"],
            "tech_signals": ["Python", "Postgres", "Anthropic API"],
            "company_type": "startup",
            "culture_signals": ["research-adjacent", "fast iteration"],
            "likely_role_context": "The intern joins a small applied-AI team prototyping LLM-based internal tools.",
        },
    },
    # ------------------------------------------------------------------
    # Medium fit (9-14)
    # ------------------------------------------------------------------
    {
        "id": "09_backend_fastapi",
        "jd": {
            "company_name": "Coalwright Health",
            "role_title": "Backend Engineering Intern",
            "team_or_org": "Platform Services",
            "must_haves": [
                "Proficiency in Python",
                "Experience with a web framework (FastAPI, Django, or Flask)",
                "Currently pursuing a B.S./B.Comp. in Computer Science or related field",
            ],
            "nice_to_haves": [
                "Experience with Docker and containerized deployments",
                "Familiarity with CI/CD pipelines",
                "Exposure to message queues or async task processing",
            ],
            "responsibilities": [
                "Build and maintain REST APIs for internal patient-scheduling services",
                "Write integration tests and improve service observability",
                "Participate in on-call shadowing and incident reviews",
            ],
            "tech_stack": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "culture_signals": ["healthcare-adjacent", "process-oriented", "mentorship-focused"],
            "comp_range": "$32-38/hr",
            "location_type": "hybrid",
        },
        "synthesis": {
            "what_they_do": "Coalwright Health builds scheduling and operations software for outpatient clinics.",
            "recent_developments": ["Migrating core services to a new containerized platform"],
            "tech_signals": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "company_type": "enterprise",
            "culture_signals": ["process-oriented", "mentorship-focused"],
            "likely_role_context": "The intern joins the platform services team supporting a containerization migration.",
        },
    },
    {
        "id": "10_data_analyst",
        "jd": {
            "company_name": "Marlstone Retail",
            "role_title": "Data Analyst Intern",
            "team_or_org": "Business Intelligence",
            "must_haves": [
                "Proficiency in SQL",
                "Currently pursuing an undergraduate degree in a quantitative or technical field",
                "Comfortable working with large datasets in spreadsheets or notebooks",
            ],
            "nice_to_haves": [
                "Experience with a BI tool (Tableau, Looker, Power BI)",
                "Familiarity with Python for data analysis (pandas)",
                "Experience presenting data findings to stakeholders",
            ],
            "responsibilities": [
                "Build and maintain SQL queries powering weekly sales dashboards",
                "Analyze customer behavior data and summarize findings for merchandising teams",
                "Support ad-hoc data requests from business stakeholders",
            ],
            "tech_stack": ["SQL", "Tableau", "Python"],
            "culture_signals": ["data-driven", "established company", "cross-functional"],
            "comp_range": "$26-32/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Marlstone Retail operates a regional chain of home-goods stores with a growing e-commerce arm.",
            "recent_developments": ["Investing in a new BI stack to unify online and in-store sales data"],
            "tech_signals": ["SQL", "Tableau", "Python"],
            "company_type": "enterprise",
            "culture_signals": ["data-driven", "cross-functional"],
            "likely_role_context": "The intern joins the BI team supporting the new unified sales-data dashboards.",
        },
    },
    {
        "id": "11_mobile_dev",
        "jd": {
            "company_name": "Hollowmere Apps",
            "role_title": "Mobile App Development Intern",
            "team_or_org": "Mobile",
            "must_haves": [
                "Experience building a mobile or cross-platform app (course or personal project)",
                "Proficiency in at least one of Dart/Flutter, Swift, or Kotlin",
                "Currently pursuing a B.S./B.Comp. in Computer Science or related field",
            ],
            "nice_to_haves": [
                "Familiarity with REST APIs and backend integration",
                "Experience with app store submission processes",
                "Comfort with Git-based collaboration",
            ],
            "responsibilities": [
                "Implement new screens and features in the company's Flutter app",
                "Fix bugs reported through the app store and internal QA",
                "Collaborate with backend engineers on API integration",
            ],
            "tech_stack": ["Flutter", "Dart", "Firebase"],
            "culture_signals": ["small team", "fast iteration"],
            "comp_range": "$28-34/hr",
            "location_type": "remote",
        },
        "synthesis": {
            "what_they_do": "Hollowmere Apps builds a personal-finance tracking app for young adults.",
            "recent_developments": ["Crossed 100k downloads and is hiring for mobile growth"],
            "tech_signals": ["Flutter", "Dart", "Firebase"],
            "company_type": "startup",
            "culture_signals": ["small team", "fast iteration"],
            "likely_role_context": "The intern joins a 3-person mobile team shipping new app features directly to production.",
        },
    },
    {
        "id": "12_devops_infra",
        "jd": {
            "company_name": "Northgate Cloud",
            "role_title": "DevOps / Infrastructure Intern",
            "team_or_org": "Infrastructure",
            "must_haves": [
                "Familiarity with Docker and containerization",
                "Basic scripting ability (Python, Bash, or similar)",
                "Currently pursuing a B.S./B.Comp. in Computer Science or related field",
            ],
            "nice_to_haves": [
                "Exposure to CI/CD pipelines (GitHub Actions, Jenkins, etc.)",
                "Familiarity with cloud platforms (AWS, GCP, or Azure)",
                "Interest in observability and monitoring tooling",
            ],
            "responsibilities": [
                "Improve CI/CD pipeline reliability and build times",
                "Write and maintain infrastructure-as-code scripts",
                "Help build dashboards for service health monitoring",
            ],
            "tech_stack": ["Docker", "Kubernetes", "AWS", "Python"],
            "culture_signals": ["infrastructure-focused", "fast-paced", "on-call rotation"],
            "comp_range": "$34-40/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Northgate Cloud provides managed Kubernetes hosting for mid-size SaaS companies.",
            "recent_developments": ["Scaling infrastructure team to support new enterprise customers"],
            "tech_signals": ["Docker", "Kubernetes", "AWS", "Terraform"],
            "company_type": "startup",
            "culture_signals": ["infrastructure-focused", "fast-paced"],
            "likely_role_context": "The intern joins the infrastructure team improving CI/CD and monitoring for the hosting platform.",
        },
    },
    {
        "id": "13_frontend_react",
        "jd": {
            "company_name": "Verdant Studio",
            "role_title": "Frontend Engineering Intern",
            "team_or_org": "Web",
            "must_haves": [
                "Proficiency in JavaScript or TypeScript",
                "Experience with a modern frontend framework (React, Vue, or similar)",
                "Currently pursuing a B.S./B.Comp. in Computer Science or related field",
            ],
            "nice_to_haves": [
                "Experience with design systems or component libraries",
                "Familiarity with accessibility best practices",
                "Comfort working closely with designers",
            ],
            "responsibilities": [
                "Build UI components for the company's web app using React",
                "Collaborate with designers to implement pixel-accurate interfaces",
                "Write component tests and fix cross-browser issues",
            ],
            "tech_stack": ["React", "TypeScript", "Storybook"],
            "culture_signals": ["design-driven", "small team", "fast iteration"],
            "comp_range": "$30-36/hr",
            "location_type": "hybrid",
        },
        "synthesis": {
            "what_they_do": "Verdant Studio builds a collaborative whiteboarding tool for design teams.",
            "recent_developments": ["Redesigning the core editor UI for a major v3 release"],
            "tech_signals": ["React", "TypeScript", "Storybook"],
            "company_type": "startup",
            "culture_signals": ["design-driven", "fast iteration"],
            "likely_role_context": "The intern joins the web team contributing components to the v3 editor redesign.",
        },
    },
    {
        "id": "14_technical_writing",
        "jd": {
            "company_name": "Quillmark Systems",
            "role_title": "Technical Writing Intern",
            "team_or_org": "Developer Relations",
            "must_haves": [
                "Strong written communication skills",
                "Currently pursuing an undergraduate degree in a technical field",
                "Comfort reading and explaining code or API documentation",
            ],
            "nice_to_haves": [
                "Experience with Markdown and static-site doc tools",
                "Familiarity with at least one programming language",
                "Experience presenting technical material to non-technical audiences",
            ],
            "responsibilities": [
                "Write and update API reference documentation and tutorials",
                "Review pull requests for documentation accuracy",
                "Create example code snippets for common integration patterns",
            ],
            "tech_stack": ["Markdown", "Docusaurus", "Python"],
            "culture_signals": ["developer-focused", "remote-friendly", "writing-heavy"],
            "comp_range": "$26-32/hr",
            "location_type": "remote",
        },
        "synthesis": {
            "what_they_do": "Quillmark Systems provides a developer API for document generation.",
            "recent_developments": ["Overhauling its public docs site ahead of a v2 API launch"],
            "tech_signals": ["Docusaurus", "Python", "REST APIs"],
            "company_type": "startup",
            "culture_signals": ["developer-focused", "writing-heavy"],
            "likely_role_context": "The intern joins developer relations supporting the docs overhaul for the v2 API launch.",
        },
    },
    # ------------------------------------------------------------------
    # Poor fit (15-20)
    # ------------------------------------------------------------------
    {
        "id": "15_ml_research",
        "jd": {
            "company_name": "Solenne Research",
            "role_title": "Machine Learning Research Intern",
            "team_or_org": "ML Research",
            "must_haves": [
                "Strong background in linear algebra, probability, and optimization",
                "Experience implementing ML models from research papers (PyTorch or JAX)",
                "Currently pursuing a graduate degree (M.S./Ph.D.) in ML, CS, or related field",
            ],
            "nice_to_haves": [
                "Publications or preprints in ML venues",
                "Experience with distributed training",
                "Familiarity with transformer architectures",
            ],
            "responsibilities": [
                "Implement and evaluate novel model architectures from recent papers",
                "Run large-scale training experiments and analyze results",
                "Co-author internal research reports and external publications",
            ],
            "tech_stack": ["PyTorch", "JAX", "CUDA"],
            "culture_signals": ["research-focused", "publication-driven", "PhD-heavy team"],
            "comp_range": "$45-55/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Solenne Research is an AI research lab focused on foundation model architectures.",
            "recent_developments": ["Published a new paper on efficient transformer training"],
            "tech_signals": ["PyTorch", "JAX", "CUDA", "distributed training"],
            "company_type": "startup",
            "culture_signals": ["research-focused", "PhD-heavy team"],
            "likely_role_context": "The intern joins a research pod working on transformer architecture experiments.",
        },
    },
    {
        "id": "16_quant_trading",
        "jd": {
            "company_name": "Castellan Capital",
            "role_title": "Quantitative Trading Intern",
            "team_or_org": "Systematic Trading",
            "must_haves": [
                "Strong background in probability, statistics, and linear algebra",
                "Programming proficiency in Python or C++ for quantitative research",
                "Currently pursuing a degree in Math, Statistics, CS, Physics, or related quantitative field",
            ],
            "nice_to_haves": [
                "Experience with time-series analysis or backtesting frameworks",
                "Competitive math or programming competition background",
                "Familiarity with market microstructure concepts",
            ],
            "responsibilities": [
                "Research and backtest systematic trading signals",
                "Build tooling to analyze strategy performance and risk",
                "Present research findings to senior quant researchers",
            ],
            "tech_stack": ["Python", "C++", "NumPy", "internal backtesting framework"],
            "culture_signals": ["high-performance", "research-driven", "competitive"],
            "comp_range": "$50-65/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Castellan Capital is a systematic trading firm running quantitative strategies across global markets.",
            "recent_developments": ["Expanding its systematic trading research team"],
            "tech_signals": ["Python", "C++", "internal backtesting tools"],
            "company_type": "enterprise",
            "culture_signals": ["high-performance", "competitive", "research-driven"],
            "likely_role_context": "The intern joins the systematic trading research team backtesting new signals.",
        },
    },
    {
        "id": "17_embedded_firmware",
        "jd": {
            "company_name": "Ironvale Robotics",
            "role_title": "Embedded Systems / Firmware Intern",
            "team_or_org": "Firmware",
            "must_haves": [
                "Proficiency in C or C++ for embedded systems",
                "Experience working with microcontrollers (Arduino, STM32, or similar)",
                "Currently pursuing a degree in Electrical Engineering, CS, or related field",
            ],
            "nice_to_haves": [
                "Experience with RTOS concepts",
                "Familiarity with hardware debugging tools (oscilloscope, logic analyzer)",
                "Experience reading schematics",
            ],
            "responsibilities": [
                "Write and debug firmware for sensor modules on a robotics platform",
                "Bring up new hardware revisions and validate sensor readings",
                "Collaborate with hardware engineers on board-level debugging",
            ],
            "tech_stack": ["C", "C++", "STM32", "RTOS"],
            "culture_signals": ["hardware-heavy", "hands-on", "small team"],
            "comp_range": "$32-40/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Ironvale Robotics builds sensor modules for industrial inspection robots.",
            "recent_developments": ["Bringing up a new sensor board revision for field testing"],
            "tech_signals": ["C", "C++", "STM32", "RTOS"],
            "company_type": "startup",
            "culture_signals": ["hardware-heavy", "hands-on"],
            "likely_role_context": "The intern joins the firmware team validating a new sensor board revision.",
        },
    },
    {
        "id": "18_sre",
        "jd": {
            "company_name": "Vantern Systems",
            "role_title": "Site Reliability Engineering Intern",
            "team_or_org": "SRE",
            "must_haves": [
                "Experience operating production services at scale",
                "Proficiency in Go, Python, or similar for tooling and automation",
                "Currently pursuing a degree in Computer Science or related field",
            ],
            "nice_to_haves": [
                "Experience with Kubernetes and service mesh technologies",
                "Familiarity with on-call practices and incident response",
                "Experience with distributed systems concepts (consensus, replication)",
            ],
            "responsibilities": [
                "Build automation to reduce toil for the SRE team",
                "Participate in incident reviews and write postmortems",
                "Improve alerting and dashboards for core production services",
            ],
            "tech_stack": ["Go", "Kubernetes", "Prometheus", "gRPC"],
            "culture_signals": ["high-scale", "on-call rotation", "blameless postmortems"],
            "comp_range": "$40-48/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Vantern Systems operates a high-throughput payments processing platform.",
            "recent_developments": ["Migrating core services to a new service mesh"],
            "tech_signals": ["Go", "Kubernetes", "Prometheus", "gRPC"],
            "company_type": "enterprise",
            "culture_signals": ["high-scale", "blameless postmortems"],
            "likely_role_context": "The intern joins the SRE team building automation around the service mesh migration.",
        },
    },
    {
        "id": "19_cybersecurity_research",
        "jd": {
            "company_name": "Greycastle Security",
            "role_title": "Cybersecurity Research Intern",
            "team_or_org": "Threat Research",
            "must_haves": [
                "Strong understanding of common attack techniques (OWASP Top 10, network attacks)",
                "Experience with penetration testing tools or CTF participation",
                "Currently pursuing a degree in Computer Science, Cybersecurity, or related field",
            ],
            "nice_to_haves": [
                "Security certifications (e.g. CompTIA Security+, OSCP coursework)",
                "Experience with malware analysis or reverse engineering",
                "Familiarity with SIEM tooling",
            ],
            "responsibilities": [
                "Research and document emerging attack techniques",
                "Build proof-of-concept exploits in a controlled lab environment",
                "Contribute findings to the team's threat intelligence reports",
            ],
            "tech_stack": ["Python", "Kali Linux", "Wireshark", "Metasploit"],
            "culture_signals": ["security-focused", "research-driven", "small team"],
            "comp_range": "$36-44/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Greycastle Security provides threat research and penetration testing services to enterprise clients.",
            "recent_developments": ["Growing its threat research team after several new enterprise contracts"],
            "tech_signals": ["Python", "Kali Linux", "Metasploit"],
            "company_type": "startup",
            "culture_signals": ["security-focused", "research-driven"],
            "likely_role_context": "The intern joins the threat research team producing proof-of-concept exploits and reports.",
        },
    },
    {
        "id": "20_robotics_software",
        "jd": {
            "company_name": "Aldercrest Robotics",
            "role_title": "Robotics Software Intern",
            "team_or_org": "Autonomy",
            "must_haves": [
                "Experience with ROS (Robot Operating System)",
                "Proficiency in C++ and Python",
                "Currently pursuing a degree in Robotics, CS, EE, or related field",
            ],
            "nice_to_haves": [
                "Experience with SLAM, path planning, or control systems",
                "Familiarity with simulation environments (Gazebo, Isaac Sim)",
                "Experience with sensor fusion (LiDAR, camera, IMU)",
            ],
            "responsibilities": [
                "Develop and test navigation modules for an autonomous mobile robot",
                "Tune control and path-planning parameters in simulation and on hardware",
                "Debug sensor integration issues across the perception stack",
            ],
            "tech_stack": ["ROS", "C++", "Python", "Gazebo"],
            "culture_signals": ["hands-on", "hardware-in-the-loop testing", "small team"],
            "comp_range": "$34-42/hr",
            "location_type": "onsite",
        },
        "synthesis": {
            "what_they_do": "Aldercrest Robotics builds autonomous mobile robots for warehouse logistics.",
            "recent_developments": ["Piloting a new navigation stack with a logistics customer"],
            "tech_signals": ["ROS", "C++", "Python", "Gazebo"],
            "company_type": "startup",
            "culture_signals": ["hands-on", "hardware-in-the-loop testing"],
            "likely_role_context": "The intern joins the autonomy team testing the new navigation stack pilot.",
        },
    },
]

BATCH_1 = FIXTURES[:10]
BATCH_2 = FIXTURES[10:]
