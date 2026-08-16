"""
System prompts for Martin.
"""
from app.core.config import get_config


def get_system_prompt() -> str:
    """Get the system prompt from configuration."""
    config = get_config()
    return config.get("ai", "system_prompt", default="""
Jsi Martin, lokální osobní AI asistent.
Tvé jméno je Martin.
Odpovídej primárně v češtině, pokud uživatel nemluví jiným jazykem.
Buď užitečný a stručný.
Nevymýšlej informace.
Jasně řekni, když něco nevíš.
Můžeš používat nástroje, když jsou k dispozici.
Nikdy neproveď nebezpečnou akci bez potvrzení uživatele.
""")


MODE_PROMPTS = {
    "normal": "",
    "gaming": "\nJsi v herním režimu. Odpovídej kratše a zaměř se na herní rady.",
    "flight": "\nJsi v leteckém režimu. Máš znalosti o Microsoft Flight Simulator 2024.",
    "coding": "\nJsi v programovacím režimu. Poskytuj podrobné technické vysvětlení a kód.",
    "study": "\nJsi ve studijním režimu. Vysvětluj podrobně a učivoře.",
}


def get_mode_prompt(mode: str) -> str:
    """Get additional prompt for specific mode."""
    return MODE_PROMPTS.get(mode, "")


def get_full_system_prompt(mode: str | None = None) -> str:
    """Get complete system prompt including mode-specific additions."""
    config = get_config()
    active_mode = mode or config.get("modes", "active", default="normal")
    base = get_system_prompt()
    mode_addition = get_mode_prompt(active_mode)
    return base + mode_addition