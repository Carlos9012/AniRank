import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def add_enum_values():
    
    commands = [
        "ALTER TYPE mediaformat ADD VALUE IF NOT EXISTS 'SPECIAL';",
        "ALTER TYPE mediaformat ADD VALUE IF NOT EXISTS 'ONA';",
        
        "ALTER TYPE mediasource ADD VALUE IF NOT EXISTS 'MANGA';",
        "ALTER TYPE mediasource ADD VALUE IF NOT EXISTS 'LIGHT_NOVEL';",
    ]
    
    print("=" * 50)
    print("🔧 Adicionando valores aos ENUMs...")
    print("=" * 50)
    
    with engine.connect() as conn:
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                conn.commit()
                print(f"✅ {cmd}")
            except Exception as e:
                print(f"❌ Erro em: {cmd}")
                print(f"   {e}")
    
    print("=" * 50)
    print("✅ Processo concluído!")
    print("📌 MediaFormat: SPECIAL, ONA")
    print("📌 MediaSource: MANGA, LIGHT_NOVEL")
    print("=" * 50)


if __name__ == "__main__":
    add_enum_values()
