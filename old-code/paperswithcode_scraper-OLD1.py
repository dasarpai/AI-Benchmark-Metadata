#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Papers With Code Scraper

This script scrapes the Papers With Code SOTA page to find benchmark links,
downloads HTML content for each benchmark page, and saves it locally.
It's designed to help researchers collect comprehensive metadata about AI benchmarks.

Usage:
    python paperswithcode_scraper.py

The script will:
1. Scrape the main SOTA page to find benchmark links
2. Download HTML content for each benchmark page
3. Save the HTML content locally in the paperswithcode directory
"""

import os
import time
import random
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://paperswithcode.com"
SOTA_URL = "https://paperswithcode.com/sota"
BENCHMARKS_DIR = "paperswithcode"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def setup_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(BENCHMARKS_DIR, exist_ok=True)
    logger.info(f"Created directory: {BENCHMARKS_DIR}")

def get_benchmark_urls_from_sota_page():
    """
    Extract benchmark URLs from the main SOTA page.
    
    Returns:
        List of benchmark URLs
    """
    logger.info(f"Scraping benchmark URLs from SOTA page: {SOTA_URL}")
    
    benchmark_urls = []
    
    try:
        # Add a random delay to avoid being blocked
        delay = random.uniform(1.0, 3.0)
        logger.info(f"Waiting {delay:.2f} seconds before accessing {SOTA_URL}")
        time.sleep(delay)
        
        # Get the SOTA page
        response = requests.get(SOTA_URL, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all h4 elements which contain area links
        h4_elements = soup.find_all('h4')
        
        # For each area, find all benchmark links
        for h4 in h4_elements:
            # Find the parent div that contains both the h4 and the benchmark links
            parent_div = h4.find_parent('div')
            if parent_div:
                # Find all links within this div that might lead to benchmark pages
                links = parent_div.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href')
                    if href and href.startswith('/sota/'):
                        full_url = urljoin(BASE_URL, href)
                        if full_url not in benchmark_urls:  # Avoid duplicates
                            benchmark_urls.append(full_url)
                            logger.info(f"Found benchmark URL: {full_url}")
        
        logger.info(f"Found {len(benchmark_urls)} benchmark URLs from SOTA page")
        
    except Exception as e:
        logger.error(f"Error scraping benchmark URLs from SOTA page: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return benchmark_urls

def download_benchmark_page(url):
    """
    Download HTML content for a benchmark page.
    
    Args:
        url: URL of the benchmark page
        
    Returns:
        HTML content of the page
    """
    try:
        # Add a random delay to avoid being blocked
        delay = random.uniform(1.0, 3.0)
        logger.info(f"Waiting {delay:.2f} seconds before downloading {url}")
        time.sleep(delay)
        
        # Download the page
        response = requests.get(url, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        
        logger.info(f"Successfully downloaded {url} (size: {len(response.text)} bytes)")
        return response.text
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def save_html_content(url, html_content):
    """
    Save HTML content to a file.
    
    Args:
        url: URL of the benchmark page
        html_content: HTML content to save
    """
    if not html_content:
        logger.warning(f"No HTML content to save for {url}")
        return
    
    try:
        # Extract benchmark name from URL
        # Example: https://paperswithcode.com/sota/image-classification-on-imagenet -> image-classification-on-imagenet
        benchmark_name = url.split('/')[-1]
        
        # Sanitize filename
        filename = f"pwc_{benchmark_name}.html"
        filename = re.sub(r'[\\/*?:"<>|]', '_', filename)  # Replace invalid filename characters
        
        # Save the HTML content
        file_path = os.path.join(BENCHMARKS_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Saved HTML content to {file_path}")
    except Exception as e:
        logger.error(f"Error saving HTML content for {url}: {e}")
        import traceback
        logger.error(traceback.format_exc())

def scrape_benchmarks():
    """
    Main function to scrape benchmark pages from Papers With Code.
    """
    # Create necessary directories
    setup_directories()
    
    # Get benchmark URLs from the SOTA page
    benchmark_urls = get_benchmark_urls_from_sota_page()
    print("xxxxxxxxxxxx",benchmark_urls)
    
    if not benchmark_urls:
        logger.warning("No benchmark URLs found. Using fallback list.")
        # Fallback to a predefined list if no URLs are found
        benchmark_urls = [
            "https://paperswithcode.com/area/computer-vision",
            "https://paperswithcode.com/area/natural-language-processing",
            "https://paperswithcode.com/area/medical",
            "https://paperswithcode.com/area/miscellaneous",
            "https://paperswithcode.com/area/methodology",
            "https://paperswithcode.com/area/time-series",
            "https://paperswithcode.com/area/graphs",
            "https://paperswithcode.com/area/audio",
            "https://paperswithcode.com/area/speech",
            "https://paperswithcode.com/area/reasoning",
            "https://paperswithcode.com/area/computer-code",
            "https://paperswithcode.com/area/robots",
            "https://paperswithcode.com/area/adversarial",
            "https://paperswithcode.com/area/knowledge-base",
            "https://paperswithcode.com/area/playing-games",
            "https://paperswithcode.com/area/music"
        ]
    
    # Download and save HTML content for each benchmark
    successful_downloads = 0
    
    for i, url in enumerate(benchmark_urls):
        logger.info(f"Processing benchmark {i+1}/{len(benchmark_urls)}: {url}")
        
        # Download the benchmark page
        html_content = download_benchmark_page(url)
        
        # Save the HTML content
        if html_content:
            save_html_content(url, html_content)
            successful_downloads += 1
    
    logger.info(f"Completed scraping. Successfully downloaded {successful_downloads} out of {len(benchmark_urls)} benchmarks")

if __name__ == '__main__':
    scrape_benchmarks()
