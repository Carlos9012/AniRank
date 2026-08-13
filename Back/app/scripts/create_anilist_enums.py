import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.database import engine


def create_enums():

    enums = [
        """
        DO $$ BEGIN
            CREATE TYPE mediastatus AS ENUM (
                'FINISHED',
                'RELEASING',
                'NOT_YET_RELEASED',
                'CANCELLED',
                'HIATUS'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE mediaformat AS ENUM (
                'TV',
                'TV_SHORT',
                'MOVIE',
                'OVA'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE mediasource AS ENUM (
                'ORIGINAL',
                'ANIME'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
    ]

    print("=" * 50)
    print("🔧 Criando ENUMs...")
    print("=" * 50)

    with engine.connect() as conn:
        for enum_sql in enums:
            try:
                conn.execute(text(enum_sql))
                conn.commit()
                print("✅ ENUM criado com sucesso!")
            except Exception as e:
                print(f"❌ Erro: {e}")

    print("=" * 50)
    print("✅ ENUMs criados!")
    print("📌 MediaStatus: FINISHED, RELEASING, NOT_YET_RELEASED, CANCELLED, HIATUS")
    print("📌 MediaFormat: TV, TV_SHORT, MOVIE, OVA")
    print("📌 MediaSource: ORIGINAL, ANIME")
    print("=" * 50)


if __name__ == "__main__":
    create_enums()
