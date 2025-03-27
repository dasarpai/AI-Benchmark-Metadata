#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Papers With Code Scraper

This script scrapes the Papers With Code website to download HTML content for benchmarks
and datasets. It follows a hierarchical approach:

1. Extract all areas from the SOTA page
2. Extract subtasks from each area page
3. Extract tasks from each subtask page
4. Extract datasets from each task page
5. Download and save the HTML content for datasets only

Usage:
    python paperswithcode_scraper.py

The script will create necessary directories and save the HTML content for later processing.
"""

import os
import time
import re
import requests
from bs4 import BeautifulSoup
import logging
import random
from urllib.parse import urljoin, urlparse
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SOTA_URL = "https://paperswithcode.com/sota"
BASE_URL = "https://paperswithcode.com"
OUTPUT_DIR = "paperswithcode"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

# Track progress
PROGRESS_FILE = "pwc_scraper_progress.json"

def get_filename_from_url(url):
    """
    Generate a filename from a URL.
    
    Args:
        url: URL to generate filename from
        
    Returns:
        Filename
    """
    # Extract the last part of the URL to use as the filename
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    
    if path_parts:
        filename = path_parts[-1].replace('-', '_')
    else:
        filename = "index"
    
    # Add prefix and extension
    filename = f"pwc_{filename}.html"
    return filename

def download_page(url, download=True):
    """
    Download a page from Papers With Code.
    
    Args:
        url: URL to download
        download: Whether to save the HTML content to a file
        
    Returns:
        HTML content of the page
    """
    try:
        logger.info(f"Downloading {url}")
        
        # Add a random delay to be respectful to the server
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)
        
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        
        # Save to file if requested
        if download:
            filename = get_filename_from_url(url)
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Saved HTML content to {filepath}")
        
        return html_content
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {url}: {e}")
        return None

def extract_areas_from_sota_page():
    """
    Extract areas from the SOTA page.
    
    Returns:
        List of dictionaries with area names and URLs
    """
    logger.info(f"Extracting areas from {SOTA_URL}")
    
    html_content = download_page(SOTA_URL, download=False)
    if not html_content:
        logger.error("Failed to download SOTA page")
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all area links
    area_links = soup.select('a[href^="/area/"]')
    
    if not area_links:
        logger.warning("No area links found on SOTA page")
        return []
    
    # Filter out duplicates by URL
    unique_areas = {}
    
    for link in area_links:
        area_url = urljoin(BASE_URL, link.get('href', ''))
        
        # Skip if we've already seen this URL
        if area_url in unique_areas:
            continue
        
        # Get the area name from the link text
        area_name = link.get_text(strip=True)
        
        # If no name, use the last part of the URL
        if not area_name:
            parsed_url = urlparse(area_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if path_parts:
                area_name = path_parts[-1].replace('-', ' ').title()
        
        if area_url and area_name:
            unique_areas[area_url] = {
                'name': area_name,
                'url': area_url
            }
    
    areas = list(unique_areas.values())
    logger.info(f"Found {len(areas)} unique areas")
    return areas

def extract_subtasks_from_area_page(area, html_content):
    """
    Extract subtasks from an area page.
    
    Args:
        area: Dictionary with area name and URL
        html_content: HTML content of the area page
        
    Returns:
        List of dictionaries with subtask names and URLs
    """
    logger.info(f"Extracting subtasks from {area['name']} - {area['url']}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try multiple approaches to find subtask links
    
    # Approach 1: Find all subtask links with /sota/ prefix
    subtask_links = soup.select('a[href^="/sota/"]')
    
    # Approach 2: If no subtask links found, look for task cards
    if not subtask_links:
        logger.info(f"No direct subtask links found, looking for task cards")
        task_cards = soup.select('div.card')
        
        if task_cards:
            logger.info(f"Found {len(task_cards)} task cards")
            subtask_links = []
            
            for card in task_cards:
                links = card.select('a')
                for link in links:
                    href = link.get('href', '')
                    if '/sota/' in href or '/task/' in href:
                        subtask_links.append(link)
    
    # Approach 3: If still no subtask links, look for any links in the content area
    if not subtask_links:
        logger.info(f"No task cards found, looking for links in content area")
        content_area = soup.select_one('div.content')
        
        if content_area:
            subtask_links = []
            for link in content_area.select('a'):
                href = link.get('href', '')
                if '/sota/' in href or '/task/' in href:
                    subtask_links.append(link)
    
    if not subtask_links:
        logger.warning(f"No subtask links found on area page: {area['url']}")
        return []
    
    logger.info(f"Found {len(subtask_links)} potential subtask links")
    
    # Filter out duplicates by URL
    unique_subtasks = {}
    
    for link in subtask_links:
        subtask_url = urljoin(BASE_URL, link.get('href', ''))
        
        # Skip if we've already seen this URL
        if subtask_url in unique_subtasks:
            continue
        
        # Get the subtask name from the link text
        subtask_name = link.get_text(strip=True)
        
        # If no name, use the last part of the URL
        if not subtask_name:
            parsed_url = urlparse(subtask_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if path_parts:
                subtask_name = path_parts[-1].replace('-', ' ').title()
        
        if subtask_url and subtask_name:
            unique_subtasks[subtask_url] = {
                'name': subtask_name,
                'url': subtask_url,
                'area': area['name']
            }
    
    subtasks = list(unique_subtasks.values())
    logger.info(f"Found {len(subtasks)} unique subtasks for area {area['name']}")
    return subtasks

def extract_tasks_from_subtask_page(subtask, html_content):
    """
    Extract tasks from a subtask page.
    
    Args:
        subtask: Dictionary with subtask name and URL
        html_content: HTML content of the subtask page
        
    Returns:
        List of dictionaries with task names and URLs
    """
    logger.info(f"Extracting tasks from {subtask['name']} - {subtask['url']}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try multiple approaches to find task links
    
    # Approach 1: Find all task links with /task/ prefix
    task_links = soup.select('a[href^="/task/"]')
    
    # Approach 2: If no task links found, look for task cards
    if not task_links:
        logger.info(f"No direct task links found, looking for task cards")
        task_cards = soup.select('div.card')
        
        if task_cards:
            logger.info(f"Found {len(task_cards)} task cards")
            task_links = []
            
            for card in task_cards:
                links = card.select('a')
                for link in links:
                    href = link.get('href', '')
                    if '/task/' in href:
                        task_links.append(link)
    
    # Approach 3: If still no task links, look for any links in the content area
    if not task_links:
        logger.info(f"No task cards found, looking for links in content area")
        content_area = soup.select_one('div.content')
        
        if content_area:
            task_links = []
            for link in content_area.select('a'):
                href = link.get('href', '')
                if '/task/' in href:
                    task_links.append(link)
    
    # Approach 4: If still no task links, treat this subtask as a task itself
    if not task_links:
        logger.info(f"No task links found, treating subtask as a task")
        # Create a synthetic task from the subtask
        task_url = subtask['url'].replace('/sota/', '/task/')
        if task_url != subtask['url']:  # Only if the URL actually changed
            return [{
                'name': subtask['name'],
                'url': task_url,
                'subtask': subtask['name'],
                'area': subtask['area']
            }]
    
    if not task_links:
        logger.warning(f"No task links found on subtask page: {subtask['url']}")
        return []
    
    logger.info(f"Found {len(task_links)} potential task links")
    
    # Filter out duplicates by URL
    unique_tasks = {}
    
    for link in task_links:
        task_url = urljoin(BASE_URL, link.get('href', ''))
        
        # Skip if we've already seen this URL
        if task_url in unique_tasks:
            continue
        
        # Get the task name from the link text
        task_name = link.get_text(strip=True)
        
        # If no name, use the last part of the URL
        if not task_name:
            parsed_url = urlparse(task_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if path_parts:
                task_name = path_parts[-1].replace('-', ' ').title()
        
        if task_url and task_name:
            unique_tasks[task_url] = {
                'name': task_name,
                'url': task_url,
                'subtask': subtask['name'],
                'area': subtask['area']
            }
    
    tasks = list(unique_tasks.values())
    logger.info(f"Found {len(tasks)} unique tasks for subtask {subtask['name']}")
    return tasks

def extract_datasets_from_task_page(task, html_content):
    """
    Extract datasets from a task page.
    
    Args:
        task: Dictionary with task name and URL
        html_content: HTML content of the task page
        
    Returns:
        List of dictionaries with dataset names and URLs
    """
    logger.info(f"Extracting datasets from {task['name']} - {task['url']}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try multiple approaches to find dataset links
    
    # Approach 1: Find all dataset links with /dataset/ prefix
    dataset_links = soup.select('a[href^="/dataset/"]')
    
    # Approach 2: If no dataset links found, look for the datasets section
    if not dataset_links:
        logger.info(f"No direct dataset links found, looking for datasets section")
        datasets_heading = soup.find('h2', id='datasets')
        
        if datasets_heading:
            logger.info(f"Found datasets heading")
            # Get the next section after the datasets heading
            datasets_section = datasets_heading.find_next('div')
            
            if datasets_section:
                logger.info(f"Found datasets section")
                dataset_links = datasets_section.select('a[href^="/dataset/"]')
            else:
                # Look for any links after the datasets heading
                logger.info(f"No datasets section found, looking for links after heading")
                dataset_links = []
                current = datasets_heading.next_sibling
                
                while current and (not isinstance(current, type(datasets_heading)) or current.name != 'h2'):
                    if hasattr(current, 'select'):
                        for link in current.select('a[href^="/dataset/"]'):
                            dataset_links.append(link)
                    current = current.next_sibling
    
    # Approach 3: If still no dataset links, look for dataset cards
    if not dataset_links:
        logger.info(f"No datasets section found, looking for dataset cards")
        dataset_cards = soup.select('div.dataset-card')
        
        if dataset_cards:
            logger.info(f"Found {len(dataset_cards)} dataset cards")
            dataset_links = []
            
            for card in dataset_cards:
                links = card.select('a')
                for link in links:
                    href = link.get('href', '')
                    if '/dataset/' in href:
                        dataset_links.append(link)
    
    # Approach 4: If still no dataset links, look for any links in the content area
    if not dataset_links:
        logger.info(f"No dataset cards found, looking for links in content area")
        content_area = soup.select_one('div.content')
        
        if content_area:
            dataset_links = []
            for link in content_area.select('a'):
                href = link.get('href', '')
                if '/dataset/' in href:
                    dataset_links.append(link)
    
    if not dataset_links:
        logger.warning(f"No dataset links found on task page: {task['url']}")
        return []
    
    logger.info(f"Found {len(dataset_links)} potential dataset links")
    
    # Filter out duplicates by URL
    unique_datasets = {}
    
    for link in dataset_links:
        dataset_url = urljoin(BASE_URL, link.get('href', ''))
        
        # Skip if we've already seen this URL
        if dataset_url in unique_datasets:
            continue
        
        # Get the dataset name from the link text
        dataset_name = link.get_text(strip=True)
        
        # If no name, use the last part of the URL
        if not dataset_name:
            parsed_url = urlparse(dataset_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if path_parts:
                dataset_name = path_parts[-1].replace('-', ' ').title()
        
        if dataset_url and dataset_name:
            unique_datasets[dataset_url] = {
                'name': dataset_name,
                'url': dataset_url,
                'task': task['name'],
                'subtask': task['subtask'],
                'area': task['area']
            }
    
    datasets = list(unique_datasets.values())
    logger.info(f"Found {len(datasets)} unique datasets for task {task['name']}")
    return datasets

def save_progress(data):
    """
    Save progress to a JSON file.
    
    Args:
        data: Data to save
    """
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved progress to {PROGRESS_FILE}")

def load_progress():
    """
    Load progress from a JSON file.
    
    Returns:
        Dictionary with progress data, or empty dictionary if no progress file exists
    """
    if not os.path.exists(PROGRESS_FILE):
        return {}
    
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded progress from {PROGRESS_FILE}")
        return data
    except Exception as e:
        logger.error(f"Error loading progress: {e}")
        return {}

def main():
    """
    Main function to run the scraper.
    """
    # Create directories if they don't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger.info(f"Created directories: {OUTPUT_DIR}")
    
    # Load progress if it exists
    progress = load_progress()
    
    # Extract areas from SOTA page if not already done
    if 'areas' not in progress:
        areas = extract_areas_from_sota_page()
        progress['areas'] = areas
        save_progress(progress)
    else:
        areas = progress['areas']
    
    # Extract subtasks from each area
    if 'subtasks' not in progress:
        subtasks = []
        
        for area in areas:
            # Download the area page
            html_content = download_page(area['url'], download=False)
            
            if not html_content:
                logger.warning(f"Failed to download area page: {area['url']}")
                continue
            
            # Extract subtasks from the area page
            area_subtasks = extract_subtasks_from_area_page(area, html_content)
            subtasks.extend(area_subtasks)
            
            # Sleep to avoid overloading the server
            time.sleep(random.uniform(1, 3))
        
        progress['subtasks'] = subtasks
        save_progress(progress)
    else:
        subtasks = progress['subtasks']
    
    # Extract tasks from each subtask
    if 'tasks' not in progress:
        tasks = []
        
        for subtask in subtasks:
            # Download the subtask page
            html_content = download_page(subtask['url'], download=False)
            
            if not html_content:
                logger.warning(f"Failed to download subtask page: {subtask['url']}")
                continue
            
            # Extract tasks from the subtask page
            subtask_tasks = extract_tasks_from_subtask_page(subtask, html_content)
            tasks.extend(subtask_tasks)
            
            # Sleep to avoid overloading the server
            time.sleep(random.uniform(1, 3))
        
        progress['tasks'] = tasks
        save_progress(progress)
    else:
        tasks = progress['tasks']
    
    # Extract datasets from each task
    if 'datasets' not in progress:
        datasets = []
        
        for task in tasks:
            # Download the task page
            html_content = download_page(task['url'], download=False)
            
            if not html_content:
                logger.warning(f"Failed to download task page: {task['url']}")
                continue
            
            # Extract datasets from the task page
            task_datasets = extract_datasets_from_task_page(task, html_content)
            datasets.extend(task_datasets)
            
            # Sleep to avoid overloading the server
            time.sleep(random.uniform(1, 3))
        
        progress['datasets'] = datasets
        save_progress(progress)
    else:
        datasets = progress['datasets']
    
    # Download dataset pages
    for dataset in datasets:
        # Skip if already downloaded
        filename = get_filename_from_url(dataset['url'])
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        if os.path.exists(filepath):
            logger.info(f"Dataset already downloaded: {dataset['name']} - {dataset['url']}")
            continue
        
        # Download the dataset page
        html_content = download_page(dataset['url'], download=True)
        
        if not html_content:
            logger.warning(f"Failed to download dataset page: {dataset['url']}")
            continue
        
        # Sleep to avoid overloading the server
        time.sleep(random.uniform(1, 3))
    
    logger.info("Scraping completed successfully")

if __name__ == '__main__':
    main()
