"""
q3_multilingual/indonesia/system_prompt.py — Bahasa Indonesia localization.

Defines the system prompt for an Indonesian Multifinance voice bot.
Enforces Indonesian cultural nuances, English loanwords, and appropriate register.
"""

from pathlib import Path

_PROMPT_PATH = Path(__file__).parent / "prompt.md"
with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_ID = f.read()

INITIAL_MESSAGE_ID = "Selamat siang Bapak/Ibu. Saya Budi dari tim pembiayaan. Mohon maaf mengganggu waktunya nggih, apakah berkenan berbicara sebentar mengenai cicilan bulan ini toh?"
