"""
Enhanced Scraping Strategy - Web scraping with navigation discovery
"""

import asyncio
import aiohttp
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from utils.logger import get_logger

class ScrapingStrategy:
    def __init__(self, max_concurrent=15, delay=0.1, timeout=30, 
                 use_selenium=False, verbose=False):
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.timeout = timeout
        self.use_selenium = use_selenium
        self.verbose = verbose
        self.logger = get_logger()

        # Navigation selectors for different GitBook layouts
        self.nav_selectors = [
            # Modern GitBook
            '[data-testid="sidebar"] a[href]',
            '[data-testid="navigation"] a[href]',
            '.sidebar a[href]',
            '.navigation a[href]',

            # Legacy GitBook
            '.book-summary a[href]',
            '.summary a[href]',

            # Generic
            'nav a[href]',
            '.nav a[href]',
            '.toc a[href]',
            'aside a[href]',
        ]

    async def extract_pages(self, url, section_path=None):
        """Extract pages using web scraping"""
        try:
            # Step 1: Discover navigation links
            nav_links = await self._discover_navigation(url)

            if not nav_links:
                # Fallback - at least get the main page
                nav_links = [{'url': url, 'title': 'Main Page'}]

            # Step 2: Filter by section if specified
            if section_path:
                nav_links = [link for link in nav_links 
                           if section_path.lower() in link['url'].lower()]

            # Step 3: Download all pages
            pages = await self._download_pages(nav_links)

            return pages

        except Exception as e:
            self.logger.debug(f"Scraping strategy error: {e}")
            return None

    async def _discover_navigation(self, url):
        """Discover navigation links from the main page"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.timeout)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return []

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    links = []
                    base_domain = urlparse(url).netloc

                    # Try each navigation selector
                    for selector in self.nav_selectors:
                        nav_links = soup.select(selector)

                        for link in nav_links:
                            href = link.get('href', '')
                            text = link.get_text().strip()

                            if not href or not text:
                                continue

                            # Convert to absolute URL
                            abs_url = urljoin(url, href)

                            # Validate URL
                            if self._is_valid_page_url(abs_url, base_domain):
                                links.append({
                                    'url': abs_url,
                                    'title': text[:100]  # Limit title length
                                })

                        # If we found good links with this selector, use them
                        if len(links) > 5:
                            break

                    # Remove duplicates
                    unique_links = []
                    seen_urls = set()

                    for link in links:
                        if link['url'] not in seen_urls:
                            unique_links.append(link)
                            seen_urls.add(link['url'])

                    self.logger.info(f"Discovered {len(unique_links)} navigation links")
                    return unique_links

        except Exception as e:
            self.logger.debug(f"Navigation discovery error: {e}")
            return []

    def _is_valid_page_url(self, url, base_domain):
        """Check if URL is a valid page to scrape"""
        if not url or url.startswith('#'):
            return False

        parsed = urlparse(url)

        # Must be same domain
        if parsed.netloc != base_domain:
            return False

        # Skip non-content URLs
        skip_patterns = [
            r'/search', r'/login', r'/logout', r'/edit',
            r'/admin', r'/api/', r'/assets/', r'/static/',
            r'\.(css|js|json|xml|rss|txt)$',
            r'\.(jpg|png|gif|svg|ico|pdf)$',
            r'mailto:', r'tel:', r'javascript:'
        ]

        url_lower = url.lower()
        for pattern in skip_patterns:
            if re.search(pattern, url_lower):
                return False

        return True

    async def _download_pages(self, nav_links):
        """Download content from all navigation links"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        pages = []

        async def download_page(link):
            async with semaphore:
                await asyncio.sleep(self.delay)

                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.timeout)) as session:
                        async with session.get(link['url']) as response:
                            if response.status == 200:
                                html = await response.text()
                                content = self._extract_main_content(html)

                                if content and len(content.strip()) > 50:  # Minimum content length
                                    pages.append({
                                        'title': link['title'],
                                        'url': link['url'],
                                        'content': content,
                                        'source': 'scraping',
                                        'html': html
                                    })

                except Exception as e:
                    self.logger.debug(f"Error downloading {link['url']}: {e}")

        # Download all pages concurrently
        tasks = [download_page(link) for link in nav_links]
        await asyncio.gather(*tasks, return_exceptions=True)

        return pages

    def _extract_main_content(self, html):
        """Extract main content from HTML page"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        unwanted_selectors = [
            'nav', 'header', 'footer', 'aside', 
            '.sidebar', '.navigation', '.nav', '.header', '.footer',
            '.breadcrumb', '.breadcrumbs', '.page-edit-link',
            'script', 'style', 'noscript',
            '.search', '.share', '.comments'
        ]

        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()

        # Find main content area
        content_selectors = [
            '[data-testid="page-content"]',
            '.page-content',
            '.content',
            'main',
            'article',
            '.post-content',
            '.entry-content'
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Convert to markdown-like text
                return self._html_to_text(content_elem)

        # Fallback - use body content
        body = soup.find('body')
        if body:
            return self._html_to_text(body)

        return soup.get_text()

    def _html_to_text(self, element):
        """Convert HTML element to clean text with basic markdown formatting"""
        # This is a simple HTML to text converter
        # For production, you might want to use a proper HTML-to-markdown library

        text_lines = []

        def process_element(elem):
            if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(elem.name[1])
                heading = '#' * level + ' ' + elem.get_text().strip()
                text_lines.append(heading)
                text_lines.append('')
            elif elem.name == 'p':
                text_lines.append(elem.get_text().strip())
                text_lines.append('')
            elif elem.name in ['ul', 'ol']:
                for li in elem.find_all('li', recursive=False):
                    text_lines.append('- ' + li.get_text().strip())
                text_lines.append('')
            elif elem.name == 'code':
                text_lines.append('`' + elem.get_text().strip() + '`')
            elif elem.name == 'pre':
                code_text = elem.get_text().strip()
                text_lines.append('```')
                text_lines.append(code_text)
                text_lines.append('```')
                text_lines.append('')
            else:
                # For other elements, just get the text
                for child in elem.children:
                    if hasattr(child, 'name') and child.name:
                        process_element(child)
                    else:
                        # Text node
                        text = str(child).strip()
                        if text:
                            text_lines.append(text)

        process_element(element)

        # Join and clean up
        result = '\n'.join(text_lines)

        # Remove excessive blank lines
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip()
