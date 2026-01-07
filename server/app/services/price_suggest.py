import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

# Simple in-memory cache for prices (in production, use Redis)
_price_cache: Dict[str, Dict[str, Any]] = {}
CACHE_DURATION_MINUTES = 60


async def fetch_amazon_price(product_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch price from Amazon using BeautifulSoup web scraping.
    Returns: {"source": "Amazon", "price": float, "url": str, "title": str}
    """
    try:
        import urllib.parse

        from bs4 import BeautifulSoup

        search_query = urllib.parse.quote(product_name)
        url = f"https://www.amazon.com/s?k={search_query}"

        # Using aiohttp for async requests with timeout
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status != 200:
                        return None

                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Find first product with price
                    for item in soup.find_all(
                        "div", {"data-component-type": "s-search-result"}
                    ):
                        try:
                            title_elem = item.find("h2", class_="s-line-clamp-2")
                            price_elem = item.find("span", class_="a-price-whole")

                            if title_elem and price_elem:
                                title = title_elem.get_text(strip=True)
                                price_text = (
                                    price_elem.get_text(strip=True)
                                    .replace("$", "")
                                    .replace(",", "")
                                )

                                # Parse price safely
                                try:
                                    if "." in price_text:
                                        price = float(price_text)
                                    else:
                                        price = float(price_text)
                                except ValueError:
                                    continue

                                return {
                                    "source": "Amazon",
                                    "price": price,
                                    "url": url,
                                    "title": title[:60],
                                }
                        except Exception as e:
                            logger.debug(f"Error parsing Amazon item: {e}")
                            continue

            return None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching Amazon price for {product_name}")
            return None
    except Exception as e:
        logger.error(f"Error fetching Amazon price: {e}")
        return None


async def fetch_walmart_price(product_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch price from Walmart using BeautifulSoup web scraping.
    Returns: {"source": "Walmart", "price": float, "url": str, "title": str}
    """
    try:
        import urllib.parse

        from bs4 import BeautifulSoup

        search_query = urllib.parse.quote(product_name)
        url = f"https://www.walmart.com/search?q={search_query}"

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status != 200:
                        return None

                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Find first product with price
                    for item in soup.find_all("div", class_="mb0 pb0-xl ph0-xl"):
                        try:
                            title_elem = item.find("span", class_="w_iUH7")
                            price_elem = item.find("div", class_="w_iUH7")

                            # Alternative selectors
                            if not title_elem:
                                title_elem = item.find("a", class_="Link")
                            if not price_elem:
                                price_elem = item.find(
                                    "span",
                                    {"class": lambda x: x and "price" in x.lower()},
                                )

                            if title_elem and price_elem:
                                title = title_elem.get_text(strip=True)
                                price_text = (
                                    price_elem.get_text(strip=True)
                                    .replace("$", "")
                                    .replace(",", "")
                                )

                                try:
                                    price = float(price_text)
                                    return {
                                        "source": "Walmart",
                                        "price": price,
                                        "url": url,
                                        "title": title[:60],
                                    }
                                except ValueError:
                                    continue
                        except Exception as e:
                            logger.debug(f"Error parsing Walmart item: {e}")
                            continue

            return None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching Walmart price for {product_name}")
            return None
    except Exception as e:
        logger.error(f"Error fetching Walmart price: {e}")
        return None


async def get_price_recommendations(product_name: str) -> List[Dict[str, Any]]:
    """
    Get price recommendations from multiple sources (Amazon, Walmart).
    Returns list of price suggestions with source information.
    With timeout protection - returns empty list on timeout instead of hanging.
    """

    # Check cache first
    cache_key = product_name.lower()
    if cache_key in _price_cache:
        cached_data = _price_cache[cache_key]
        if datetime.now() - cached_data["timestamp"] < timedelta(
            minutes=CACHE_DURATION_MINUTES
        ):
            logger.info(f"Returning cached price suggestions for {product_name}")
            return cached_data["prices"]

    recommendations = []

    # Fetch from both sources in parallel with timeout
    try:
        # Use asyncio.wait_for to enforce a timeout on the entire operation
        amazon_task = fetch_amazon_price(product_name)
        walmart_task = fetch_walmart_price(product_name)

        # Run both concurrently with 8 second total timeout
        results = await asyncio.wait_for(
            asyncio.gather(amazon_task, walmart_task, return_exceptions=True),
            timeout=8.0,
        )

        # Handle exceptions from gather
        amazon_price = results[0]
        walmart_price = results[1]

        if isinstance(amazon_price, dict) and amazon_price:
            recommendations.append(amazon_price)
        if isinstance(walmart_price, dict) and walmart_price:
            recommendations.append(walmart_price)

        # Sort by price (lowest first)
        recommendations.sort(key=lambda x: x["price"])

        # Cache the results
        _price_cache[cache_key] = {
            "prices": recommendations,
            "timestamp": datetime.now(),
        }

        logger.info(
            f"Found {len(recommendations)} price suggestions for {product_name}"
        )
        return recommendations

    except asyncio.TimeoutError:
        logger.warning(f"Timeout getting price recommendations for {product_name}")
        return []
    except Exception as e:
        logger.error(f"Error getting price recommendations: {e}")
        return []


def suggest_price(
    product_id: int, recent_prices: Optional[List[float]] = None
) -> float:
    """
    Suggest a price for a product based on recent prices (mean + random noise for demo).
    """
    if not recent_prices:
        # Fallback: use a default price range
        base_price = 100.0 + product_id % 10 * 5
    else:
        base_price = sum(recent_prices) / len(recent_prices)
    # Add small randomization for demo
    return round(base_price * (1 + random.uniform(-0.05, 0.05)), 2)
