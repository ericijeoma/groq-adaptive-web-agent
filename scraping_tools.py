import nodriver
import asyncio
from nodriver.cdp import input_ as cdp_input
from typing import Literal

async def search_web(
    query: str,
    time_range: Literal["", "d", "w", "m", "y"] = "",
    site: str = "",
) -> str:
    """Search the web using DuckDuckGo and return top results with URLs and snippets.
    
    Args:
        query:      The search query.
        time_range: "d" day, "w" week, "m" month, "y" year, "" = no filter.
        site:       Restrict to a domain e.g. "reddit.com", "" = no restriction.
    """
    # Build query string — site filter goes into the query itself
    full_query = f"site:{site} {query}" if site else query

    # Build URL — time filter goes as a URL parameter
    url = f"https://duckduckgo.com/?q={full_query}&ia=web"
    if time_range in ("d", "w", "m", "y"):
        url += f"&df={time_range}"

    browser = await nodriver.start()
    try:
        page = await browser.get(url)
        await browser.wait(5)
        results = []
        items = await page.select_all("article[data-testid='result']")
        for el in items[:5]:
            title   = await el.query_selector("a[data-testid='result-title-a'] span")
            link    = await el.query_selector("a[data-testid='result-title-a']")
            snippet = await el.query_selector("div[data-result='snippet']")
            if title and link:
                href = await link.apply("(el) => el.getAttribute('href')") or ""
                results.append({
                    "title":   title.text.strip(),
                    "url":     href,
                    "snippet": snippet.text_all.strip() if snippet else ""
                })
        return str(results) if results else "No results found"
    except Exception as e:
        return f"Search error: {str(e)}"
    finally:
        browser.stop()


async def scrape_page(url: str) -> str:
    """Scrape the full text content of a webpage given its URL."""
    browser = await nodriver.start()
    try:
        tab = await browser.get(url)
        await tab.wait_for("body", timeout=10)
        await tab.evaluate("document.querySelectorAll('script,style,nav,footer').forEach(e=>e.remove())")
        body = await tab.select("body")
        return body.text_all[:5000] if body else ""
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
    finally:
        browser.stop()



async def crawl_website(url: str, max_pages: int = 10) -> str:
    """Crawl a website, following internal links up to max_pages."""
    browser = await nodriver.start()
    visited, results = set(), []
    try:
        async def visit(u):
            if u in visited or len(visited) >= max_pages:
                return
            visited.add(u)
            tab = await browser.get(u)
            await tab.wait_for("body", timeout=10)
            await tab.evaluate("document.querySelectorAll('script,style,nav,footer').forEach(e=>e.remove())")
            body = await tab.select("body")
            text = body.text_all[:2000] if body else ""
            results.append({"url": u, "content": text})
            links = await tab.select_all("a[href]")
            for link in links[:20]:
                href = await link.apply("(el) => el.getAttribute('href')") or ""
                if href.startswith("http") and url in href and href not in visited:
                    await visit(href)
        await visit(url)
        return str(results)
    except Exception as e:
        return f"Crawl error: {str(e)}"
    finally:
        browser.stop()

async def map_website(url: str) -> str:
    """Extract all internal links from a website's homepage."""
    browser = await nodriver.start()
    try:
        tab = await browser.get(url)
        await tab.wait_for("body", timeout=10)
        links = await tab.select_all("a[href]")
        hrefs = []
        for link in links:
            href = await link.apply("(el) => el.getAttribute('href')") or ""
            if href.startswith("http"):
                hrefs.append(href)
        return str(list(set(hrefs)))
    except Exception as e:
        return f"Map error: {str(e)}"
    finally:
        browser.stop()





async def scrape_amazon_product(search_term: str) -> str:
    """Search Amazon for a product the way a human would and return listings."""
    browser = await nodriver.start()
    try:
        # Step 1 — land on homepage
        page = await browser.get("https://www.amazon.com")
        await asyncio.sleep(3)  # Use asyncio.sleep for async compatibility

        # Step 2 — find and click the search box
        search_box = await page.select("#twotabsearchtextbox")
        await search_box.click()
        await asyncio.sleep(1)

        # Step 3 — type the search term slowly to simulate human typing
        for char in search_term:
            await search_box.send_keys(char)
            await asyncio.sleep(0.1)  # Randomize this (e.g., random.uniform(0.05, 0.2)) for better anti-detection

        await asyncio.sleep(2)  # Wait for autocomplete to settle

        # Step 4 — Simulate pressing Enter using CDP key events (more reliable than \n)
        # First, ensure focus (though send_keys should handle it)
        await search_box.focus()
        
        # Press Enter down
        submit = (await page.select_all("#nav-search-submit-button"))[0] if await page.select_all("#nav-search-submit-button") else None
        if submit:
            await submit.click()
        else:
            await page.send(cdp_input.dispatch_key_event("keyDown", code="Enter", key="Enter", text="\r", windows_virtual_key_code=13))
            await page.send(cdp_input.dispatch_key_event("keyUp",   code="Enter", key="Enter", text="\r", windows_virtual_key_code=13))

        # Step 5 — give the results page time to fully load
        await asyncio.sleep(6)

        # Step 6 — scroll down like a human reading the page
        await page.evaluate("window.scrollBy(0, 600)")
        await asyncio.sleep(2)

        # Step 7 — extract product data
        products = []
        items = await page.select_all("div[data-component-type='s-search-result']")
        for el in items[:5]:
            title = await el.query_selector("h2 span")
            price = await el.query_selector(".a-price .a-offscreen")
            rating = await el.query_selector(".a-icon-alt")
            if title:
                products.append({
                    "title": title.text.strip(),
                    "price": price.text.strip() if price else "N/A",
                    "rating": rating.text.strip() if rating else "N/A",
                })

        return str(products) if products else "No products found"

    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        browser.stop()

