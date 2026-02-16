# CLAUDE.md

This file provides guidance for AI assistants working with the **data-driven** repository.

## Project Overview

Data analysis project for a **promotions engine** in a betting platform. Uses Python to generate synthetic data and SQL (Databricks) for analysis. Focus areas: funnel analysis, cohort analysis, and promo vs non-promo user comparisons.

## Repository Structure

```
data-driven/
├── README.md                          # Project description
├── CLAUDE.md                          # This file — AI assistant guidance
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
├── scripts/
│   └── generate_data.py               # Synthetic data generator
├── analysis/
│   ├── 00_load_data.sql               # Load CSVs into Databricks tables
│   ├── 01_funnel_analysis.sql         # Promotion funnel conversion
│   ├── 02_cohort_analysis.sql         # Weekly participation cohorts
│   └── 03_promo_vs_no_promo.sql       # Promo users vs non-promo comparison
└── data/                              # Generated CSVs (gitignored)
```

## Tech Stack

- **Python 3.10+** with pandas, numpy, faker for data generation
- **SQL (Databricks)** for analysis queries
- Data stored as CSV, loaded into Databricks tables

## Development Guidelines

Since this project is in its initial phase, follow these principles when contributing:

### General

- Keep changes small and focused
- Write clear, descriptive commit messages
- Prefer simple solutions over complex abstractions

### When Adding New Technologies

- Document the rationale for tech stack choices in commit messages or README
- Include appropriate configuration files (e.g., `package.json`, `requirements.txt`, `tsconfig.json`)
- Set up linting and formatting from the start
- Add a `.gitignore` appropriate for the chosen stack

### When Adding Code

- Establish and follow consistent naming conventions
- Add tests alongside new functionality
- Keep secrets and credentials out of the repository — use environment variables or `.env` files (gitignored)

## Commands

```
pip install -r requirements.txt                  # Install dependencies
python scripts/generate_data.py                  # Generate synthetic data (default: 2000 users, 12 weeks)
python scripts/generate_data.py --users 10000    # Generate with more users
python scripts/generate_data.py --weeks 26       # Generate with more weeks
```
