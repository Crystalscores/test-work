# Quiz Funnel Runner (MVP)

Асинхронный инструмент для автопрохождения квиз-воронок с мобильной эмуляцией iPhone, скриншотами каждого шага, классификацией экранов и сохранением результатов в удобной структуре.

## Что делает проект

- Принимает до 5 URL квиз-воронок.
- Запускает каждую воронку в **Playwright** с эмуляцией iPhone.
- Автоматически двигается по шагам до `max_steps` или до обнаружения paywall.
- Делает скриншот каждого шага.
- Классифицирует экран по типам:
  - `question`
  - `info`
  - `input`
  - `email`
  - `paywall`
  - `other`
- Дублирует скриншоты в папки классификации.
- Сохраняет `log.txt` и `summary.json` по каждой воронке.

## Архитектура

```text
quiz_funnel_runner/
  config.py       # Pydantic-конфиг + JSON loader
  classifier.py   # Rule-based классификация + extraction price
  actions.py      # Логика кликов/заполнения/закрытия popups
  runner.py       # Асинхронный engine Playwright
  cli.py          # CLI интерфейс
  ui.py           # Streamlit UI
```

### Flow выполнения

1. Загрузка конфигурации (CLI args или JSON).
2. Старт Playwright Chromium.
3. Параллельный запуск воронок (`asyncio` + semaphore).
4. Для каждого шага:
   - обработка popup/cookie;
   - сбор HTML/text;
   - классификация;
   - скриншот;
   - действие по типу экрана;
   - логирование.
5. Остановка при paywall.
6. Запись `summary.json`.

## Почему выбран стек

- **Python**: быстрое MVP и хорошая экосистема для automation.
- **Playwright**: надежная браузерная автоматизация + мобильная эмуляция.
- **asyncio**: конкурентный запуск 3–5 воронок.
- **Streamlit**: быстрый и понятный UI без избыточной frontend-разработки.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

## Использование (CLI)

```bash
quiz-runner https://example-funnel-1.com https://example-funnel-2.com \
  --max-steps 20 \
  --concurrency 3 \
  --output-dir results
```

### Через JSON-конфиг

`config.json`:

```json
{
  "urls": [
    "https://example-funnel-1.com",
    "https://example-funnel-2.com"
  ],
  "max_steps": 20,
  "concurrency": 3,
  "headless": false,
  "output_dir": "results",
  "device": "iPhone 13"
}
```

Запуск:

```bash
quiz-runner --config config.json
```

## Использование (UI)

```bash
streamlit run quiz_funnel_runner/ui.py
```

В UI можно:
- вставить URL списком,
- выбрать `max_steps`, `concurrency`, `headless`, `device`,
- запустить и посмотреть JSON-результат.

## Структура результатов

```text
results/
  domain-name/
    01_question.png
    02_input.png
    log.txt
    summary.json
  _classified/
    question/
      domain-name-01-question.png
    info/
    input/
    email/
    paywall/
    other/
```

## Ограничения MVP

- Классификация сейчас в основном rule-based.
- Эвристики кликов универсальны, но не покрывают 100% кастомных UI.
- Не все SPA одинаково стабильно дают `networkidle`.

## Что улучшить при масштабировании

- Добавить отдельный ML/LLM-классификатор с уверенностью и explainability.
- Улучшить анти-флейки слой (ретраи, smart wait policies).
- Добавить storage backend (S3 + Postgres) для большой истории прогонов.
- Поддержка очередей задач (Celery/RQ/Temporal).

## Где использован AI

- Возможность включить `llm_enabled` в конфиг уже предусмотрена в архитектуре и кэше классификатора.
- В текущем MVP fallback выполнен rule-based логикой для стабильности и скорости.
