import sqlite3
import os

DB_PATH = "backend/data/raw/chembl/chembl_36_sqlite/chembl_36/chembl_36_sqlite/chembl_36.db"

def check_columns():
    if not os.path.exists(DB_PATH):
        print(f"Error: DB not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(component_class)")
        columns = cursor.fetchall()
        print("Columns in component_class:")
        for col in columns:
            print(f" - {col[1]}")
            
        cursor.execute("PRAGMA table_info(protein_classification)")
        columns = cursor.fetchall()
        print("\nColumns in protein_classification:")
        for col in columns:
            print(f" - {col[1]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_columns()
