"""
test_amazon_scrape.py
---------------------
Run with:
    python test_amazon_scrape.py
    python test_amazon_scrape.py "standing desk"   ← custom search term
    
"""

import sys
import nodriver
import ast  
from scraping_tools import scrape_amazon_product


def _print_products(result: str) -> None:
    """Parse and pretty-print the result string."""
    if result.startswith("Error") or result == "No products found":
        print(f"\n  ⚠  {result}")
        return

    # result is a stringified list — eval it back safely
    try:
        products = ast.literal_eval(result)
    except Exception:
        print(f"\n  Raw output:\n{result}")
        return

    print(f"\n  Found {len(products)} product(s):\n")
    for i, p in enumerate(products, 1):
        print(f"  {i}. {p['title']}")
        print(f"     Price  : {p['price']}")
        print(f"     Rating : {p['rating']}")
        print()


async def main() -> None:
    search_term = sys.argv[1] if len(sys.argv) > 1 else "mechanical keyboard"

    print(f"\n{'─' * 60}")
    print(f"  Testing scrape_amazon_product('{search_term}')")
    print(f"{'─' * 60}")

    result = await scrape_amazon_product(search_term)
    _print_products(result)
    


if __name__ == "__main__":
    nodriver.loop().run_until_complete(main())