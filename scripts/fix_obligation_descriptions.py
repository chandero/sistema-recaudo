"""
Script para corregir descripciones de obligaciones que tienen el prefijo no deseado "Importación de cartera - ".
Este script debe ejecutarse una vez para limpiar los registros afectados.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Agregar el directorio backend al path para poder importar las configuraciones
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.config import settings


def fix_obligation_descriptions():
    """
    Corrige las descripciones de obligaciones que tienen el prefijo "Importación de cartera - "
    extrayendo solo el número de obligación real.
    """
    # Crear conexión a la base de datos
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Buscar obligaciones con el prefijo no deseado en la descripción
        query = text("""
            SELECT id, description 
            FROM obligations 
            WHERE description LIKE 'Importación de cartera - %'
        """)
        
        results = db.execute(query).fetchall()
        
        if not results:
            print("No se encontraron obligaciones con el prefijo 'Importación de cartera - ' en la descripción.")
            return
        
        print(f"Se encontraron {len(results)} obligaciones con descripciones incorrectas.")
        
        # Procesar cada obligación y corregir la descripción
        fixed_count = 0
        for obligation in results:
            old_description = obligation.description
            # Extraer el número de obligación después del prefijo
            new_description = old_description.replace("Importación de cartera - ", "")
            
            # Actualizar la descripción en la base de datos
            update_query = text("""
                UPDATE obligations 
                SET description = :new_description 
                WHERE id = :obligation_id
            """)
            
            db.execute(update_query, {
                "new_description": new_description,
                "obligation_id": obligation.id
            })
            
            print(f"Corregida obligación ID {obligation.id}: '{old_description}' -> '{new_description}'")
            fixed_count += 1
        
        # Confirmar todos los cambios
        db.commit()
        print(f"\nSe corrigieron exitosamente {fixed_count} obligaciones.")
        
    except Exception as e:
        print(f"Error durante la corrección: {str(e)}")
        db.rollback()
    finally:
        db.close()


def preview_changes():
    """
    Muestra una vista previa de los cambios que se realizarían sin aplicarlos.
    """
    # Crear conexión a la base de datos
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Buscar obligaciones con el prefijo no deseado en la descripción
        query = text("""
            SELECT id, description 
            FROM obligations 
            WHERE description LIKE 'Importación de cartera - %'
            LIMIT 10  -- Limitar a 10 resultados para la vista previa
        """)
        
        results = db.execute(query).fetchall()
        
        if not results:
            print("No se encontraron obligaciones con el prefijo 'Importación de cartera - ' en la descripción.")
            return
        
        print(f"Vista previa de {len(results)} obligaciones que serían corregidas:")
        print("-" * 80)
        
        for obligation in results:
            old_description = obligation.description
            new_description = old_description.replace("Importación de cartera - ", "")
            print(f"ID {obligation.id}:")
            print(f"  Antes: '{old_description}'")
            print(f"  Después: '{new_description}'")
            print("-" * 80)
        
        print(f"\nTotal de obligaciones que serían corregidas: {len(results)}")
        
    except Exception as e:
        print(f"Error durante la vista previa: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        print("=== Vista previa de cambios ===")
        preview_changes()
    else:
        print("=== Script de corrección de descripciones de obligaciones ===")
        print("Este script corregirá las descripciones de obligaciones que tienen el prefijo 'Importación de cartera - '")
        print("\nAdvertencia: Este script modificará permanentemente datos en la base de datos.")
        
        response = input("\n¿Desea continuar? (s/n): ")
        if response.lower() in ['s', 'si', 'sí']:
            fix_obligation_descriptions()
        else:
            print("Operación cancelada.")