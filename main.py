"""
Martin - Local AI Desktop Assistant
Main entry point with CLI chat interface.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ai.agent import MartinAgent
from app.ai.ollama import OllamaProvider
from app.core.logger import setup_logger
from app.memory.memory import MemoryManager


async def main() -> None:
    """Main entry point."""
    logger = setup_logger()

    logger.info("Starting Martin...")

    # Initialize components
    provider = OllamaProvider()
    agent = MartinAgent(provider)
    memory = MemoryManager()

    # Check provider availability
    if not await agent.initialize():
        print("Chyba: Ollama není dostupný nebo model 'gemma3:4b' není nainstalovaný.")
        print("Ujistěte se, že Ollama běží a model je stažen:")
        print("  ollama pull gemma3:4b")
        return

    print("\n=== Martin - Lokální AI Asistent ===")
    print("Napište 'konec' pro ukončení.")
    print("Napište 'paměť' pro zobrazení paměti.")
    print("Napište 'zapomeň' pro vymazání historie.\n")

    while True:
        try:
            user_input = input("Vy: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNa shledanou!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("konec", "exit", "quit"):
            print("Na shledanou!")
            break

        if user_input.lower() == "paměť":
            memories = memory.get_long_term(limit=10)
            if memories:
                print("\n--- Dlouhodobá paměť ---")
                for m in memories:
                    print(f"  [{m['category']}] {m['content']}")
            else:
                print("Paměť je prázdná.")
            continue

        if user_input.lower() == "zapomeň":
            memory.clear_short_term()
            print("Historie vymazána.")
            continue

        if user_input.lower().startswith("zapamatuj si "):
            content = user_input[13:].strip()
            if content:
                memory.add_long_term(content, category="user", importance=5)
                print(f"Zapamatoval jsem si: {content}")
            else:
                print("Co mám zapamatovat?")
            continue

        # Process through agent
        response = await agent.chat(user_input)
        print(f"Martin: {response}")


if __name__ == "__main__":
    asyncio.run(main())