#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hugging Face Dataset Scraper

This script scrapes the Hugging Face datasets catalog to get a list of all available datasets,
then downloads the HTML content for each dataset page and saves it locally.

Usage:
    python huggingface_dataset_scraper.py

The script will:
1. Scrape the Hugging Face datasets catalog to get a list of all available datasets
2. Download the HTML content for each dataset page
3. Save the HTML content to a file in the huggingface directory

After running this script, you can run huggingface_html_2_csv.py to extract information
from the downloaded HTML files and save it to a CSV file.
"""

import os
import time
import requests
import logging
import concurrent.futures
from typing import List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://huggingface.co"
DATASETS_URL = f"{BASE_URL}/datasets"
DATASETS_DIR = "huggingface"
REQUEST_TIMEOUT = 30  # seconds
REQUEST_DELAY = 1  # seconds
MAX_RETRIES = 3
MAX_WORKERS = 10  # Number of concurrent requests

def get_dataset_list(page_count=10) -> List[Tuple[str, str]]:
    """
    Scrape the Hugging Face datasets catalog to get a list of all available datasets.
    
    Args:
        page_count: Number of pages to scrape (each page contains multiple datasets)
        
    Returns:
        List of tuples containing (dataset_name, dataset_url)
    """
    logger.info(f"Scraping dataset list from Hugging Face (up to {page_count} pages)...")
    all_datasets = []
    
    for page in range(1, page_count + 1):
        url = f"{DATASETS_URL}?p={page}"
        logger.info(f"Scraping page {page}: {url}")
        
        try:
            # Add headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                logger.error(f"Failed to fetch page {page}: Status code {response.status_code}")
                continue
            
            # Save the HTML content to debug the structure
            debug_file = os.path.join(DATASETS_DIR, f"huggingface_page_{page}.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Saved page {page} HTML to {debug_file} for debugging")
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try different selectors to find dataset cards
            # 1. Try the original selector
            dataset_cards = soup.select('.dataset-card')
            
            # 2. If that doesn't work, try alternative selectors
            if not dataset_cards:
                dataset_cards = soup.select('article')
            
            if not dataset_cards:
                dataset_cards = soup.select('div[class*="card"]')
                
            if not dataset_cards:
                dataset_cards = soup.select('div[class*="dataset"]')
                
            logger.info(f"Found {len(dataset_cards)} dataset cards on page {page}")
            
            if not dataset_cards:
                # If we still can't find any cards, try to find any links to datasets
                all_links = soup.select('a[href*="/datasets/"]')
                logger.info(f"Found {len(all_links)} links to datasets on page {page}")
                
                for link in all_links:
                    href = link.get('href', '')
                    if href.startswith('/datasets/') and '/datasets/viewer/' not in href and len(href.split('/')) >= 3:
                        dataset_name = href.split('/')[2]
                        if dataset_name and not dataset_name.startswith('?'):
                            full_url = urljoin(BASE_URL, href)
                            all_datasets.append((dataset_name, full_url))
                            logger.info(f"Added dataset from link: {dataset_name} - {full_url}")
            else:
                # Extract dataset names and URLs from cards
                for card in dataset_cards:
                    try:
                        # Find the link to the dataset
                        link = card.select_one('a')
                        if link and 'href' in link.attrs:
                            dataset_url = link['href']
                            if dataset_url.startswith('/datasets/'):
                                dataset_name = dataset_url.split('/')[2]
                                if dataset_name:
                                    full_url = urljoin(BASE_URL, dataset_url)
                                    all_datasets.append((dataset_name, full_url))
                                    logger.info(f"Added dataset from card: {dataset_name} - {full_url}")
                    except Exception as e:
                        logger.error(f"Error extracting dataset info from card: {e}")
            
            # If we didn't find any datasets on this page and we're past page 1, 
            # we might have reached the end of the dataset list
            if not dataset_cards and not all_links and page > 1:
                logger.info(f"No datasets found on page {page}, might have reached the end of the list")
                break
            
            # Add a delay to avoid overwhelming the server
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            logger.error(f"Error scraping page {page}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # If we didn't find any datasets, use a hardcoded list of popular datasets as a fallback
    if not all_datasets:
        logger.warning("Could not find any datasets through scraping. Using fallback list of popular datasets.")
        popular_datasets = [
            "squad", "glue", "super_glue", "imdb", "wmt16", "cnn_dailymail", "common_voice",
            "xnli", "multi_nli", "sst2", "mnli", "cola", "rte", "wnli", "qnli", "mrpc", "stsb",
            "boolq", "record", "multirc", "wic", "copa", "wsc", "cb", "race", "drop", "newsqa",
            "natural_questions", "triviaqa", "hotpotqa", "squad_v2", "xquad", "mlqa", "tydiqa",
            "piqa", "winogrande", "hellaswag", "commonsense_qa", "arc", "openbookqa", "sciq",
            "ai2_arc", "adversarial_qa", "quoref", "quail", "quartz", "cosmos_qa", "dream"
        ]
        
        for dataset_name in popular_datasets:
            dataset_url = f"{BASE_URL}/datasets/{dataset_name}"
            all_datasets.append((dataset_name, dataset_url))
            logger.info(f"Added dataset from fallback list: {dataset_name} - {dataset_url}")
    
    logger.info(f"Extracted {len(all_datasets)} dataset names and URLs in total")
    return all_datasets

def download_dataset_page(dataset):
    """
    Download the HTML content for a dataset page.
    
    Args:
        dataset: Tuple containing (dataset_name, dataset_url)
        
    Returns:
        Tuple containing (dataset_name, success)
    """
    dataset_name, dataset_url = dataset
    logger.info(f"Downloading {dataset_name} from {dataset_url}")
    
    # Create file path for the HTML file
    file_path = os.path.join(DATASETS_DIR, f"huggingface_{dataset_name}.html")
    
    # Check if file already exists
    if os.path.exists(file_path):
        logger.info(f"File already exists for {dataset_name}, skipping download")
        return dataset_name, True
    
    # Try to download the page with retries
    for attempt in range(MAX_RETRIES):
        try:
            # Add headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(dataset_url, headers=headers, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                # Save the HTML content to a file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info(f"Successfully downloaded {dataset_name}")
                return dataset_name, True
            else:
                logger.warning(f"Failed to download {dataset_name}: Status code {response.status_code} (Attempt {attempt+1}/{MAX_RETRIES})")
                time.sleep(REQUEST_DELAY * (attempt + 1))  # Exponential backoff
        
        except Exception as e:
            logger.error(f"Error downloading {dataset_name}: {e} (Attempt {attempt+1}/{MAX_RETRIES})")
            time.sleep(REQUEST_DELAY * (attempt + 1))  # Exponential backoff
    
    logger.error(f"Failed to download {dataset_name} after {MAX_RETRIES} attempts")
    return dataset_name, False

def main():
    """
    Main function to scrape dataset list and download HTML content.
    """
    # Create necessary directories
    os.makedirs(DATASETS_DIR, exist_ok=True)
    
    # Get list of datasets
    datasets = get_dataset_list(page_count=20)  # Adjust page_count as needed
    
    # Download HTML content for each dataset
    logger.info(f"Downloading HTML content for {len(datasets)} datasets...")
    
    successful_downloads = 0
    failed_downloads = 0
    
    # Use ThreadPoolExecutor for concurrent downloads
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit download tasks
        future_to_dataset = {executor.submit(download_dataset_page, dataset): dataset for dataset in datasets}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_dataset):
            dataset = future_to_dataset[future]
            try:
                dataset_name, success = future.result()
                if success:
                    successful_downloads += 1
                else:
                    failed_downloads += 1
                logger.info(f"Progress: {successful_downloads + failed_downloads}/{len(datasets)} datasets processed")
            except Exception as e:
                logger.error(f"Error processing {dataset[0]}: {e}")
                failed_downloads += 1
    
    logger.info(f"Completed scraping. Successfully downloaded {successful_downloads} datasets, failed to download {failed_downloads} datasets.")
    logger.info(f"HTML files saved to {DATASETS_DIR} directory.")
    logger.info(f"Now you can run huggingface_html_2_csv.py to extract information from the downloaded HTML files.")

if __name__ == '__main__':
    main()
