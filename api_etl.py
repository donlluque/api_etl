#!/usr/bin/env python3
"""
API ETL Tool
Extracts paginated REST API data to CSV/XLSX with field filtering and rate limiting.
"""
import argparse
import logging
import os
from pathlib import Path
import time
import json
import requests
import pandas as pd
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def fetch_paginated(
    url: str,
    headers: dict,
    params: dict,
    page_param: str = "page",
    start: int = 1,
    max_pages: int = 1,
    sleep_s: float = 0.5
) -> list[dict]:
    """
    Fetches data from paginated API endpoint.
    
    Args:
        url: Base API endpoint URL
        headers: HTTP headers (including authentication)
        params: Base query parameters
        page_param: Name of pagination parameter (default: 'page')
        start: Starting page number (default: 1)
        max_pages: Maximum pages to fetch
        sleep_s: Seconds to wait between requests for rate limiting
        
    Returns:
        List of all items collected across pages
        
    Raises:
        requests.HTTPError: On 4xx/5xx responses (except 429 which retries)
        requests.RequestException: On connection/timeout errors
    """
    all_items = []
    page = start
    
    for i in range(max_pages):
        qp = dict(params or {})
        qp[page_param] = page
        
        try:
            logger.info(f"Fetching page {page}/{start + max_pages - 1}...")
            r = requests.get(url, headers=headers, params=qp, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            # Debug: log response structure
            logger.debug(f"Response type: {type(data).__name__}")

            # Support both {"items": [...]} and direct array responses
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("items", [])
                if not items and data:
                    logger.warning(f"Dict response without 'items' key. Available keys: {list(data.keys())}")
            else:
                logger.error(f"Unexpected response type: {type(data)}")
                items = []
            
            if not items:
                logger.warning(f"Page {page} returned empty, stopping pagination")
                break
                
            logger.info(f"✓ Page {page}: {len(items)} items retrieved")
            all_items.extend(items)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit hit
                logger.warning("Rate limited (429), waiting 5s before retry...")
                time.sleep(5)
                continue  # Retry same page
            logger.error(f"HTTP error on page {page}: {e}")
            raise
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed on page {page}: {e}")
            raise
            
        page += 1
        
        # Sleep between pages (but not after the last one)
        if i < max_pages - 1:
            time.sleep(sleep_s)
    
    return all_items


def select_fields(rows: list[dict], fields: list[str] | None) -> list[dict]:
    """
    Filters specific fields from each item.
    
    Args:
        rows: List of dictionaries (API response items)
        fields: Field names to keep (None = keep all)
        
    Returns:
        List of filtered dictionaries
    """
    if not fields:
        return rows
    
    filtered = []
    for item in rows:
        filtered.append({f: item.get(f, None) for f in fields})
    return filtered


def main() -> int:
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Extract data from paginated REST APIs to CSV/XLSX",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic extraction from public API (no auth)
  python api_etl.py \\
    --url "https://jsonplaceholder.typicode.com/posts" \\
    --output posts.csv \\
    --max-pages 2

  # With field filtering and authentication
  python api_etl.py \\
    --url "https://api.example.com/users" \\
    --output users.xlsx \\
    --fields "id,name,email,created_at" \\
    --max-pages 5 \\
    --token-env MY_API_TOKEN

  # Custom pagination parameter
  python api_etl.py \\
    --url "https://api.github.com/repos/python/cpython/issues" \\
    --output issues.csv \\
    --page-param "per_page" \\
    --params '{"state":"open"}' \\
    --max-pages 3
        """
    )
    parser.add_argument(
        "--url",
        required=True,
        help="API endpoint URL"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output file (.csv or .xlsx)"
    )
    parser.add_argument(
        "--fields",
        help="Comma-separated fields to extract (e.g., 'id,name,email')"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Maximum pages to fetch (default: 1)"
    )
    parser.add_argument(
        "--page-param",
        default="page",
        help="Pagination parameter name (default: 'page')"
    )
    parser.add_argument(
        "--params",
        help='Additional query params as JSON (e.g., \'{"status":"active"}\')'
    )
    parser.add_argument(
        "--auth-header",
        default="Authorization",
        help="Authorization header name (default: 'Authorization')"
    )
    parser.add_argument(
        "--token-env",
        default="API_TOKEN",
        help="Environment variable name for auth token (default: 'API_TOKEN')"
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Seconds to wait between requests (default: 0.5)"
    )
    
    args = parser.parse_args()

    try:
        # Load environment variables from .env file if present
        load_dotenv()
        token = os.getenv(args.token_env, "")
        
        headers = {}
        if token:
            headers[args.auth_header] = f"Bearer {token}"
            logger.info(f"✓ Auth token loaded from ${args.token_env}")
        else:
            logger.info("No auth token found, proceeding without authentication")

        # Parse additional query parameters
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
                logger.info(f"Additional params: {params}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in --params: {e}")
                return 2

        # Fetch data from API
        logger.info(f"Starting extraction from: {args.url}")
        items = fetch_paginated(
            args.url,
            headers=headers,
            params=params,
            page_param=args.page_param,
            max_pages=args.max_pages,
            sleep_s=args.sleep
        )
        
        if not items:
            logger.warning("No data retrieved, aborting")
            return 1

        # Apply field filtering if requested
        fields = [f.strip() for f in args.fields.split(",")] if args.fields else None
        if fields:
            logger.info(f"Filtering fields: {fields}")
            items = select_fields(items, fields)

        # Convert to DataFrame and export
        df = pd.DataFrame(items)
        logger.info(f"Total rows: {len(df)}, columns: {list(df.columns)}")
        
        # Create output directory if needed
        args.output.parent.mkdir(parents=True, exist_ok=True)
        
        if args.output.suffix.lower() == ".csv":
            df.to_csv(args.output, index=False)
        elif args.output.suffix.lower() in [".xlsx", ".xls"]:
            df.to_excel(args.output, index=False)
        else:
            raise ValueError("Output must be .csv or .xlsx")
        
        logger.info(f"✓ Saved to {args.output}")
        logger.info("Next steps: Validate data quality, schedule with cron, or load to database")
        
        return 0

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 2
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())