"""
q3_multilingual/philippines/system_prompt.py — Taglish localization for PH market.

Defines the system prompt for a Philippines Bancassurance / Life Insurance voice bot.
Enforces cultural tone, natural Taglish code-switching, and local finance terminology.
"""

from pathlib import Path

_PROMPT_PATH = Path(__file__).parent / "prompt.md"
with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_PH = f.read()

INITIAL_MESSAGE_PH = "Hello po, magandang araw! Tumatawag po ako mula sa Bancassurance team natin. Do you have a few minutes to discuss your policy?"
