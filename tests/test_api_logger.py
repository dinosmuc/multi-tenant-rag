"""
API Logger Test - Logs every RAW OpenAI API call and response during agent execution.

Creates a clear, readable log file (result.log) showing:
- RAW request sent to OpenAI
- RAW response received from OpenAI
- Clear separators between each call

Usage:
    python tests/test_api_logger.py
    python tests/test_api_logger.py --test-id test_case_1
    python tests/test_api_logger.py --query "Your custom query here"
"""

import json
import logging
import os
import sys
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

import django
from django.test import Client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


class RawAPILogger:
    """
    Logs RAW OpenAI API calls and responses to a plain text file.
    """

    def __init__(self, log_file: str):
        self.log_file = log_file
        self.call_counter = 0
        self.original_create = None
        self.file_handle = None

    def start(self):
        """Start logging by patching OpenAI responses.create method."""
        from openai.resources.responses import Responses

        # Open log file
        self.file_handle = open(self.log_file, "w", encoding="utf-8")
        self.call_counter = 0

        # Write header
        self._write_header()

        # Store original method
        self.original_create = Responses.create

        # Create wrapper
        raw_logger = self

        @wraps(Responses.create)
        def logged_create(self_responses, **kwargs):
            raw_logger.call_counter += 1
            call_number = raw_logger.call_counter
            timestamp = datetime.now()

            # Log the RAW REQUEST
            raw_logger._log_request(call_number, timestamp, kwargs)

            # Make the actual API call
            try:
                response = raw_logger.original_create(self_responses, **kwargs)

                # Log the RAW RESPONSE
                raw_logger._log_response(call_number, timestamp, response)

                return response

            except Exception as e:
                raw_logger._log_error(call_number, e)
                raise

        # Apply patch
        Responses.create = logged_create
        logger.info("Logging started -> %s", self.log_file)

    def stop(self):
        """Stop logging and restore original method."""
        from openai.resources.responses import Responses

        if self.original_create:
            Responses.create = self.original_create

        # Write footer and close file
        if self.file_handle:
            self._write_footer()
            self.file_handle.close()
            self.file_handle = None

        logger.info("Logging stopped. Total API calls: %s", self.call_counter)

    def _write(self, text: str):
        """Write to log file and flush."""
        if self.file_handle:
            self.file_handle.write(text + "\n")
            self.file_handle.flush()

    def _write_header(self):
        """Write log file header."""
        self._write("=" * 100)
        self._write("OPENAI API CALL LOG")
        self._write(f"Started: {datetime.now().isoformat()}")
        self._write("=" * 100)
        self._write("")

    def _write_footer(self):
        """Write log file footer."""
        self._write("")
        self._write("=" * 100)
        self._write(f"LOGGING COMPLETE - Total API Calls: {self.call_counter}")
        self._write(f"Ended: {datetime.now().isoformat()}")
        self._write("=" * 100)

    def _log_request(self, call_number: int, timestamp: datetime, kwargs: dict):
        """Log the RAW request."""
        self._write("")
        self._write("#" * 100)
        self._write(f"#  API CALL #{call_number}")
        self._write(f"#  Timestamp: {timestamp.isoformat()}")
        self._write("#" * 100)
        self._write("")
        self._write(">>> RAW REQUEST >>>")
        self._write("-" * 50)

        # Log each parameter separately for clarity
        self._write(f"MODEL: {kwargs.get('model', 'N/A')}")
        self._write("")

        # Instructions (system prompt) - truncate if very long
        instructions = kwargs.get("instructions", "")
        self._write("INSTRUCTIONS (System Prompt):")
        self._write("-" * 30)
        if len(instructions) > 2000:
            self._write(instructions[:2000])
            self._write(f"... [TRUNCATED - {len(instructions)} total chars]")
        else:
            self._write(instructions)
        self._write("")

        # Input
        input_data = kwargs.get("input", "")
        self._write("INPUT:")
        self._write("-" * 30)
        self._write(self._format_json(input_data))
        self._write("")

        # Tools
        tools = kwargs.get("tools", [])
        self._write(f"TOOLS ({len(tools)} available):")
        self._write("-" * 30)
        for tool in tools:
            self._write(f"  - {tool.get('name', 'unknown')}")
        self._write("")

        # Other parameters
        other_params = {
            k: v
            for k, v in kwargs.items()
            if k not in ["model", "instructions", "input", "tools"]
        }
        if other_params:
            self._write("OTHER PARAMETERS:")
            self._write("-" * 30)
            self._write(self._format_json(other_params))
            self._write("")

    def _log_response(self, call_number: int, start_time: datetime, response):
        """Log the RAW response."""
        duration = (datetime.now() - start_time).total_seconds() * 1000

        self._write("")
        self._write("<<< RAW RESPONSE <<<")
        self._write("-" * 50)
        self._write(f"Duration: {duration:.2f} ms")
        self._write("")

        # Response ID
        if hasattr(response, "id"):
            self._write(f"RESPONSE ID: {response.id}")

        # Model
        if hasattr(response, "model"):
            self._write(f"MODEL: {response.model}")

        # Usage/Tokens
        if hasattr(response, "usage") and response.usage:
            self._write("")
            self._write("TOKEN USAGE:")
            self._write(
                f"  Input tokens:  {getattr(response.usage, 'input_tokens', 0)}"
            )
            self._write(
                f"  Output tokens: {getattr(response.usage, 'output_tokens', 0)}"
            )
            self._write(
                f"  Total tokens:  {getattr(response.usage, 'total_tokens', 0)}"
            )

        # Output
        self._write("")
        self._write("OUTPUT:")
        self._write("-" * 30)

        if hasattr(response, "output"):
            for i, item in enumerate(response.output):
                self._write(f"\n[Output Item {i + 1}] Type: {item.type}")

                if item.type == "function_call":
                    self._write(f"  Function: {item.name}")
                    self._write(f"  Call ID:  {item.call_id}")
                    self._write("  Arguments:")
                    try:
                        args = json.loads(item.arguments)
                        self._write(self._format_json(args, indent=4))
                    except Exception:
                        self._write(f"    {item.arguments}")

                elif item.type == "message":
                    for content in item.content:
                        if content.type == "output_text":
                            self._write(f"  Text: {content.text}")

        self._write("")
        self._write("=" * 100)

    def _log_error(self, call_number: int, error: Exception):
        """Log an error."""
        self._write("")
        self._write("!!! ERROR !!!")
        self._write("-" * 50)
        self._write(f"Call #{call_number} failed: {str(error)}")
        self._write("=" * 100)

    def _format_json(self, obj: Any, indent: int = 2) -> str:
        """Format object as pretty JSON string."""
        try:
            if isinstance(obj, str):
                return obj
            return json.dumps(obj, indent=indent, ensure_ascii=False, default=str)
        except Exception:
            return str(obj)


def run_test(
    query: str = None,
    test_id: str = None,
    testcases_file: str = None,
    output_file: str = None,
):
    """
    Run a single test and log all API calls.
    """
    # Determine query and test case
    test_case_data = None

    if query:
        test_query = query
        test_description = "Custom query"
    else:
        testcases_path = testcases_file or str(Path(__file__).parent / "testcases.json")
        with open(testcases_path) as f:
            test_cases = json.load(f)

        if test_id:
            test_case_data = next(
                (tc for tc in test_cases if tc["id"] == test_id), None
            )
            if not test_case_data:
                raise ValueError(f"Test case '{test_id}' not found")
        else:
            test_case_data = test_cases[0]

        test_query = test_case_data["query"]
        test_description = test_case_data["description"]
        test_id = test_case_data["id"]

    logger.info("\n%s", "=" * 80)
    logger.info("STARTING TEST")
    logger.info("%s", "=" * 80)
    logger.info("Test ID: %s", test_id or "custom")
    logger.info("Description: %s", test_description)
    logger.info("Query: %s...", test_query[:100])
    logger.info("%s\n", "=" * 80)

    # Setup log file
    log_path = output_file or str(Path(__file__).parent / "result.log")

    # Initialize logger
    api_logger = RawAPILogger(log_path)
    api_logger.start()

    # Prepare request
    if test_case_data and "request_data" in test_case_data:
        request_data = test_case_data["request_data"].copy()
    else:
        request_data = {
            "function_id": "company_1",
            "llm_provider": "openai",
            "llm": "gpt-4o",
            "prompt_objects": {"query": test_query},
            "scope_variables": {},
            "previous_prompt_outputs": {},
        }

    start_time = datetime.now()

    try:
        client = Client()
        response = client.post(
            "/custom_rag/execute/",
            data=json.dumps(request_data),
            content_type="application/json",
        )
        response_data = response.json()
        success = response.status_code == 200 and response_data.get("success")

    except Exception as e:
        logger.exception("Request failed: %s", e)
        response_data = {"error": str(e)}
        success = False

    finally:
        api_logger.stop()

    duration = (datetime.now() - start_time).total_seconds()

    logger.info("\n%s", "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("%s", "=" * 80)
    logger.info("Success: %s", success)
    logger.info("Duration: %.2fs", duration)
    logger.info("API calls made: %s", api_logger.call_counter)
    logger.info("Log file: %s", log_path)
    logger.info("%s\n", "=" * 80)

    return {
        "success": success,
        "api_calls": api_logger.call_counter,
        "duration": duration,
        "log_file": log_path,
        "response": response_data,
    }


def main():
    import argparse
    import io

    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )

    parser = argparse.ArgumentParser(
        description="Log all OpenAI API calls during agent execution"
    )
    parser.add_argument("--test-id", help="Test case ID from testcases.json")
    parser.add_argument("--query", help="Custom query (overrides --test-id)")
    parser.add_argument("--testcases", help="Path to testcases.json")
    parser.add_argument("--output", help="Output log file path (default: result.log)")
    args = parser.parse_args()

    try:
        run_test(
            query=args.query,
            test_id=args.test_id,
            testcases_file=args.testcases,
            output_file=args.output,
        )
    except Exception as e:
        logger.exception("Error: %s", e)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
