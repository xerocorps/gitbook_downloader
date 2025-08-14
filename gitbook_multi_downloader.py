"""
GitBook Multi-Strategy Downloader v4.0
Tries multiple approaches: GitHub cloning → Sitemap parsing → Web scraping
"""

import asyncio
import aiohttp
import time
import shutil
from pathlib import Path
from utils.logger import get_logger
from strategies.github_strategy import GitHubStrategy
from strategies.sitemap_strategy import SitemapStrategy  
from strategies.scraping_strategy import ScrapingStrategy
from utils.content_consolidator import ContentConsolidator
from utils.asset_downloader import AssetDownloader

class GitBookMultiDownloader:
    def __init__(self, url, output_file, strategy='auto', section_path=None,
                 max_concurrent=15, delay=0.1, timeout=30, include_assets=False,
                 keep_temp=False, use_selenium=False, verbose=False):

        self.url = url.rstrip('/')
        self.output_file = Path(output_file)
        self.strategy = strategy
        self.section_path = section_path
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.timeout = timeout
        self.include_assets = include_assets
        self.keep_temp = keep_temp
        self.use_selenium = use_selenium
        self.verbose = verbose

        self.logger = get_logger()

        # Initialize strategies
        self.strategies = {
            'github': GitHubStrategy(verbose=verbose),
            'sitemap': SitemapStrategy(
                max_concurrent=max_concurrent,
                delay=delay, 
                timeout=timeout,
                verbose=verbose
            ),
            'scraping': ScrapingStrategy(
                max_concurrent=max_concurrent,
                delay=delay,
                timeout=timeout,
                use_selenium=use_selenium,
                verbose=verbose
            )
        }

        # Content processor
        self.consolidator = ContentConsolidator(verbose=verbose)
        self.asset_downloader = AssetDownloader(verbose=verbose) if include_assets else None

        # Statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'strategy_used': None,
            'pages_downloaded': 0,
            'assets_downloaded': 0,
            'errors': 0
        }

    async def download(self):
        """Main download method - tries strategies in order"""
        self.stats['start_time'] = time.time()

        try:
            # Determine which strategies to try
            if self.strategy == 'auto':
                strategy_order = ['github', 'sitemap', 'scraping']
            else:
                strategy_order = [self.strategy]

            pages = None
            successful_strategy = None

            # Try each strategy until one succeeds
            for strategy_name in strategy_order:
                try:
                    self.logger.info(f"🔄 Trying {strategy_name} strategy...")

                    strategy = self.strategies[strategy_name]
                    pages = await strategy.extract_pages(self.url, self.section_path)

                    if pages and len(pages) > 0:
                        successful_strategy = strategy_name
                        self.logger.info(f"✅ {strategy_name} strategy succeeded - found {len(pages)} pages")
                        break
                    else:
                        self.logger.warning(f"⚠️  {strategy_name} strategy found no pages")

                except Exception as e:
                    self.logger.warning(f"❌ {strategy_name} strategy failed: {e}")
                    if self.verbose:
                        self.logger.debug(f"Strategy error details: {e}")
                    continue

            if not pages:
                raise Exception("All download strategies failed - could not extract any pages")

            self.stats['strategy_used'] = successful_strategy
            self.stats['pages_downloaded'] = len(pages)

            # Consolidate content
            self.logger.info("📝 Consolidating content...")
            final_content = await self.consolidator.consolidate_pages(
                pages, 
                self.url, 
                self.section_path
            )

            # Download assets if requested
            if self.include_assets and self.asset_downloader:
                self.logger.info("🖼️  Downloading assets...")
                assets_downloaded = await self.asset_downloader.download_assets(
                    pages, 
                    self.output_file.parent / 'assets'
                )
                self.stats['assets_downloaded'] = assets_downloaded

                # Update content with asset paths
                final_content = self.asset_downloader.update_asset_references(
                    final_content, 'assets'
                )

            # Write final file
            self.logger.info("💾 Writing output file...")
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)

            # Cleanup temporary files if not keeping them
            if not self.keep_temp:
                self._cleanup_temp_files()

            self.stats['end_time'] = time.time()
            duration = self.stats['end_time'] - self.stats['start_time']

            return {
                'success': True,
                'strategy_used': successful_strategy,
                'pages_downloaded': self.stats['pages_downloaded'],
                'assets_downloaded': self.stats['assets_downloaded'],
                'duration': duration,
                'pages_per_second': self.stats['pages_downloaded'] / max(duration, 0.1),
                'output_file': str(self.output_file)
            }

        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            self._cleanup_temp_files()
            raise

    def _cleanup_temp_files(self):
        """Clean up any temporary files/directories"""
        temp_dirs = ['temp_repo', 'temp_download', 'selenium_temp']

        for temp_dir in temp_dirs:
            temp_path = Path(temp_dir)
            if temp_path.exists():
                try:
                    shutil.rmtree(temp_path)
                    self.logger.debug(f"Cleaned up {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Could not clean up {temp_dir}: {e}")
