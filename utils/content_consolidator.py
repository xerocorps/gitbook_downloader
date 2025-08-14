"""
Content Consolidator - Combines pages into a single markdown document
"""

import re
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

class ContentConsolidator:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.logger = get_logger()

    async def consolidate_pages(self, pages, base_url, section_path=None):
        """Consolidate all pages into a single markdown document"""
        if not pages:
            return "# No Content Found\n\nNo pages were successfully downloaded."

        # Sort pages for logical order
        sorted_pages = self._sort_pages(pages)

        # Generate document
        content_parts = []

        # Add header
        content_parts.append(self._generate_header(base_url, section_path, len(pages)))

        # Generate table of contents
        # toc = self._generate_toc(sorted_pages)
        # if toc:
            # content_parts.append("## Table of Contents\n")
            # content_parts.append(toc)
            # content_parts.append("\n---\n")

        # Add each page
        for i, page in enumerate(sorted_pages, 1):
            page_content = self._process_page_content(page, i)
            if page_content:
                content_parts.append(page_content)
                content_parts.append("\n---\n")

        # Combine and clean up
        final_content = "\n".join(content_parts)
        final_content = self._post_process_content(final_content)

        return final_content

    def _generate_header(self, base_url, section_path, page_count):
        """Generate document header"""
        from urllib.parse import urlparse

        domain = urlparse(base_url).netloc
        title = domain.replace('.gitbook.io', '').replace('.com', '').title()

        if section_path:
            title += f" - {section_path.replace('/', ' / ').title()}"

        header = f"""# {title}

*Downloaded with GitBook Multi-Strategy Downloader v4.0*

**Source:** {base_url}  
**Pages:** {page_count}  
**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
"""

        if section_path:
            header += f"**Section:** {section_path}  \n"

        header += "\n---\n"

        return header

    def _sort_pages(self, pages):
        """Sort pages in logical reading order"""
        def sort_key(page):
            title = page['title'].lower()
            url = page.get('url', '').lower()

            score = 0

            # Prioritize certain page types
            if any(word in title for word in ['readme', 'introduction', 'intro', 'start', 'index']):
                score += 1000

            if any(word in title for word in ['getting started', 'quick start', 'overview']):
                score += 900

            # Try to extract numeric prefixes
            import re
            numeric_match = re.search(r'(\d+)', title)
            if numeric_match:
                score += 800 - int(numeric_match.group(1))

            # Shorter paths/titles often come first
            score += max(0, 100 - len(title.split()))
            score += max(0, 50 - len(url.split('/')))

            return -score  # Negative for descending order

        return sorted(pages, key=sort_key)

    def _generate_toc(self, pages):
        """Generate table of contents"""
        if len(pages) <= 1:
            return ""

        toc_lines = []
        for page in pages:
            title = page['title']
            # Create anchor from title
            anchor = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
            anchor = re.sub(r'\s+', '-', anchor).lower()

            toc_lines.append(f"- [{title}](#{anchor})")

        return "\n".join(toc_lines)

    def _process_page_content(self, page, page_num):
        """Process individual page content"""
        title = page['title']
        content = page.get('content', '')
        source = page.get('source', 'unknown')

        if not content or not content.strip():
            self.logger.warning(f"Empty content for page: {title}")
            return None

        # Clean title for header
        clean_title = re.sub(r'[#\n]', '', title).strip()

        # Create page section
        section_parts = []
        # section_parts.append(f"## {clean_title}\n")

        # Add source info
        if page.get('url'):
            section_parts.append(f"*Source: {page['url']}*\n")
        elif page.get('path'):
            section_parts.append(f"*Source: {page['path']}*\n")

        # section_parts.append(f"*Method: {source}*\n\n")

        # Process content
        processed_content = self._clean_content(content)
        section_parts.append(processed_content)

        return "\n".join(section_parts)

    def _clean_content(self, content):
        """Clean and normalize content"""
        # Remove any existing title headers at the start
        lines = content.split('\n')

        # Skip initial empty lines and top-level headers
        start_idx = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            if line.startswith('# '):
                start_idx = i + 1
                continue
            break

        if start_idx > 0:
            lines = lines[start_idx:]

        # Adjust heading levels (bump everything down by 1)
        adjusted_lines = []
        for line in lines:
            if re.match(r'^#{1,5}\s', line):
                adjusted_lines.append('#' + line)
            else:
                adjusted_lines.append(line)

        content = '\n'.join(adjusted_lines)

        # Clean up excessive whitespace
        content = re.sub(r'\n{4,}', '\n\n\n', content)

        return content.strip()

    def _post_process_content(self, content):
        """Final post-processing of the complete document"""
        # Remove excessive whitespace
        content = re.sub(r'\n{4,}', '\n\n\n', content)

        # Fix any broken markdown
        content = re.sub(r'^#{7,}', '######', content, flags=re.MULTILINE)

        # Ensure document ends cleanly
        content = content.rstrip() + '\n'

        return content
