from __future__ import annotations

import argparse
import json

from app.application.demo_seed_service import generate_demo_dataset
from app.infrastructure.db import get_session_local, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera base demonstracao completa para o SysPragas.")
    parser.add_argument(
        "--output-dir",
        default="output/demo_seed",
        help="Diretorio para arquivos exportados (manifesto, SQL e documentos).",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Mantem dados demonstracao existentes em vez de recriar a base.",
    )
    args = parser.parse_args()

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

    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
