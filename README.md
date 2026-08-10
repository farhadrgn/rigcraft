# RigCraft

A PC gaming component compatibility checker and build planner, built with Django. Users
pick a target resolution, then choose GPU → CPU → Motherboard → Cooler → RAM → Storage →
PSU → Case one step at a time; incompatible options are grayed out live as they go, and
the finished build gets a bottleneck read and per-game FPS estimates.

Built as my final project for CS50W.

## Distinctiveness and Complexity

This project is neither an e-commerce site nor a social network / forum, and it is not a
close relative of any other project in the course (it is not a to-do list, blog, or
messaging app).

**A real, multi-rule constraint-satisfaction engine, not a form.** Nine independent
compatibility rules (socket matching, dual DDR support checks, cooler TDP/socket fit,
physical GPU/radiator clearance, PSU headroom) run entirely server-side against a
category-keyed selection, returning structured `{reason_code, message}` violations. A
separate, purely informational bottleneck engine compares CPU/GPU benchmark percentiles
with resolution-dependent sensitivity weighting. Both are backed by real, independently
sourced data (PassMark CPU scores, TechPowerUp GPU specs, manufacturer spec sheets, and
per-game FPS benchmarks from exo.ir) loaded into PostgreSQL — not placeholder or
randomly generated data.

**A 9-step wizard with live, bidirectional-aware revalidation, built entirely in vanilla
JavaScript.** As each component is picked, the wizard re-checks compatibility for every
still-unpicked candidate in the current step by calling the server's `/builder/check/`
endpoint once per candidate, in parallel (`Promise.all`), and grays out any candidate
that would introduce a violation -- with the server's exact message shown as a tooltip.
No compatibility logic is duplicated on the client. Going back and changing an earlier
choice re-validates (and selectively clears, never wholesale resets) later choices,
strictly in wizard order, rather than forcing the user to restart. This is meaningfully
more complex than typical CRUD-with-JS-polish coursework: it required deliberately
working around the constraint of "no client-side compatibility logic at all" while still
delivering real-time predictive UI feedback.

**Full account-aware CRUD with correct ownership boundaries.** Builds can be created and
explored as a guest, but saving, listing, viewing, editing, and deleting builds all
require ownership checks that return 404 (not 403) for another user's build, to avoid
leaking existence -- consistent with security-conscious API design.

## Project Structure

- `config/` -- project settings, root URL configuration
- `components/` -- the 8 hardware category models (GPU, CPU, Motherboard, CPUCooler,
  RAM, Storage, PSU, Case) plus `GPUBenchmark`, fixture data, and Django admin
- `compatibility/` -- the 9 pure compatibility rule functions, the category-keyed
  dispatcher, the bottleneck formula, and the `/builder/check/` JSON endpoint
- `builds/` -- the `Build` model, the wizard view, save/list/detail/edit/delete views,
  and their templates
- `users/` -- a custom `User` model (no extra fields, defined from day one to keep the
  door open for future fields without a disruptive migration) and registration
- `templates/` -- shared layout (`base.html`), per-app templates, custom `404.html`
- `static/css/`, `static/js/` -- hand-written CSS (Material Dark-inspired, blue accent)
  and the wizard's vanilla JS (`builder.js`)
- `build_fixtures.py` -- a one-time data transformation script that converts the raw,
  independently-sourced JSON files in `components-data/` into a proper Django fixture

## How to Run Locally

Requires Python 3.14, PostgreSQL 17, and no other services (no Docker, no Node).

```bash
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt  # or: pip install "Django>=5.2,<6.0" django-environ psycopg2-binary

# Create the database and role in psql, matching .env.example, then:
python manage.py migrate
python manage.py loaddata components/fixtures/components_data.json
python manage.py createsuperuser
python manage.py runserver
```

Copy `.env.example` to `.env` and fill in real values (a generated `SECRET_KEY` and your
own database credentials) before running the commands above.

## Design Decisions Worth Knowing About

- **The bottleneck formula is a reasoned heuristic, not an industry-standard
  benchmark model.** No official standard exists for quantifying "bottleneck severity."
  The resolution-sensitivity multipliers and Minor/Major thresholds are estimates based
  on the general principle that games lean more CPU-bound at 1080p and more GPU-bound at
  4K -- they have not been calibrated against real review data. This is intentional and
  disclosed rather than presented as authoritative.
- **Django server-rendered templates + vanilla JS, not React/DRF.** An earlier prototype
  used React, DRF, JWT auth, and Docker; that stack was deliberately abandoned in favor
  of this simpler, fully server-rendered architecture, matching the course's own
  Django-based projects and keeping the whole stack auditable without a build step.
- **GPU catalog intentionally limited to the RTX 50 series and RX 9000 series** (9 cards
  total) rather than an exhaustive historical catalog, to keep the dataset a deliberately
  curated, verifiable sample rather than a sprawling and harder-to-verify one.
- **The DDR4 subset (2 motherboards, 2 RAM kits) is intentionally small.** It exists
  specifically to demonstrate the RAM/CPU/motherboard DDR-generation compatibility rule,
  not as general support for older hardware.
- **No pricing or shop links.** Removed from scope entirely -- this project answers
  "will these parts work together," not "what should I buy them for."

## Deliberately Out of Scope

- **Deployment.** This README describes local development only. No hosting, WSGI/ASGI
  production server, or environment-specific configuration beyond `DEBUG=False`
  readiness is included.
- **Calibrating the bottleneck formula against real review/benchmark data.** The current
  thresholds and multipliers are reasoned estimates, clearly documented as such above.
- **Automated linting/formatting tooling** (black, eslint/prettier) was not set up.
- **API versioning, CI/CD, and OpenAPI/Swagger documentation** do not apply to this
  architecture at all -- there is no DRF/API layer to version or document. Their absence
  is a consequence of the Django-templates architecture choice, not an oversight.
- **Pricing/shop links and a JS-framework or DRF-based rebuild** were considered and
  consciously set aside; either could be revisited later as a distinct, separate effort.

## Demo Video

[Link to be added after recording.]
