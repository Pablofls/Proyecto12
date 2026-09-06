"""Aplica las migraciones de db/migrations en orden y registra cuales ya corrieron.

Uso (dentro de la VM):
    docker compose exec app python scripts/migrate.py
    docker compose exec app python scripts/migrate.py --estado
"""
import os
import sys
import hashlib
from pathlib import Path

import psycopg2

RAIZ = Path(__file__).resolve().parent.parent
MIGRACIONES = RAIZ / "db" / "migrations"

CONTROL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(100) PRIMARY KEY,
    checksum    VARCHAR(64)  NOT NULL,
    aplicada_en TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def conectar():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def pendientes(cur):
    cur.execute("SELECT version, checksum FROM schema_migrations")
    aplicadas = dict(cur.fetchall())
    archivos = sorted(MIGRACIONES.glob("*.sql"))
    resultado = []
    for archivo in archivos:
        contenido = archivo.read_text(encoding="utf-8")
        checksum = hashlib.sha256(contenido.encode("utf-8")).hexdigest()
        if archivo.name in aplicadas:
            if aplicadas[archivo.name] != checksum:
                print(
                    f"  AVISO: {archivo.name} ya fue aplicada pero su contenido cambio.\n"
                    f"         Nunca edites una migracion aplicada: crea una nueva."
                )
            continue
        resultado.append((archivo, contenido, checksum))
    return resultado


def main():
    solo_estado = "--estado" in sys.argv
    with conectar() as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(CONTROL)
            conn.commit()

            faltantes = pendientes(cur)
            if solo_estado:
                cur.execute("SELECT version, aplicada_en FROM schema_migrations ORDER BY version")
                print("Aplicadas:")
                for version, fecha in cur.fetchall():
                    print(f"  {version}  ({fecha:%Y-%m-%d %H:%M})")
                print("Pendientes:")
                for archivo, _, _ in faltantes:
                    print(f"  {archivo.name}")
                return

            if not faltantes:
                print("Sin migraciones pendientes.")
                return

            for archivo, contenido, checksum in faltantes:
                print(f"Aplicando {archivo.name} ...", end=" ")
                try:
                    cur.execute(contenido)
                    cur.execute(
                        "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                        (archivo.name, checksum),
                    )
                    conn.commit()
                    print("ok")
                except Exception as exc:
                    conn.rollback()
                    print("FALLO")
                    print(f"  {exc}")
                    sys.exit(1)
    print("Migraciones al dia.")


if __name__ == "__main__":
    main()
