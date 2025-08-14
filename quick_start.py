#!/usr/bin/env python3
"""
Quick start script for GitBook Multi-Strategy Downloader v4.0
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from gitbook_multi_downloader import GitBookMultiDownloader

async def main():
    print("🚀 GitBook Multi-Strategy Downloader v4.0 - Quick Start")
    print("=" * 60)

    # Get URL from user
    url = input("Enter GitBook URL: ").strip()
    if not url:
        print("❌ No URL provided")
        return

    # Get output file
    output = input("Output file [gitbook.md]: ").strip() or "gitbook.md"

    # Ask about assets
    assets = input("Download assets? (y/n) [n]: ").strip().lower() == 'y'

    print(f"\n📥 Downloading: {url}")
    print(f"📁 Output: {output}")
    print(f"🖼️  Assets: {'Yes' if assets else 'No'}")
    print()

    # Create downloader
    downloader = GitBookMultiDownloader(
        url=url,
        output_file=output,
        strategy="auto",
        include_assets=assets,
        verbose=True
    )

    try:
        result = await downloader.download()

        print("\n" + "=" * 50)
        print("✅ SUCCESS!")
        print(f"📊 Strategy used: {result['strategy_used']}")
        print(f"📚 Pages downloaded: {result['pages_downloaded']}")
        print(f"⏱️  Time taken: {result['duration']:.1f}s")
        print(f"🚀 Speed: {result['pages_per_second']:.1f} pages/sec")

        if result.get('assets_downloaded', 0) > 0:
            print(f"🖼️  Assets downloaded: {result['assets_downloaded']}")

        print(f"📁 Output saved to: {result['output_file']}")

    except KeyboardInterrupt:
        print("\n🛑 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\n💡 Try different options:")
        print("   - Add --verbose flag for more details")
        print("   - Try --strategy scraping for difficult sites")
        print("   - Reduce --max-concurrent if getting rate limited")

if __name__ == "__main__":
    asyncio.run(main())
