"""
CLI entry point for the Autonomous Software Engineering Agent.

Usage:
    export MISTRAL_API_KEY=sk-...
    python main.py "Write a function that checks if a number is prime"
    python main.py --max-iterations 3 "Build a simple LRU cache class"
"""

import argparse
import sys

from graph import build_graph
from tools.file_tool import write_file


def main():
    parser = argparse.ArgumentParser(description="Autonomous Software Engineering Agent")
    parser.add_argument("requirement", nargs="?", help="The feature/requirement to implement")
    parser.add_argument(
        "--max-iterations", type=int, default=2,
        help="Max Coder<->Tester retry loops on test failure (default: 2)",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Don't write generated code/tests to ./workspace",
    )
    args = parser.parse_args()

    requirement = args.requirement or input("Describe what you want built: ").strip()
    if not requirement:
        print("No requirement provided. Exiting.")
        sys.exit(1)

    app = build_graph()

    print(f"\nRunning agent pipeline for: {requirement!r}\n" + "-" * 60)
    result = app.invoke({
        "requirement": requirement,
        "max_iterations": args.max_iterations,
    })

    print(result["final_output"])

    if not args.no_save:
        filename = result.get("filename", "solution.py")
        code_path = write_file(filename, result.get("code", ""))
        test_path = write_file(f"test_{filename}", result.get("tests", ""))
        report_path = write_file("REPORT.md", result.get("final_output", ""))
        print("-" * 60)
        print(f"Saved code:   {code_path}")
        print(f"Saved tests:  {test_path}")
        print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
