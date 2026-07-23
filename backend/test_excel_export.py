"""
Test script to verify the Excel export functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import create_engine
from app.core.database import get_session
from app.services.excel_export_service import ExcelExportService

def test_excel_export():
    """Test the Excel export functionality"""
    print("Testing Excel export functionality...")
    
    # Get database session
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Test with a sample range (these numbers should exist in the database)
        # For testing purposes, we'll use a range that likely exists in the DB
        excel_file = ExcelExportService.export_obligations_by_resolution_range(
            db=session,
            resolution_from=1000,
            resolution_to=9999
        )
        
        # Save the file temporarily to verify it works
        with open("test_obligations_export.xlsx", "wb") as f:
            f.write(excel_file.getvalue())
        
        print("SUCCESS: Excel file generated successfully!")
        print("File saved as 'test_obligations_export.xlsx'")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_excel_export()