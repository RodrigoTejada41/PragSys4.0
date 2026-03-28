from __future__ import annotations

import argparse

from sqlalchemy import inspect

from app.application.demo_seed_service import generate_demo_dataset
from app.infrastructure.db import get_engine, get_session_local, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerencia bootstrap e migracoes do banco SysPragas.")
    parser.add_argument("command", choices=["init", "status", "seed-demo"], help="Acao desejada.")
    parser.add_argument(
        "--output-dir",
        default="output/demo_seed",
        help="Diretorio para exportar arquivos da seed demonstracao.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Mantem a base demonstracao anterior ao inves de recria-la.",
    )
    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print("Banco inicializado e migracoes aplicadas com sucesso.")
        return

    if args.command == "seed-demo":
        init_db()
        session = get_session_local()()
        try:
            result = generate_demo_dataset(
                session,
                output_dir=args.output_dir,
                replace_existing=not args.keep_existing,
            )
        finally:
            session.close()
        print("Base demonstracao criada com sucesso.")
        print(f"- diretorio: {result.output_dir}")
        print(f"- empresa principal: {result.company_id}")
        print(f"- filial: {result.branch_company_id}")
        print(f"- usuario admin demo: {result.admin_username}")
        return

    engine = get_engine()
    inspector = inspect(engine)
    print("Tabelas encontradas:")
    for table_name in inspector.get_table_names():
        print(f"- {table_name}")


if __name__ == "__main__":
    main()
