# RigCraft

A PC gaming component compatibility checker and build planner, built with Django. Users
pick a target resolution, then choose GPU → CPU → Motherboard → Cooler → RAM → Storage →
PSU → Case one step at a time; incompatible options are grayed out live as they go, and
the finished build gets a bottleneck read and per-game FPS estimates.

Built as my final project for CS50W.

## Distinctiveness and Complexity

This project is neither an e-commerce site nor a social network / forum, and it is not a
close relative of any other project in the course (it is not a to-do list, blog, or
messaging app). It may look e-commerce-adjacent at a glance -- a user picks hardware
components, after all -- but there is no cart, checkout, payment, pricing, or purchasing
flow anywhere in the app; every screen answers "will these parts work together," never
"how much does this cost" or "how do I buy it." That's a deliberate scope boundary, not
an oversight (see "Deliberately Out of Scope" below).

**A real, multi-rule constraint-satisfaction engine, not a form.** Nine independent
compatibility rules (socket matching, dual DDR support checks, cooler TDP/socket fit,
physical GPU/radiator clearance, PSU headroom) run entirely server-side against a
category-keyed selection, returning structured `{reason_code, message}` violations. A
separate, purely informational bottleneck engine looks up empirically observed
CPU/GPU/resolution results from manually testing the full catalog, rather than computing
a live formula (see "Design Decisions" below for why). Both are backed by real,
independently sourced data (PassMark CPU scores, TechPowerUp GPU specs, manufacturer
spec sheets, and per-game FPS benchmarks from exo.ir) loaded into PostgreSQL — not
placeholder or randomly generated data.

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
  dispatcher, the empirically-tested bottleneck lookup table, and the `/builder/check/`
  JSON endpoint
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
python manage.py loaddata compatibility/fixtures/bottleneck_exceptions.json
python manage.py createsuperuser
python manage.py runserver
```

Copy `.env.example` to `.env` and fill in real values (a generated `SECRET_KEY` and your
own database credentials) before running the commands above.

## Design Decisions Worth Knowing About

- **The bottleneck engine is an empirically tested lookup table, not a benchmark-ratio
  formula -- and that wasn't the original design.** The first version compared each
  CPU's and GPU's benchmark score as a percentage of the strongest part in its category,
  then weighted the gap between those two percentages by a resolution-dependent
  multiplier. That formula's output didn't hold up under scrutiny: it assumes a CPU's
  single-thread benchmark score is a reliable stand-in for its real gaming performance,
  and testing showed that assumption breaks down across different CPU microarchitectures.
  Two concrete, independently documented examples surfaced while investigating: Intel's
  Arrow Lake generation (Core Ultra 200S) is publicly known to underperform its own
  benchmark scores in games relative to the previous generation, and AMD's dual-CCD
  Ryzen 9 chips (9900X, 9950X) can score inconsistently against each other and against
  weaker single-CCD siblings, due to documented cross-CCD latency and core-parking
  behavior in early Zen 5 platforms. Neither pattern can be expressed by a formula built
  on benchmark percentiles alone. So the formula was scrapped in favor of testing real
  combinations directly: for each CPU microarchitecture family, the weakest CPU in the
  catalog was tested against every GPU at every resolution first; if that weakest CPU
  showed no bottleneck (or only a minor one), stronger CPUs in the same family were
  assumed to do at least as well and were not individually tested, since a stronger part
  in the same architecture shouldn't bottleneck where a weaker one already didn't. Every
  case that did show a bottleneck, and every different architecture family, was tested
  directly. The actual observed result for each tested case was recorded directly
  (`BottleneckException` model, populated from a generated fixture, not hand-typed, to
  avoid transcription errors). Any combination with no matching row -- whether tested and
  passing, or inferred from a same-family weaker CPU passing -- defaults to Balanced.
  Cyberpunk 2077 was chosen as the one reference game for this testing specifically
  because it's a demanding, graphically-heavy AAA title without leaning as hard toward
  either CPU-bound or GPU-bound extremes as some other games sampled during exploration,
  keeping results reasonably representative rather than a best- or worst-case outlier.
  The Balanced / Minor / Major cutoffs (94% / 84% GPU utilization observed at fixed
  settings) are this project's own thresholds, not pulled from any third-party
  classification scheme. **This table is a helpful reference, not a precise guarantee:**
  it reflects one game at one settings profile (Ultra quality, no upscaling, no ray
  tracing), and real bottleneck severity can shift meaningfully with a different game,
  quality preset, or upscaling setting than what was tested here.
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
- **Testing the bottleneck table against more than one reference game.** The lookup
  table reflects observed results in a single title (Cyberpunk 2077) at fixed settings.
  Real testing during development showed GPU utilization for identical hardware can swing
  by 60+ percentage points between games depending on how CPU- or GPU-heavy a title is --
  so these results are a reasonable single-game reference point, not a cross-game
  average or a guarantee for every title.
- **Automated linting/formatting tooling** (black, eslint/prettier) was not set up.
- **API versioning, CI/CD, and OpenAPI/Swagger documentation** do not apply to this
  architecture at all -- there is no DRF/API layer to version or document. Their absence
  is a consequence of the Django-templates architecture choice, not an oversight.
- **Pricing/shop links and a JS-framework or DRF-based rebuild** were considered and
  consciously set aside; either could be revisited later as a distinct, separate effort.

## Demo Video

[RigCraft demo video](https://youtu.be/JJcLvYzh9n8)
