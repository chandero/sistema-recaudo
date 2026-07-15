#!/usr/bin/env python3
"""
Ejemplo de uso del archivo de cartera de impuesto de alumbrado público de Girón

Este script demuestra cómo usar el archivo cartera_giron_2026_final.csv
con el sistema de importación de cartera.
"""

import pandas as pd
import sys
import os

def analyze_giron_portfolio_file():
    """
    Analiza el archivo de cartera de Girón para verificar su estructura
    """
    file_path = "examples/cartera_giron_2026_final.csv"
    
    if not os.path.exists(file_path):
        print(f"Error: No se encuentra el archivo {file_path}")
        return None
    
    try:
        # Leer el archivo CSV
        df = pd.read_csv(file_path)
        
        print("=== Análisis del archivo de cartera de Girón ===")
        print(f"Número de registros: {len(df)}")
        print(f"Número de columnas: {len(df.columns)}")
        print("\nNombres de columnas:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")
        
        print("\nPrimeros 5 registros:")
        print(df.head())
        
        print("\nInformación estadística:")
        print(df.describe(include='all'))
        
        # Verificar datos específicos
        print(f"\nDatos únicos en columna 'municipio': {df['municipio'].unique()}")
        print(f"Rango de valores en 'valor_alpu': {df['valor_alpu'].min()} - {df['valor_alpu'].max()}")
        
        return df
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None

def create_sample_mapping():
    """
    Crea un ejemplo de mapeo para el archivo de cartera de Girón
    """
    mapping_example = {
        'IDENTIFICACION': 'documento_identidad',  # Mapea al campo de identificación
        'NOMBRE': 'nombre',                       # Mapea al nombre del contribuyente
        'DIRECCION': 'direccion',                 # Mapea a la dirección
        'CIUDAD': 'municipio',                    # Mapea a la ciudad
        'NUMERO_OBLIGACION': 'cuenta',           # Mapea al número de obligación
        'VALOR_TOTAL': 'valor_alpu',              # Mapea al valor total de la obligación
    }
    
    print("\n=== Mapeo recomendado para cartera de Girón ===")
    for system_field, file_column in mapping_example.items():
        print(f"  {system_field} ← {file_column}")
    
    return mapping_example

def validate_data_format(df):
    """
    Valida el formato de los datos en el archivo de Girón
    """
    print("\n=== Validación de formato de datos ===")
    
    # Verificar valores nulos
    null_counts = df.isnull().sum()
    print("Conteo de valores nulos por columna:")
    for col, count in null_counts.items():
        if count > 0:
            print(f"  {col}: {count}")
    
    # Verificar formato de valores monetarios
    if 'valor_alpu' in df.columns:
        print(f"\nFormato de valores en 'valor_alpu':")
        sample_values = df['valor_alpu'].head(10)
        for i, value in enumerate(sample_values):
            print(f"  Fila {i+1}: '{value}' (tipo: {type(value).__name__})")

def main():
    print("Ejemplo de uso del archivo de cartera de impuesto de alumbrado público de Girón")
    print("="*80)
    
    # Analizar el archivo
    df = analyze_giron_portfolio_file()
    
    if df is not None:
        # Crear ejemplo de mapeo
        mapping = create_sample_mapping()
        
        # Validar formato de datos
        validate_data_format(df)
        
        print("\n=== Instrucciones para importar ===")
        print("1. Accede al sistema de recaudo")
        print("2. Navega a la sección de importación")
        print("3. Carga el archivo 'cartera_giron_2026_final.csv'")
        print("4. Usa el siguiente mapeo:")
        for system_field, file_column in mapping.items():
            print(f"   - {system_field}: {file_column}")
        print("5. Considera establecer 'departamento' como 'Santander' y 'vigencia' como '2026'")
        print("6. Valida el archivo antes de procesar")
        print("7. Confirma e inicia la importación")
        
        print(f"\nEl archivo contiene {len(df)} registros de contribuyentes con deudas de alumbrado público.")
        print("Los datos abarcan información de clientes con deuda de alumbrado público en Girón,")
        print("con antigüedad mínima de 3 meses y saldo mayor a 0.")

if __name__ == "__main__":
    main()