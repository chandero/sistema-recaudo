
from app.core.database import engine, init_db
from sqlmodel import text

print('Inicializando base de datos...')
init_db()
print('Base de datos inicializada.')

# Verificar si la columna file_path existe
with engine.connect() as conn:
    result = conn.execute(text("PRAGMA table_info(document_templates);"))
    columns = [row[1] for row in result.fetchall()]
    print(f'Columnas en document_templates: {columns}')
    
    if 'file_path' in columns:
        print('✓ La columna file_path existe')
    else:
        print('✗ La columna file_path NO existe')

