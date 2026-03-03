from __future__ import annotations

import asyncio
import json
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import Browser, Error, Playwright, async_playwright
from rich.console import Console

from .actions import close_popups, execute_step_action
from .classifier import HtmlClassifier, SCREEN_TYPES
from .config import RunnerConfig

console = Console()


@dataclass
class StepRecord:
    step: int
    screen_type: str
    url: str
    screenshot: str
    action: str
    error: str = ""


async def run_funnels(config: RunnerConfig) -> list[dict[str, Any]]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    classifier = HtmlClassifier(llm_enabled=config.llm_enabled)
    semaphore = asyncio.Semaphore(config.concurrency)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.headless)
        tasks = [run_single_funnel(browser, p, semaphore, config, classifier, url) for url in config.urls]
        results = await asyncio.gather(*tasks)
        await browser.close()
    return results


async def run_single_funnel(
    browser: Browser,
    playwright: Playwright,
    semaphore: asyncio.Semaphore,
    config: RunnerConfig,
    classifier: HtmlClassifier,
    url: str,
) -> dict[str, Any]:
    async with semaphore:
        domain = normalize_domain(url)
        folder = config.output_dir / domain
        classified_root = config.output_dir / "_classified"
        for t in SCREEN_TYPES:
            (classified_root / t).mkdir(parents=True, exist_ok=True)
        folder.mkdir(parents=True, exist_ok=True)

        log_path = folder / "log.txt"
        steps: list[StepRecord] = []
        types = Counter()
        paywall_detected = False
        price_detected = ""

        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write(f"Started at {datetime.utcnow().isoformat()}Z\n")
            device = playwright.devices[config.device]
            context = await browser.new_context(**device)
            page = await context.new_page()
            last_url = ""
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
                await page.wait_for_load_state("networkidle", timeout=15_000)
            except Exception as exc:
                log_file.write(f"Failed to open {url}: {exc}\n")

            for step in range(1, config.max_steps + 1):
                current_url = page.url
                try:
                    await close_popups(page)
                    await page.wait_for_timeout(500)
                    html = await page.content()
                    text = await page.inner_text("body")
                    result = classifier.classify(current_url, html, text)
                    if result.price_detected and not price_detected:
                        price_detected = result.price_detected
                    screen_type = result.screen_type
                    paywall_detected = screen_type == "paywall"

                    filename = f"{step:02d}_{screen_type}.png"
                    screenshot_path = folder / filename
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                    duplicated = classified_root / screen_type / f"{domain}-{step:02d}-{screen_type}.png"
                    duplicated.write_bytes(screenshot_path.read_bytes())

                    action = "stop-on-paywall"
                    if not paywall_detected:
                        action = await execute_step_action(page, screen_type)
                        await page.wait_for_timeout(900)

                    record = StepRecord(
                        step=step,
                        screen_type=screen_type,
                        url=current_url,
                        screenshot=str(screenshot_path),
                        action=action,
                    )
                    steps.append(record)
                    types[screen_type] += 1
                    log_file.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

                    if paywall_detected:
                        break

                    if last_url == page.url and action == "no-action":
                        log_file.write("No progress detected, continue to next step.\n")
                    last_url = page.url
                except Error as exc:
                    err = f"Playwright error on step {step}: {exc}"
                    log_file.write(err + "\n")
                    steps.append(StepRecord(step=step, screen_type="other", url=current_url, screenshot="", action="error", error=err))
                    types["other"] += 1
                except Exception as exc:  # noqa: BLE001
                    err = f"Unexpected error on step {step}: {exc}"
                    log_file.write(err + "\n")
                    steps.append(StepRecord(step=step, screen_type="other", url=current_url, screenshot="", action="error", error=err))
                    types["other"] += 1

            await context.close()

        summary = {
            "domain": domain,
            "steps": len(steps),
            "paywall_detected": paywall_detected,
            "types_distribution": dict(types),
            "price_detected": price_detected,
            "source_url": url,
        }
        (folder / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"[green]Done[/green] {domain} steps={summary['steps']} paywall={summary['paywall_detected']}")
        return summary


def normalize_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    safe = domain.replace(":", "_").replace("/", "_")
    return safe or "unknown-domain"
