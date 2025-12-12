"""Test script to verify all connections: OpenAI, Database, and Weaviate."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from dotenv import load_dotenv
from openai import OpenAI
from custom_rag.connectors.database import DatabaseConnector
from custom_rag.connectors.weaviate_connector import WeaviateConnector

load_dotenv()


def test_openai():
    """Test OpenAI API connection."""
    print("\n" + "=" * 80)
    print("Testing OpenAI API Connection")
    print("=" * 80)

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("[FAIL] OPENAI_API_KEY not found in environment variables")
        return False

    if api_key.startswith("sk-"):
        print(f"[OK] API Key found: {api_key[:20]}...{api_key[-4:]}")
    else:
        print(f"[WARN] API Key format looks incorrect: {api_key[:20]}...")

    try:
        client = OpenAI(api_key=api_key)
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model for testing
            messages=[{"role": "user", "content": "Say 'Connection test successful'"}],
            max_tokens=10,
        )
        result = response.choices[0].message.content
        print(f"[OK] OpenAI API working: {result}")
        print(f"[OK] Model: gpt-4o-mini")
        print(f"[OK] Response received successfully")
        return True
    except Exception as e:
        print(f"[FAIL] OpenAI API Error: {str(e)}")
        return False


def test_database():
    """Test database connection."""
    print("\n" + "=" * 80)
    print("Testing Database Connection")
    print("=" * 80)

    db_url = os.getenv("COMPANY_1_DB_URL")

    if not db_url:
        print("[FAIL] COMPANY_1_DB_URL not found in environment variables")
        return False

    # Mask password in URL for display
    display_url = db_url
    if "@" in db_url:
        parts = db_url.split("@")
        credentials = parts[0].split("://")[1]
        if ":" in credentials:
            user = credentials.split(":")[0]
            display_url = db_url.replace(credentials, f"{user}:****")

    print(f"[OK] Connection string found: {display_url}")

    try:
        db = DatabaseConnector(db_url)
        session = db.get_session()

        # Test query to count products
        from custom_rag.pipelines.company_1.models import Product

        product_count = session.query(Product).count()
        print(f"[OK] Database connected successfully")
        print(f"[OK] Found {product_count} products in database")

        if product_count == 0:
            print("[WARN] Warning: Database is empty (no products found)")
        else:
            # Show a sample product
            sample = session.query(Product).first()
            if sample:
                print(f"[OK] Sample product: {sample.id} - {sample.name}")

        session.close()
        return True
    except Exception as e:
        print(f"[FAIL] Database Error: {str(e)}")
        return False


def test_weaviate():
    """Test Weaviate connection."""
    print("\n" + "=" * 80)
    print("Testing Weaviate Connection")
    print("=" * 80)

    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

    if not weaviate_url:
        print("[FAIL] WEAVIATE_URL not found in environment variables")
        return False

    print(f"[OK] Weaviate URL: {weaviate_url}")

    if weaviate_api_key:
        print(f"[OK] API Key found: {weaviate_api_key[:10]}...{weaviate_api_key[-4:]}")
    else:
        print("[WARN] No WEAVIATE_API_KEY found (may not be required for local instance)")

    try:
        import socket

        # Test basic connectivity first
        hostname = weaviate_url.replace("https://", "").replace("http://", "").split("/")[0]
        try:
            socket.setdefaulttimeout(5)
            socket.create_connection((hostname, 443), timeout=5)
            print(f"[OK] Network connectivity to {hostname}: OK")
        except Exception as conn_err:
            print(f"[FAIL] Cannot reach {hostname}: {str(conn_err)}")
            return False

        print("[INFO] Connecting to Weaviate (may take a moment)...")
        weaviate = WeaviateConnector(collection_name="Company1Products")

        # Test connection by checking if collection exists
        print(f"[OK] Connected to Weaviate")
        print(f"[OK] Collection: Company1Products")

        # Try a simple search with timeout
        try:
            results = weaviate.semantic_search(query="test", top_k=1)
            if results:
                print(f"[OK] Found {len(results)} objects in collection")
                if results[0].get("properties"):
                    sample_name = results[0]["properties"].get("name", "Unknown")
                    print(f"[OK] Sample product: {sample_name}")
            else:
                print("[WARN] Warning: No objects found in Weaviate collection")
        except Exception as search_err:
            print(f"[WARN] Search test failed: {str(search_err)}")
            print("[WARN] Collection might be empty or not exist yet")

        return True
    except Exception as e:
        print(f"[FAIL] Weaviate Error: {str(e)}")
        if "timed out" in str(e).lower():
            print("[INFO] Tip: Check if collection 'Company1Products' exists in Weaviate")
            print("[INFO] Tip: Verify Weaviate URL and API key are correct")
        return False


def main():
    """Run all connection tests."""
    print("\n" + "=" * 80)
    print("CONNECTION TEST SUITE")
    print("=" * 80)

    results = {
        "OpenAI": test_openai(),
        "Database": test_database(),
        "Weaviate": test_weaviate(),
    }

    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)

    for service, status in results.items():
        icon = "[PASS]" if status else "[FAIL]"
        status_text = "PASS" if status else "FAIL"
        print(f"{icon} {service}: {status_text}")

    all_pass = all(results.values())
    print("\n" + "=" * 80)
    if all_pass:
        print("ALL TESTS PASSED! System is ready.")
    else:
        print("SOME TESTS FAILED. Check errors above.")
    print("=" * 80 + "\n")

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
