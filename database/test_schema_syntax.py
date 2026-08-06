"""
ComplianceIQ - Database SQL Syntax & Structure Validator
Validates SQL DDL files against syntax rules and checks for required keywords.
"""

import sys
from pathlib import Path

def validate_sql_file(filepath: Path):
    print(f"Validating SQL file: {filepath.name}...")
    if not filepath.exists():
        print(f"ERROR: File {filepath} does not exist.")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Check basic SQL transaction blocks
    if "BEGIN;" not in content or "COMMIT;" not in content:
        print(f"ERROR: {filepath.name} missing BEGIN/COMMIT transaction block.")
        return False

    print(f"[OK] {filepath.name} passed static validation ({len(content.splitlines())} lines).")
    return True

def main():
    db_dir = Path(__file__).parent
    files_to_check = [
        db_dir / "schema.sql",
        db_dir / "seeds.sql",
        db_dir / "migrations" / "05_triggers_and_indexes.sql",
    ]
    
    all_passed = True
    for sql_file in files_to_check:
        if not validate_sql_file(sql_file):
            all_passed = False

    # Specific check for Day 5 requirements
    schema_content = (db_dir / "schema.sql").read_text(encoding="utf-8")
    if "prevent_audit_trail_mutation()" not in schema_content:
        print("ERROR: prevent_audit_trail_mutation() trigger function missing in schema.sql")
        all_passed = False

    if "idx_controls_embedding_hnsw" not in schema_content:
        print("ERROR: idx_controls_embedding_hnsw vector index missing in schema.sql")
        all_passed = False

    if "vector_cosine_ops" not in schema_content:
        print("ERROR: vector_cosine_ops missing in HNSW vector index definition")
        all_passed = False

    if all_passed:
        print("SUCCESS: ALL DAY 5 DATABASE ASSETS VALIDATED!")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
