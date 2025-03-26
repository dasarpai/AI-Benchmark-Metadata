#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Debug script for Papers With Code HTML processing
"""

import os
import logging
from bs4 import BeautifulSoup

# Set up logging to file
log_file = "pwc_debug.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler()  # Still log to console
    ]
)
logger = logging.getLogger(__name__)

# Constants
BENCHMARKS_DIR = "paperswithcode"
DEBUG_OUTPUT = "pwc_debug_output.txt"

def is_area_page(html_content):
    """
    Determine if the HTML content is from an area page or a specific benchmark page.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Area pages typically have a title like "Speech | Papers With Code"
    title = soup.find('title')
    if title and '|' in title.text and 'Papers With Code' in title.text:
        # Check if there's no SOTA table, which is present in benchmark pages
        sota_table = soup.select_one('.leaderboard-table-container')
        if not sota_table:
            return True
    
    return False

def main():
    """
    Main function to debug HTML files.
    """
    # Open debug output file
    with open(DEBUG_OUTPUT, 'w', encoding='utf-8') as debug_file:
        debug_file.write("Papers With Code HTML Debug Output\n")
        debug_file.write("=================================\n\n")
        
        try:
            # Check if the directory exists
            if not os.path.exists(BENCHMARKS_DIR):
                error_msg = f"Directory {BENCHMARKS_DIR} does not exist"
                logger.error(error_msg)
                debug_file.write(f"ERROR: {error_msg}\n")
                return
            
            # Get all HTML files
            html_files = [f for f in os.listdir(BENCHMARKS_DIR) if f.endswith('.html')]
            info_msg = f"Found {len(html_files)} HTML files"
            logger.info(info_msg)
            debug_file.write(f"{info_msg}\n\n")
            
            # Process files
            area_pages = []
            benchmark_pages = []
            
            for html_file in html_files:
                file_path = os.path.join(BENCHMARKS_DIR, html_file)
                
                try:
                    info_msg = f"Processing file: {html_file}"
                    logger.info(info_msg)
                    debug_file.write(f"{info_msg}\n")
                    
                    # Read the HTML content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        html_content = f.read()
                    
                    info_msg = f"Read {len(html_content)} bytes from {html_file}"
                    logger.info(info_msg)
                    debug_file.write(f"{info_msg}\n")
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Get title
                    title = soup.find('title')
                    title_text = title.text if title else "No title found"
                    info_msg = f"Title: {title_text}"
                    logger.info(info_msg)
                    debug_file.write(f"{info_msg}\n")
                    
                    # Check if this is an area page
                    area = is_area_page(html_content)
                    info_msg = f"Is area page: {area}"
                    logger.info(info_msg)
                    debug_file.write(f"{info_msg}\n")
                    
                    # Check for key elements
                    leaderboard = soup.select_one('.leaderboard-table-container')
                    debug_file.write(f"Has leaderboard: {leaderboard is not None}\n")
                    
                    # Check for benchmark description
                    description = soup.select_one('.benchmark-description')
                    debug_file.write(f"Has description: {description is not None}\n")
                    
                    # Check for dataset section
                    dataset = soup.select_one('.dataset-section')
                    debug_file.write(f"Has dataset section: {dataset is not None}\n")
                    
                    # Check for benchmark links
                    benchmark_links = soup.select('a[href^="/sota/"]')
                    debug_file.write(f"Number of benchmark links: {len(benchmark_links)}\n")
                    
                    if area:
                        area_pages.append(html_file)
                    else:
                        benchmark_pages.append(html_file)
                    
                    debug_file.write("\n")
                    
                except Exception as e:
                    error_msg = f"Error processing {html_file}: {str(e)}"
                    logger.error(error_msg)
                    debug_file.write(f"ERROR: {error_msg}\n\n")
                    import traceback
                    error_trace = traceback.format_exc()
                    logger.error(error_trace)
                    debug_file.write(f"{error_trace}\n\n")
            
            # Summary
            debug_file.write("\nSUMMARY\n=======\n")
            info_msg = f"Area pages ({len(area_pages)}): {', '.join(area_pages)}"
            logger.info(info_msg)
            debug_file.write(f"{info_msg}\n\n")
            
            info_msg = f"Benchmark pages ({len(benchmark_pages)}): {', '.join(benchmark_pages)}"
            logger.info(info_msg)
            debug_file.write(f"{info_msg}\n")
            
        except Exception as e:
            error_msg = f"Error in main function: {str(e)}"
            logger.error(error_msg)
            debug_file.write(f"ERROR: {error_msg}\n")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(error_trace)
            debug_file.write(f"{error_trace}\n")

if __name__ == '__main__':
    main()
