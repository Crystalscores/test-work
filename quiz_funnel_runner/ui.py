from __future__ import annotations

import asyncio
import json
from pathlib import Path

import streamlit as st

from .config import RunnerConfig
from .runner import run_funnels


def main() -> None:
    st.set_page_config(page_title="Quiz Funnel Runner", page_icon="📱", layout="wide")
    st.title("📱 Quiz Funnel Runner")
    st.caption("MVP UI: run 3–5 quiz funnels in iPhone emulation and collect classified screenshots.")

    with st.form("run_form"):
        urls_text = st.text_area("Funnel URLs (one per line)", height=130)
        col1, col2, col3 = st.columns(3)
        max_steps = col1.slider("Max steps", 1, 50, 20)
        concurrency = col2.slider("Parallel funnels", 1, 5, 3)
        headless = col3.checkbox("Headless", value=False)
        device = st.selectbox("iPhone device", ["iPhone 13", "iPhone 12", "iPhone SE"])
        output_dir = st.text_input("Output folder", value="results")
        submit = st.form_submit_button("Run funnels")

    if submit:
        urls = [line.strip() for line in urls_text.splitlines() if line.strip()]
        if not (1 <= len(urls) <= 5):
            st.error("Введите от 1 до 5 URL.")
            return

        config = RunnerConfig(
            urls=urls,
            max_steps=max_steps,
            concurrency=concurrency,
            headless=headless,
            device=device,
            output_dir=Path(output_dir),
        )

        with st.spinner("Running automation..."):
            summaries = asyncio.run(run_funnels(config))

        st.success("Run finished")
        st.json(summaries)

        for summary in summaries:
            st.subheader(summary["domain"])
            st.write(summary)
            summary_path = Path(output_dir) / summary["domain"] / "summary.json"
            if summary_path.exists():
                st.code(summary_path.read_text(encoding="utf-8"), language="json")


def streamlit_entry() -> None:
    main()


if __name__ == "__main__":
    main()
