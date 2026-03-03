from __future__ import annotations

from playwright.async_api import Page

DEFAULT_INPUTS = {
    "name": "John",
    "height": "170",
    "weight": "65",
    "age": "30",
    "email": "test@example.com",
}

NEXT_SELECTORS = [
    "button:has-text('Continue')",
    "button:has-text('Next')",
    "button:has-text('Start')",
    "button:has-text('Submit')",
    "[role='button']:has-text('Continue')",
    "[role='button']:has-text('Next')",
    "button",
    "a[role='button']",
]


async def close_popups(page: Page) -> None:
    for selector in [
        "button:has-text('Accept')",
        "button:has-text('I agree')",
        "button:has-text('Allow all')",
        "button:has-text('Close')",
        "[aria-label='Close']",
    ]:
        loc = page.locator(selector).first
        if await loc.count() and await loc.is_visible():
            await loc.click(force=True)


async def execute_step_action(page: Page, screen_type: str) -> str:
    if screen_type == "question":
        options = page.locator("input[type='radio'], button, [role='radio'], [role='option']")
        if await options.count():
            await options.first.click(force=True)
            return "clicked first option"

    if screen_type in {"input", "email"}:
        await fill_inputs(page, email_only=(screen_type == "email"))

    action = await click_next(page)
    return action or "no-action"


async def fill_inputs(page: Page, email_only: bool = False) -> None:
    inputs = page.locator("input")
    count = await inputs.count()
    for idx in range(count):
        element = inputs.nth(idx)
        input_type = (await element.get_attribute("type") or "text").lower()
        name = (await element.get_attribute("name") or "").lower()
        placeholder = (await element.get_attribute("placeholder") or "").lower()
        target = f"{name} {placeholder}"
        value = DEFAULT_INPUTS["email"] if input_type == "email" or "email" in target else DEFAULT_INPUTS["name"]
        if not email_only or value == DEFAULT_INPUTS["email"]:
            await element.fill(value)


async def click_next(page: Page) -> str:
    for selector in NEXT_SELECTORS:
        loc = page.locator(selector).first
        if await loc.count() and await loc.is_visible():
            await loc.click(force=True)
            return f"clicked {selector}"
    return ""
