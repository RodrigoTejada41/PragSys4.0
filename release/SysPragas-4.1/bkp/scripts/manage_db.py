from __future__ import annotations

import argparse

from sqlalchemy import inspect

from app.infrastructure.db import get_engine, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerencia bootstrap e migracoes do banco SysPragas.")
    parser.add_argument("command", choices=["init", "status"], help="Acao desejada.")
    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print("Banco inicializado e migracoes aplicadas com sucesso.")
        return

    engine = get_engine()
    inspector = inspect(engine)
    print("Tabelas encontradas:")
    for table_name in inspector.get_table_names():
        print(f"- {table_name}")


if __name__ == "__main__":
    main()
