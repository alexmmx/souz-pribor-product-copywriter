# Product Copywriter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Создать локальный Python CLI, который генерирует проверенный черновик карточки B2B-товара через OpenAI Responses API и сдаётся как публичный Git-репозиторий.

**Architecture:** Pydantic фиксирует входной и выходной контракты, OpenAI Structured Outputs генерирует только редакционные поля, а сервис детерминированно переносит характеристики и блокирует новые цифровые значения. CLI читает один объект или массив, выводит Markdown/JSON и переводит ошибки в понятные сообщения и коды завершения.

**Tech Stack:** Python 3.11+, OpenAI Python SDK, Pydantic 2, python-dotenv, pytest, Ruff, uv.

**Spec:** `docs/superpowers/specs/2026-11-03-product-copywriter-design.md`

## Global Constraints

- OpenAI API key exists only in environment variables or ignored `.env.local`.
- Default model is `gpt-6.1-sol`; `OPENAI_MODEL` and `--model` can override it.
- SEO title is at most 70 Unicode characters; description is 800-1200 Unicode characters; search query count is 3-5.
- Technical characteristics in the final card come only from input `specs`.
- Any digit-bearing generated token absent from the normalized input rejects the result.
- Responses API requests use Structured Outputs and `store=False`.
- User-facing text, examples, and README are in Russian.

## Review Focus

- Malformed JSON and a top-level scalar must fail before an API call; Task 1 tests both.
- Empty or whitespace-only product name must report the exact item path; Task 1 tests object and batch paths.
- A model response with an ungrounded technical number must be rejected; Task 2 tests model codes, ranges, units, and safe source values.
- OpenAI timeouts, rate limits, authentication/status failures, and refusals must not leak SDK traces; Task 3 tests translated errors.
- CLI output files must not be partially overwritten when generation fails; Task 4 tests atomic write behavior.

---

### Task 1: Project scaffold, input contract, and JSON loader

**Files:**
- Create: `pyproject.toml`
- Create: `src/product_copywriter/__init__.py`
- Create: `src/product_copywriter/errors.py`
- Create: `src/product_copywriter/models.py`
- Create: `src/product_copywriter/input_loader.py`
- Test: `tests/test_input_loader.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `ProductInput`, `GeneratedCopy`, `ProductCard`, `load_products(path: Path) -> list[ProductInput]`, typed application errors.
- Consumes: JSON files shaped as one object or an array of objects.

- [ ] Write failing tests for one product, a product list, malformed JSON, scalar input, whitespace name, and batch item error locations.
- [ ] Run `uv run pytest tests/test_input_loader.py tests/test_models.py -q` and verify failures are caused by missing modules.
- [ ] Add project configuration and the minimal models/loader needed by the tests.
- [ ] Run the same tests and the full suite; expect all passing.
- [ ] Commit `feat: validate product input`.

### Task 2: Prompt, orchestration, and hallucination guard

**Files:**
- Create: `src/product_copywriter/prompts.py`
- Create: `src/product_copywriter/service.py`
- Test: `tests/test_prompts.py`
- Test: `tests/test_service.py`

**Interfaces:**
- Consumes: `ProductInput`, `GeneratedCopy`, a `CopyProvider.generate(product)` protocol.
- Produces: `ProductCardService.generate(product) -> ProductCard`, deterministic characteristics, `validate_grounding(product, copy)`.

- [ ] Write failing tests that the prompt carries source-only rules and exact JSON, characteristics mirror `specs`, missing fields are listed, valid source values pass, and a new numeric value fails.
- [ ] Run the task tests and verify expected missing-symbol failures.
- [ ] Implement the minimal prompt, provider protocol, service, and grounding normalizer.
- [ ] Run task tests and full suite; expect all passing.
- [ ] Commit `feat: ground generated product copy`.

### Task 3: OpenAI Responses API adapter

**Files:**
- Create: `src/product_copywriter/provider.py`
- Test: `tests/test_provider.py`

**Interfaces:**
- Consumes: `ProductInput`, `GeneratedCopy`, OpenAI-compatible client with `responses.create(...)`.
- Produces: `OpenAIProvider.generate(product) -> GeneratedCopy` and stable `ConfigurationError`/`ProviderError` messages.

- [ ] Write failing tests for model/input/schema/store request fields, malformed output, refusal, timeout, rate limit, and status errors using a boundary fake client.
- [ ] Run `uv run pytest tests/test_provider.py -q` and verify missing adapter failures.
- [ ] Implement the provider using `responses.create` with `text.format` JSON Schema and `store=False`.
- [ ] Run task tests and full suite; expect all passing.
- [ ] Commit `feat: add OpenAI Responses provider`.

### Task 4: CLI, renderers, and atomic output

**Files:**
- Create: `src/product_copywriter/renderers.py`
- Create: `src/product_copywriter/cli.py`
- Test: `tests/test_renderers.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `load_products`, `OpenAIProvider`, `ProductCardService`, list of `ProductCard`.
- Produces: `render_markdown(cards)`, `render_json(cards)`, `main(argv: Sequence[str] | None) -> int`, `product-copywriter` console command.

- [ ] Write failing tests for readable Markdown/JSON, stdout, atomic output, model override, invalid input, missing key, and provider failure exit codes.
- [ ] Run task tests and verify failures are from absent CLI/renderers.
- [ ] Implement renderers, dependency-injectable CLI flow, dotenv loading, and atomic file replacement.
- [ ] Run task tests and full suite; expect all passing.
- [ ] Commit `feat: add product copywriter CLI`.

### Task 5: Two real products, generated examples, and handoff documentation

**Files:**
- Create: `examples/input/products.json`
- Create: `examples/output/products.json`
- Create: `examples/output/products.md`
- Create: `README.md`
- Create: `docs/PROMPTING.md`

**Interfaces:**
- Consumes: public YML/product-page facts for two selected products and the completed CLI.
- Produces: runnable demonstration and complete submission documentation.

- [ ] Build two input fixtures from verified СОЮЗ-ПРИБОР source fields without adding unsupported facts.
- [ ] Run the real CLI once through OpenAI for both products and save JSON and Markdown outputs.
- [ ] Validate title/description/query counts and grounding for saved outputs.
- [ ] Document installation, commands, prompt strategy, decisions, limitations, improvements, examples, and error behavior.
- [ ] Run `uv run ruff check .`, `uv run pytest -q`, CLI help, example JSON replay, and repository secret scan; expect clean results.
- [ ] Commit `docs: add examples and submission guide`.

### Task 6: Project checks and GitHub publication

**Files:**
- Modify only files required by verification findings.

**Interfaces:**
- Consumes: complete feature branch.
- Produces: reviewed public GitHub repository on `main`.

- [ ] Run the file-aware Bitrix Vibe test plan and all relevant safe checks.
- [ ] Perform whole-branch code review; fix Critical/Important findings through RED-GREEN tests.
- [ ] Run final full suite, Ruff, packaging smoke test, `bitrix-vibe verify`, and `bitrix-vibe health`.
- [ ] Create a new public GitHub repository under the authenticated user, push verified `main`, and verify remote file visibility plus absence of `.env.local`.
- [ ] Commit any verification-only fixes and report the repository URL.
