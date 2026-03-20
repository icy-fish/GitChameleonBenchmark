#!/usr/bin/env python3
"""
Filter dataset and clean up test files based on library and example_id.
This script:
1. Filters dataset.jsonl to keep only 'django' or 'matplotlib' libraries
2. Updates ground_truth_solutions.jsonl with matching example_ids
3. Deletes unrelated test files from hidden_tests and visible_tests folders
"""

import json
import os
from pathlib import Path

def main():
    dataset_path = Path("dataset/dataset.jsonl")
    solutions_path = Path("dataset/ground_truth_solutions.jsonl")
    hidden_tests_dir = Path("dataset/hidden_tests")
    visible_tests_dir = Path("dataset/visible_tests")
    
    print("Step 1: Filtering dataset.jsonl for 'django' and 'matplotlib' libraries...")
    
    # Step 1: Filter dataset.jsonl
    target_libraries = {"django", "matplotlib", "flask"}
    filtered_examples = []
    kept_example_ids = set()
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            if obj.get("library") in target_libraries:
                filtered_examples.append(obj)
                kept_example_ids.add(obj.get("example_id"))
    
    # Write filtered dataset back
    with open(dataset_path, 'w', encoding='utf-8') as f:
        for obj in filtered_examples:
            f.write(json.dumps(obj) + '\n')
    
    print(f"  ✓ Kept {len(filtered_examples)} objects from dataset.jsonl")
    print(f"  ✓ Example IDs to keep: {sorted([int(x) for x in kept_example_ids])[:20]}{'...' if len(kept_example_ids) > 20 else ''}")
    
    # Step 2: Filter ground_truth_solutions.jsonl
    print("\nStep 2: Filtering ground_truth_solutions.jsonl to match example_ids...")
    
    filtered_solutions = []
    with open(solutions_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            if obj.get("example_id") in kept_example_ids:
                filtered_solutions.append(obj)
    
    with open(solutions_path, 'w', encoding='utf-8') as f:
        for obj in filtered_solutions:
            f.write(json.dumps(obj) + '\n')
    
    print(f"  ✓ Kept {len(filtered_solutions)} objects from ground_truth_solutions.jsonl")
    
    # Step 3: Delete unrelated test files
    print("\nStep 3: Deleting unrelated test files...")
    
    expected_test_files = {f"test_sample_{eid}.py" for eid in kept_example_ids}
    
    def clean_test_directory(test_dir, dir_name):
        deleted_count = 0
        if test_dir.exists():
            for file in test_dir.iterdir():
                if file.is_file() and file.name.endswith('.py'):
                    if file.name not in expected_test_files:
                        file.unlink()
                        deleted_count += 1
        return deleted_count
    
    hidden_deleted = clean_test_directory(hidden_tests_dir, "hidden_tests")
    visible_deleted = clean_test_directory(visible_tests_dir, "visible_tests")
    
    print(f"  ✓ Deleted {hidden_deleted} files from hidden_tests/")
    print(f"  ✓ Deleted {visible_deleted} files from visible_tests/")
    
    print("\n✅ Done! Dataset filtered successfully.")
    print(f"   Total example_ids retained: {len(kept_example_ids)}")

if __name__ == "__main__":
    main()
