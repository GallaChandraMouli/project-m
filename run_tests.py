import subprocess
import sys
import os

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def run_command(command, description):
    print(f"\n========================================================")
    print(f"RUNNING: {description}")
    print(f"COMMAND: {command}")
    print(f"========================================================\n")
    
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"\n[FAILED]: {description} (Exit code: {result.returncode})")
        return False
    print(f"\n[PASSED]: {description}")
    return True

def main():
    print("""
========================================================
     NEXUSCOMPUTE: FULL SUITE TEST RUNNER
========================================================
    """)

    python_exe = sys.executable

    steps = [
        (f'"{python_exe}" -m pytest -v backend/tests', "Backend Unit & Integration Tests (31 test cases)"),
        (f'"{python_exe}" -u backend/tests/e2e_standalone.py', "Live WebSocket & SSE Streaming End-to-End Test"),
        ('cd frontend && npm run build', "Frontend Production Build & Typecheck")
    ]

    all_passed = True
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            all_passed = False
            break

    print("\n========================================================")
    if all_passed:
        print("[SUCCESS] ALL TEST SUITES PASSED WITH 100% SUCCESS!")
    else:
        print("[ERROR] ONE OR MORE TESTS FAILED.")
    print("========================================================\n")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
