# PayOptimise Suite
### MS5132 Major ISM Project — University of Galway 2025–2026
**Jane Donisha Masila Clement Valavan**
<img width="1080" height="1350" alt="image" src="https://github.com/user-attachments/assets/7a335e6a-cd7d-4578-b7a0-c5c60d499446" />

---

## What this is

A full-stack, launch-ready web application implementing a unified data-driven optimisation suite for digital payment platforms. Three AI systems — an A/B experimentation engine, a hybrid recommendation engine, and a funnel analytics module — are integrated through a shared feature store architecture.

**Research context:** This suite is the artefact produced by the MS5132 Major ISM Project:  
*"Enhancing User Journey Efficiency in Digital Payments through a Data-Driven Optimisation Suite"*
<img width="1080" height="1350" alt="image" src="https://github.com/user-attachments/assets/e5268557-0d89-4d59-a796-ae8b31589aa8" />

---

## Quick start

```bash
# 1. Install dependencies (Python 3.9+)
pip install -r requirements.txt

# 2. Launch
python app.py
# OR
bash launch.sh

# 3. Open browser
open http://localhost:5000
```
<img width="1080" height="1350" alt="image" src="https://github.com/user-attachments/assets/9767dbf2-d717-4ab2-ab6a-e69dab787e1d" />

---

## Project structure

```
payoptimise-suite/
│
├── app.py                      # Flask application — main entry point
├── requirements.txt            # Python dependencies
├── launch.sh                   # One-click launch script
│
├── backend/
│   ├── __init__.py
│   ├── data_generator.py       # Synthetic 20,000-session dataset generator
│   ├── ab_engine.py            # A/B experimentation engine (chi-square + Cohen's h)
│   ├── recommender.py          # Hybrid recommendation engine + shared feature store
│   ├── funnel_analytics.py     # Funnel drop-off analysis + friction alerts
│   └── database.py             # SQLite ORM — sessions, experiments, alerts
│
├── database/
│   └── schema.sql              # Full SQL schema — 5 tables, 4 indexes, 2 views
│
└── frontend/
    ├── base.html               # Jinja2 base template with sidebar navigation
    ├── index.html              # Home / landing page
    ├── dashboard.html          # Funnel analytics dashboard
    ├── experiments.html        # A/B experiment results
    ├── recommendations.html    # Recommendation engine explorer
    ├── simulator.html          # Live payment journey simulator
    ├── css/
    │   └── main.css            # Complete dark-mode design system (CSS variables)
    └── js/
        └── utils.js            # Shared API client, chart utilities, DOM helpers
```
<img width="1080" height="1350" alt="image" src="https://github.com/user-attachments/assets/6ce8aeec-86a4-45a4-83cf-1d4897bcefee" />

---

## Pages

| URL | Description |
|-----|-------------|
| `http://localhost:5000/` | Home — suite overview, live key metrics |
| `http://localhost:5000/dashboard` | Funnel analytics — drop-off charts, condition comparison |
| `http://localhost:5000/experiments` | A/B experiments — all 3 results, time-series, methodology |
| `http://localhost:5000/recommendations` | Recommendation engine — live scoring, feature importance |
| `http://localhost:5000/simulator` | Live simulator — configure and run payment journeys |

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Summary statistics from 20,000-session dataset |
| GET | `/api/funnel` | Funnel drop-off data, alerts, 3-condition comparison |
| GET | `/api/funnel?segment=device&value=mobile` | Segmented funnel (mobile/desktop) |
| GET | `/api/funnel/cohort?col=device` | Cohort comparison by column |
| GET | `/api/experiments` | All 3 A/B experiment results |
| POST | `/api/experiments/run` | Run a custom A/B experiment |
| GET | `/api/recommend?device=mobile&hour=13` | Live payment method recommendations |
| GET | `/api/recommend/ctr` | Recommendation CTR evaluation |
| GET | `/api/recommend/features` | Feature importance weights |
| GET | `/api/db/sessions` | Recent logged sessions from database |
| GET | `/api/db/stats` | Database-level aggregated statistics |
| POST | `/api/db/log` | Log a session to the database |
| POST | `/api/simulate` | Run a payment journey simulation |

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend framework | Flask 3.0 (Python) |
| Data science | NumPy, Pandas, SciPy |
| Database | SQLite (dev) — schema compatible with PostgreSQL |
| Frontend | Vanilla HTML5 + CSS3 + JavaScript (ES2022) |
| Charts | Chart.js 4.4.1 (CDN) |
| Templating | Jinja2 (via Flask) |
| Fonts | Inter (Google Fonts) |

---

## Key results (from research manuscript)

| Experiment | Control | Treatment | p-value | Effect |
|---|---|---|---|---|
| Authentication: OTP vs Biometric | 61.2% | 73.4% | < 0.001 | h=0.18 medium |
| Onboarding: 4-step vs 2-step | 68.7% | 84.1% | < 0.001 | h=0.22 medium |
| Recommendations: Generic vs Personalised | 11.7% CTR | 24.3% CTR | < 0.001 | h=0.31 large |

| Condition | Conversion | Rec CTR | Auth drop |
|---|---|---|---|
| Baseline | 43.3% | 11.7% | 37.1% |
| Siloed | 51.4% | 19.8% | 28.6% |
| **Integrated** | **58.7%** | **24.3%** | **21.4%** |

**Integration advantage: +7.3pp over siloed (answers RQ1)**  
**Feature store boost: +8.4% CTR from real-time signals (answers RQ2)**
<img width="1080" height="1350" alt="image" src="https://github.com/user-attachments/assets/27b699d3-eac0-4cfe-99b9-4fc7dc5c685a" />

---

## Recommendation scoring formula

```python
score = 0.40 × collaborative_signal   # past payment preference history
      + 0.31 × device_match_signal    # mobile=1-tap, desktop=bank/card
      + 0.22 × time_context_signal    # peak hours 12-14, 19-21 → 1.0×
      + 0.07 × session_depth_signal   # page_depth / 5.0 (intent proxy)
```

---

## Database schema (SQLite)

5 tables: `sessions`, `experiment_results`, `recommendations`, `friction_alerts`, `feature_store`  
4 indexes for query performance  
2 views: `funnel_summary`, `device_performance`  
Full schema: `database/schema.sql`

---

## Theoretical foundations

| Theory | Source | Application |
|---|---|---|
| Cognitive load theory | Sweller et al., 2019 | Authentication drop-off probabilities |
| Dual-process theory | Kahneman, 2011 | System 1 vs System 2 payment behaviour |
| Technology acceptance model | Davis, 1989 | Ease of use → conversion |
| Causal inference | Imbens & Rubin, 2015 | A/B engine statistical framework |
| Process optimisation | Dumas et al., 2018 | Funnel as business process |
| Design Science Research | Hevner et al., 2004 | Overall research methodology |

---

## References

- Hevner, A.R. et al. (2004) 'Design science in information systems research', *MIS Quarterly*, 28(1), pp. 75–105.
- Imbens, G.W. and Rubin, D.B. (2015) *Causal Inference for Statistics*. Cambridge UP.
- Jordon, J. et al. (2022) 'Synthetic data for machine learning', *ACM Computing Surveys*, 55(11).
- Kahneman, D. (2011) *Thinking, Fast and Slow*. Farrar, Straus and Giroux.
- Kou, G. and Lu, Y. (2025) 'FinTech: a literature review', *Financial Innovation*, 11.
- Mendonça, G. et al. (2023) 'Hybrid recommender systems at PicPay', *arXiv:2310.10268*.
- Quin, F. et al. (2024) 'A/B testing: a systematic literature review', *JSS*, 211.
- Sweller, J. et al. (2019) *Cognitive Load Theory*. Springer.
- Yin, J. et al. (2025) 'AI-personalized recommendations on consumer click intention', *JTAER*, 20(1).
- Zhao, Y. et al. (2025) 'LLM-GNN financial recommendations', *arXiv:2506.05873*.
