import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from services.validation_service import ValidationService

def test_fingerprinting():
    print("--- Test 1: Random Entropy (Secret Key) ---")
    secrets = pd.Series(["a7c9f8d1e2b3c4d5e6f7a8b9c0d1e2f3", "9b8a7c6d5e4f3a2b1c0d9e8f7a6b5c4d"])
    entropy = ValidationService._calculate_sample_entropy(secrets)
    print(f"Entropy: {entropy:.2f} (Expected > 4.0)")

    print("\n--- Test 2: Case Pattern (Snake Case) ---")
    snake = pd.Series(["user_name", "created_at", "last_login"])
    pattern = ValidationService._detect_case_pattern(snake)
    print(f"Pattern: {pattern} (Expected: snake)")

    print("\n--- Test 3: Structural Detection (JSON) ---")
    json_data = pd.Series(['{"id": 1, "val": "A"}', '{"id": 2, "val": "B"}'])
    rate = ValidationService._detect_structural_pattern(json_data, "json")
    print(f"JSON Match Rate: {rate:.0%} (Expected: 100%)")

    print("\n--- Test 4: Structural Detection (Base64) ---")
    b64_data = pd.Series(["SGVsbG8gd29ybGQ=", "R29vZGJ5ZSB3b3JsZA=="])
    rate = ValidationService._detect_structural_pattern(b64_data, "base64")
    print(f"Base64 Match Rate: {rate:.0%} (Expected: 100%)")

if __name__ == "__main__":
    test_fingerprinting()
