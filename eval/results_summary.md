# Material Quality Eval — Results Summary

Generated from 20 tailored outputs and 20 baseline outputs.

## Headline metric: factual grounding

- **Anchor (Resume Tailorer + Grounding Critic, 1 retry max)**: 2/20 (10%) passed grounding, 74 total violation(s) across all attempts, 18 escalated (failed even after retry).
- **Baseline (single-prompt, no critic, no grounding instructions)**: 0/20 (0%) passed grounding, 53 total violation(s).

## Match score distribution (Anchor)

- `01_fullstack_startup` — Brightloop / Software Engineering Intern - Full Stack: score=73 tier=warm
- `02_pm_intern_startup` — Tindergrove Labs / Product Management Intern: score=73 tier=warm
- `03_devex_ai_tools` — Pathwright / Developer Experience Intern: score=73 tier=hot
- `04_program_coordinator` — Civora Education / Technical Program Coordinator Intern: score=73 tier=warm
- `05_qa_testing` — Ferrowell Systems / Software Testing Intern: score=73 tier=warm
- `06_web_platform` — Reedmark / Software Engineering Intern - Web Platform: score=74 tier=warm
- `07_community_ops` — Fernbridge Foundation / Community & Operations Intern: score=58 tier=cold
- `08_ai_tools_eng` — Lucenta AI / AI Tools Engineering Intern: score=73 tier=warm
- `09_backend_fastapi` — Coalwright Health / Backend Engineering Intern: score=78 tier=hot
- `10_data_analyst` — Marlstone Retail / Data Analyst Intern: score=74 tier=warm
- `11_mobile_dev` — Hollowmere Apps / Mobile App Development Intern: score=73 tier=warm
- `12_devops_infra` — Northgate Cloud / DevOps / Infrastructure Intern: score=73 tier=warm
- `13_frontend_react` — Verdant Studio / Frontend Engineering Intern: score=73 tier=warm
- `14_technical_writing` — Quillmark Systems / Technical Writing Intern: score=78 tier=hot
- `15_ml_research` — Solenne Research / Machine Learning Research Intern: score=85 tier=hot
- `16_quant_trading` — Castellan Capital / Quantitative Trading Intern: score=75 tier=hot
- `17_embedded_firmware` — Ironvale Robotics / Embedded Systems / Firmware Intern: score=78 tier=hot
- `18_sre` — Vantern Systems / Site Reliability Engineering Intern: score=79 tier=hot
- `19_cybersecurity_research` — Greycastle Security / Cybersecurity Research Intern: score=73 tier=warm
- `20_robotics_software` — Aldercrest Robotics / Robotics Software Intern: score=75 tier=hot

## Per-application detail

| id | company | role | match score | tier | grounding (Anchor) | grounding (baseline) |
|---|---|---|---|---|---|---|
| 01_fullstack_startup | Brightloop | Software Engineering Intern - Full Stack | 73 | warm | fail (2) | fail (1) |
| 02_pm_intern_startup | Tindergrove Labs | Product Management Intern | 73 | warm | fail (2) | fail (3) |
| 03_devex_ai_tools | Pathwright | Developer Experience Intern | 73 | hot | fail (5) | fail (2) |
| 04_program_coordinator | Civora Education | Technical Program Coordinator Intern | 73 | warm | fail (3) | fail (3) |
| 05_qa_testing | Ferrowell Systems | Software Testing Intern | 73 | warm | pass (0) | fail (3) |
| 06_web_platform | Reedmark | Software Engineering Intern - Web Platform | 74 | warm | fail (4) | fail (3) |
| 07_community_ops | Fernbridge Foundation | Community & Operations Intern | 58 | cold | fail (4) | fail (3) |
| 08_ai_tools_eng | Lucenta AI | AI Tools Engineering Intern | 73 | warm | fail (3) | fail (4) |
| 09_backend_fastapi | Coalwright Health | Backend Engineering Intern | 78 | hot | pass (0) | fail (1) |
| 10_data_analyst | Marlstone Retail | Data Analyst Intern | 74 | warm | fail (5) | fail (3) |
| 11_mobile_dev | Hollowmere Apps | Mobile App Development Intern | 73 | warm | fail (6) | fail (3) |
| 12_devops_infra | Northgate Cloud | DevOps / Infrastructure Intern | 73 | warm | fail (6) | fail (3) |
| 13_frontend_react | Verdant Studio | Frontend Engineering Intern | 73 | warm | fail (4) | fail (3) |
| 14_technical_writing | Quillmark Systems | Technical Writing Intern | 78 | hot | fail (5) | fail (2) |
| 15_ml_research | Solenne Research | Machine Learning Research Intern | 85 | hot | fail (4) | fail (3) |
| 16_quant_trading | Castellan Capital | Quantitative Trading Intern | 75 | hot | fail (2) | fail (3) |
| 17_embedded_firmware | Ironvale Robotics | Embedded Systems / Firmware Intern | 78 | hot | fail (3) | fail (3) |
| 18_sre | Vantern Systems | Site Reliability Engineering Intern | 79 | hot | fail (6) | fail (2) |
| 19_cybersecurity_research | Greycastle Security | Cybersecurity Research Intern | 73 | warm | fail (6) | fail (2) |
| 20_robotics_software | Aldercrest Robotics | Robotics Software Intern | 75 | hot | fail (4) | fail (3) |
