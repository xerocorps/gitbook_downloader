#!/usr/bin/env python3
"""
Example usage of GitBook Multi-Strategy Downloader v4.0
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from gitbook_multi_downloader import GitBookMultiDownloader

async def example_auto_strategy():
    """Example: Auto-strategy (tries all methods)"""
    print("🚀 Example 1: Auto-strategy download")

    downloader = GitBookMultiDownloader(
        url="https://appsecexplained.gitbook.io/appsecexplained",
        output_file="appsec-auto.md",
        strategy="auto",
        verbose=True
    )

    try:
        result = await downloader.download()
        print(f"✅ Success! Strategy: {result['strategy_used']}, Pages: {result['pages_downloaded']}")
    except Exception as e:
        print(f"❌ Failed: {e}")

async def example_force_scraping():
    """Example: Force scraping strategy"""
    print("🚀 Example 2: Force scraping strategy")

    downloader = GitBookMultiDownloader(
        url="https://x3m1sec.gitbook.io/notes/",
        output_file="x3m1sec-scraping.md",
        strategy="scraping",
        max_concurrent=10,
        delay=0.2,
        verbose=True
    )

    try:
        result = await downloader.download()
        print(f"✅ Success! Pages: {result['pages_downloaded']}")
    except Exception as e:
        print(f"❌ Failed: {e}")

async def example_with_assets():
    """Example: Download with assets"""
    print("🚀 Example 3: Download with assets")

    downloader = GitBookMultiDownloader(
        url="https://docs.example.com",
        output_file="docs-with-assets.md",
        include_assets=True,
        verbose=True
    )

    try:
        result = await downloader.download()
        print(f"✅ Success! Pages: {result['pages_downloaded']}, Assets: {result['assets_downloaded']}")
    except Exception as e:
        print(f"❌ Failed: {e}")

async def main():
    print("GitBook Multi-Strategy Downloader v4.0 Examples")
    print("=" * 50)

    examples = [
        ("Auto-strategy (recommended)", example_auto_strategy),
        ("Force scraping", example_force_scraping),  
        ("With assets", example_with_assets),
    ]

    print("Choose an example:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    try:
        choice = int(input("\nEnter choice (1-3): "))
        if 1 <= choice <= len(examples):
            name, example_func = examples[choice - 1]
            print(f"\nRunning: {name}")
            await example_func()
        else:
            print("Invalid choice")
    except (ValueError, KeyboardInterrupt):
        print("\nExiting...")

if __name__ == "__main__":
    asyncio.run(main())
