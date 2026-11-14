#!/usr/bin/env python3
"""Ponto de entrada para o assistente de configuração (Setup Wizard) do Telegram Money."""
from pathlib import Path
import sys

# Garante acesso aos módulos auxiliares em scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from setup_wizard import main

if __name__ == "__main__":
    main()
