#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = 'https://paperswithcode.com'
SOTA_URL = 'https://paperswithcode.com/sota'
OUTPUT_DIR = 'paperswithcode'
PROGRESS_FILE = 'pwc_scraper_progress.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    logger.info(f"Created directories: {OUTPUT_DIR}")

def load_progress():
    """
    Load the progress from the progress file.
    
    Returns:
        Dictionary with progress information
    """
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
            logger.info(f"Loaded progress from {PROGRESS_FILE}")
            
            # Ensure all required keys exist
            if 'processed_areas' not in progress:
                progress['processed_areas'] = []
            if 'processed_subtasks' not in progress:
                progress['processed_subtasks'] = []
            if 'processed_tasks' not in progress:
                progress['processed_tasks'] = []
            if 'processed_datasets' not in progress:
                progress['processed_datasets'] = []
            if 'downloaded_datasets' not in progress:
                progress['downloaded_datasets'] = []
                
            return progress
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
    
    # Initialize progress
    progress = {
        'processed_areas': [],
        'processed_subtasks': [],
        'processed_tasks': [],
        'processed_datasets': [],
        'downloaded_datasets': []
    }
    
    return progress

def save_progress(progress):
    """
    Save progress to the progress file.
    """
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=4)

def download_page(url):
    """
    Download a page from the given URL.
    
    Args:
        url: URL to download
        
    Returns:
        HTML content of the page
    """
    try:
        logger.info(f"Downloading {url}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        # Check if the page was found
        if response.status_code == 404:
            logger.warning(f"Page not found: {url}")
            return None
        
        response.raise_for_status()
        return response.text
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
    
    # Download the SOTA page
    html_content = download_page(SOTA_URL)
    if not html_content:
        logger.error(f"Failed to download SOTA page: {SOTA_URL}")
        # Fallback to a list of predefined areas
        logger.info("Using fallback list of areas")
        return [
            # {'name': 'Computer Vision', 'url': 'https://paperswithcode.com/area/computer-vision'},
            {'name': 'Natural Language Processing', 'url': 'https://paperswithcode.com/area/natural-language-processing'},
            {'name': 'Medical', 'url': 'https://paperswithcode.com/area/medical'},
            {'name': 'Methodology', 'url': 'https://paperswithcode.com/area/methodology'},
            {'name': 'Graphs', 'url': 'https://paperswithcode.com/area/graphs'},
            {'name': 'Audio', 'url': 'https://paperswithcode.com/area/audio'},
            {'name': 'Reinforcement Learning', 'url': 'https://paperswithcode.com/area/reinforcement-learning'},
            {'name': 'Time Series', 'url': 'https://paperswithcode.com/area/time-series'},
            {'name': 'Robotics', 'url': 'https://paperswithcode.com/area/robotics'},
            {'name': 'Playing Games', 'url': 'https://paperswithcode.com/area/playing-games'},
            {'name': 'Reasoning', 'url': 'https://paperswithcode.com/area/reasoning'},
            {'name': 'Adversarial', 'url': 'https://paperswithcode.com/area/adversarial'},
            {'name': 'Speech', 'url': 'https://paperswithcode.com/area/speech'},
            {'name': 'Generative Models', 'url': 'https://paperswithcode.com/area/generative-models'},
            {'name': 'Multimodal', 'url': 'https://paperswithcode.com/area/multimodal'},
            {'name': 'Recommender Systems', 'url': 'https://paperswithcode.com/area/recommender-systems'}
        ]
    else:
        html_content = html_content[1:]
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all area sections with h4 headings
    area_sections = soup.find_all('h4', class_='task-section-title')
    
    if not area_sections:
        logger.warning("Could not find area sections with h4 headings, looking for area links directly")
        
        # Look for area links directly
        area_links = soup.select('a[href^="/area/"]')
        
        if not area_links:
            logger.warning("Could not find area links, using fallback list")
            # Fallback to a list of predefined areas
            return [
                {'name': 'Computer Vision', 'url': 'https://paperswithcode.com/area/computer-vision'},
                {'name': 'Natural Language Processing', 'url': 'https://paperswithcode.com/area/natural-language-processing'},
                {'name': 'Medical', 'url': 'https://paperswithcode.com/area/medical'},
                {'name': 'Methodology', 'url': 'https://paperswithcode.com/area/methodology'},
                {'name': 'Graphs', 'url': 'https://paperswithcode.com/area/graphs'},
                {'name': 'Audio', 'url': 'https://paperswithcode.com/area/audio'},
                {'name': 'Reinforcement Learning', 'url': 'https://paperswithcode.com/area/reinforcement-learning'},
                {'name': 'Time Series', 'url': 'https://paperswithcode.com/area/time-series'},
                {'name': 'Robotics', 'url': 'https://paperswithcode.com/area/robotics'},
                {'name': 'Playing Games', 'url': 'https://paperswithcode.com/area/playing-games'},
                {'name': 'Reasoning', 'url': 'https://paperswithcode.com/area/reasoning'},
                {'name': 'Adversarial', 'url': 'https://paperswithcode.com/area/adversarial'},
                {'name': 'Speech', 'url': 'https://paperswithcode.com/area/speech'},
                {'name': 'Generative Models', 'url': 'https://paperswithcode.com/area/generative-models'},
                {'name': 'Multimodal', 'url': 'https://paperswithcode.com/area/multimodal'},
                {'name': 'Recommender Systems', 'url': 'https://paperswithcode.com/area/recommender-systems'}
            ]
    
    # Extract area names and URLs
    unique_areas = {}
    
    for section in area_sections:
        # Get the area name from the h4 heading
        area_name = section.get_text(strip=True)
        
        # Find the parent div that contains the links
        parent_div = section.find_parent('div')
        
        if parent_div:
            # Find all area links in the parent div
            area_links = parent_div.select('a[href^="/area/"]')
            
            if area_links:
                # Use the first link as the area URL
                area_url = urljoin(BASE_URL, area_links[0].get('href', ''))
                
                # Clean the area name to remove any strange characters or formatting
                area_name = re.sub(r'\s+', ' ', area_name).strip()
                
                if area_url and area_name:
                    unique_areas[area_url] = {
                        'name': area_name,
                        'url': area_url
                    }
    
    # If no areas found using h4 headings, try direct links
    if not unique_areas:
        logger.warning("No areas found using h4 headings, trying direct links")
        
        # Find all area links directly
        area_links = soup.select('a[href^="/area/"]')
        
        for link in area_links:
            area_url = urljoin(BASE_URL, link.get('href', ''))
            
            # Get the text content of the link, making sure to clean it properly
            area_name = link.get_text(strip=True)
            
            # If the text is empty or contains only whitespace, extract from URL
            if not area_name:
                parsed_url = urlparse(area_url)
                path_parts = parsed_url.path.strip('/').split('/')
                if len(path_parts) > 1:
                    area_name = path_parts[-1].replace('-', ' ').title()
            
            # Clean the area name to remove any strange characters or formatting
            area_name = re.sub(r'\s+', ' ', area_name).strip()
            
            if area_url and area_name:
                unique_areas[area_url] = {
                    'name': area_name,
                    'url': area_url
                }
    
    areas = list(unique_areas.values())
    
    # If still no areas found, use fallback list
    if not areas:
        logger.warning("No areas found, using fallback list")
        return [
            {'name': 'Computer Vision', 'url': 'https://paperswithcode.com/area/computer-vision'},
            {'name': 'Natural Language Processing', 'url': 'https://paperswithcode.com/area/natural-language-processing'},
            {'name': 'Medical', 'url': 'https://paperswithcode.com/area/medical'},
            {'name': 'Methodology', 'url': 'https://paperswithcode.com/area/methodology'},
            {'name': 'Graphs', 'url': 'https://paperswithcode.com/area/graphs'},
            {'name': 'Audio', 'url': 'https://paperswithcode.com/area/audio'},
            {'name': 'Reinforcement Learning', 'url': 'https://paperswithcode.com/area/reinforcement-learning'},
            {'name': 'Time Series', 'url': 'https://paperswithcode.com/area/time-series'},
            {'name': 'Robotics', 'url': 'https://paperswithcode.com/area/robotics'},
            {'name': 'Playing Games', 'url': 'https://paperswithcode.com/area/playing-games'},
            {'name': 'Reasoning', 'url': 'https://paperswithcode.com/area/reasoning'},
            {'name': 'Adversarial', 'url': 'https://paperswithcode.com/area/adversarial'},
            {'name': 'Speech', 'url': 'https://paperswithcode.com/area/speech'},
            {'name': 'Generative Models', 'url': 'https://paperswithcode.com/area/generative-models'},
            {'name': 'Multimodal', 'url': 'https://paperswithcode.com/area/multimodal'},
            {'name': 'Recommender Systems', 'url': 'https://paperswithcode.com/area/recommender-systems'}
        ]
    
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
    subtask_links = []
    
    # Approach 1: Find the sota-all-tasks div
    sota_all_tasks = soup.find('div', class_='sota-all-tasks')
    if sota_all_tasks:
        # Find all subtask links in the sota-all-tasks div
        # For subtasks, we need to look for links to task pages, not sota pages
        subtask_links = sota_all_tasks.select('a[href^="/task/"]')
        logger.info(f"Found {len(subtask_links)} subtask links in sota-all-tasks div")
    
    # Approach 2: If no subtask links found, look for all task links on the page
    if not subtask_links:
        logger.info("Looking for all task links on the page")
        subtask_links = soup.select('a[href^="/task/"]')
        logger.info(f"Found {len(subtask_links)} subtask links on the page")
    
    # Approach 3: If still no subtask links, look for links in cards
    if not subtask_links:
        logger.info("Looking for links in cards")
        cards = soup.select('div.card')
        
        if cards:
            logger.info(f"Found {len(cards)} cards")
            for card in cards:
                links = card.select('a')
                for link in links:
                    href = link.get('href', '')
                    if href.startswith('/task/'):
                        subtask_links.append(link)
    
    if not subtask_links:
        logger.warning(f"No subtask links found on area page: {area['url']}")
        return []
    
    logger.info(f"Found {len(subtask_links)} potential subtask links")
    
    # Filter out duplicates by URL
    unique_subtasks = {}
    
    for link in subtask_links:
        subtask_url = urljoin(BASE_URL, link.get('href', ''))
        
        # Get the text content of the link, making sure to clean it properly
        subtask_name = link.get_text(strip=True)
        
        # If the text is empty or contains only whitespace, extract from URL
        if not subtask_name:
            # Extract name from URL if text is empty
            parsed_url = urlparse(subtask_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) > 1:
                subtask_name = path_parts[-1].replace('-', ' ').title()
        
        # Clean the subtask name to remove any strange characters or formatting
        subtask_name = re.sub(r'\s+', ' ', subtask_name).strip()
        
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
    
    # Since we're now using task URLs directly for subtasks, the subtask URL is already a task URL
    # We can just return the subtask as a task
    return [{
        'name': subtask['name'],
        'url': subtask['url'],
        'subtask': subtask['name'],
        'area': subtask['area']
    }]

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
    
    # If the HTML content is None (page not found), try to create a synthetic dataset
    if html_content is None:
        logger.warning(f"No HTML content for task page: {task['url']}")
        
        # Try to extract a dataset name from the task name
        dataset_name = f"{task['name']} Dataset"
        dataset_url = task['url'].replace('/task/', '/dataset/')
        
        if dataset_url != task['url']:  # Only if the URL actually changed
            logger.info(f"Created synthetic dataset: {dataset_name} - {dataset_url}")
            return [{
                'name': dataset_name,
                'url': dataset_url,
                'task': task['name'],
                'subtask': task['subtask'],
                'area': task['area'],
                'is_synthetic': True
            }]
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try multiple approaches to find dataset links
    
    # Approach 1: Find the datasets heading and extract links after it
    datasets_heading = soup.find('h2', id='datasets')
    
    if datasets_heading:
        logger.info(f"Found datasets heading")
        
        # Find dataset links after the datasets heading
        datasets = []
        current = datasets_heading.next_sibling
        
        # Look through elements after the datasets heading until we find another heading
        while current and not (hasattr(current, 'name') and current.name == 'h2'):
            if hasattr(current, 'select'):
                dataset_links = current.select('a[href^="/dataset/"]')
                
                for link in dataset_links:
                    dataset_url = urljoin(BASE_URL, link.get('href', ''))
                    dataset_name = link.get_text(strip=True)
                    
                    if not dataset_name:
                        # Extract name from URL if text is empty
                        parsed_url = urlparse(dataset_url)
                        path_parts = parsed_url.path.strip('/').split('/')
                        if len(path_parts) > 1:
                            dataset_name = path_parts[-1].replace('-', ' ').title()
                    
                    if dataset_url and dataset_name:
                        datasets.append({
                            'name': dataset_name,
                            'url': dataset_url,
                            'task': task['name'],
                            'subtask': task['subtask'],
                            'area': task['area']
                        })
            
            current = current.next_sibling
        
        if datasets:
            logger.info(f"Found {len(datasets)} datasets after heading for task {task['name']}")
            return datasets
    
    # Approach 2: Find all dataset links directly
    dataset_links = soup.select('a[href^="/dataset/"]')
    
    if dataset_links:
        logger.info(f"Found {len(dataset_links)} direct dataset links")
        
        # Extract dataset names and URLs
        datasets = []
        for link in dataset_links:
            dataset_url = urljoin(BASE_URL, link.get('href', ''))
            dataset_name = link.get_text(strip=True)
            
            if not dataset_name:
                # Extract name from URL if text is empty
                parsed_url = urlparse(dataset_url)
                path_parts = parsed_url.path.strip('/').split('/')
                if len(path_parts) > 1:
                    dataset_name = path_parts[-1].replace('-', ' ').title()
            
            if dataset_url and dataset_name:
                datasets.append({
                    'name': dataset_name,
                    'url': dataset_url,
                    'task': task['name'],
                    'subtask': task['subtask'],
                    'area': task['area']
                })
        
        if datasets:
            logger.info(f"Found {len(datasets)} datasets from direct links for task {task['name']}")
            return datasets
    
    # Approach 3: Look for dataset cards
    dataset_cards = soup.select('div.dataset-card')
    
    if dataset_cards:
        logger.info(f"Found {len(dataset_cards)} dataset cards")
        
        # Extract dataset links from cards
        datasets = []
        for card in dataset_cards:
            links = card.select('a')
            
            for link in links:
                href = link.get('href', '')
                if '/dataset/' in href:
                    dataset_url = urljoin(BASE_URL, href)
                    dataset_name = link.get_text(strip=True)
                    
                    if not dataset_name:
                        # Extract name from URL if text is empty
                        parsed_url = urlparse(dataset_url)
                        path_parts = parsed_url.path.strip('/').split('/')
                        if len(path_parts) > 1:
                            dataset_name = path_parts[-1].replace('-', ' ').title()
                    
                    if dataset_url and dataset_name:
                        datasets.append({
                            'name': dataset_name,
                            'url': dataset_url,
                            'task': task['name'],
                            'subtask': task['subtask'],
                            'area': task['area']
                        })
        
        if datasets:
            logger.info(f"Found {len(datasets)} datasets from cards for task {task['name']}")
            return datasets
    
    # Approach 4: Try to create a synthetic dataset from the task name
    logger.info(f"No datasets found, creating synthetic dataset from task name")
    dataset_name = f"{task['name']} Dataset"
    dataset_url = task['url'].replace('/task/', '/dataset/')
    
    if dataset_url != task['url']:  # Only if the URL actually changed
        logger.info(f"Created synthetic dataset: {dataset_name} - {dataset_url}")
        return [{
            'name': dataset_name,
            'url': dataset_url,
            'task': task['name'],
            'subtask': task['subtask'],
            'area': task['area'],
            'is_synthetic': True
        }]
    
    logger.warning(f"No datasets found for task {task['name']}")
    return []

def save_dataset_page(dataset):
    """
    Save the dataset page to a file.
    
    Args:
        dataset: Dictionary with dataset name and URL
        
    Returns:
        True if successful, False otherwise
    """
    # Create a valid filename from the dataset name
    dataset_name = re.sub(r'[^\w\-\.]', '_', dataset['name'])
    dataset_name = dataset_name[:50]  # Limit length to avoid excessively long filenames
    
    # Create directory structure
    area_name = re.sub(r'[^\w\-\.]', '_', dataset['area'])
    area_name = area_name[:30]  # Limit length
    
    subtask_name = re.sub(r'[^\w\-\.]', '_', dataset['subtask'])
    subtask_name = subtask_name[:30]  # Limit length
    
    task_name = re.sub(r'[^\w\-\.]', '_', dataset['task'])
    task_name = task_name[:30]  # Limit length
    
    # Avoid duplicate folder names by checking if subtask and task are the same
    if subtask_name == task_name:
        dir_path = os.path.join(OUTPUT_DIR, area_name, task_name)
    else:
        dir_path = os.path.join(OUTPUT_DIR, area_name, subtask_name, task_name)
    
    os.makedirs(dir_path, exist_ok=True)
    
    # Create the file path
    file_path = os.path.join(dir_path, f"{dataset_name}.html")
    
    # Check if the file already exists
    if os.path.exists(file_path):
        logger.info(f"Dataset page already exists: {file_path}")
        return True
    
    # If this is a synthetic dataset, create a placeholder HTML file with metadata
    if dataset.get('is_synthetic', False):
        logger.info(f"Creating placeholder HTML for synthetic dataset: {dataset['name']}")
        
        # Create a simple HTML file with dataset metadata
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{dataset['name']}</title>
            <meta name="dataset" content="{dataset['name']}">
            <meta name="task" content="{dataset['task']}">
            <meta name="subtask" content="{dataset['subtask']}">
            <meta name="area" content="{dataset['area']}">
            <meta name="url" content="{dataset['url']}">
            <meta name="synthetic" content="true">
        </head>
        <body>
            <h1>{dataset['name']}</h1>
            <p>This is a synthetic dataset created by the Papers With Code scraper.</p>
            <p>Task: {dataset['task']}</p>
            <p>Subtask: {dataset['subtask']}</p>
            <p>Area: {dataset['area']}</p>
            <p>URL: <a href="{dataset['url']}">{dataset['url']}</a></p>
        </body>
        </html>
        """
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Saved synthetic dataset page: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving synthetic dataset page: {e}")
            return False
    
    # Download the dataset page
    html_content = download_page(dataset['url'])
    if not html_content:
        logger.error(f"Failed to download dataset page: {dataset['url']}")
        return False
    
    # Save the dataset page
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Saved dataset page: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving dataset page: {e}")
        return False

def scrape_paperswithcode():
    """
    Scrape the Papers With Code website.
    """
    # Load progress
    progress = load_progress()
    
    # Extract areas from the SOTA page
    areas = extract_areas_from_sota_page()
    
    # Process each area
    for area in areas:
        # Skip if already processed
        if area['url'] in progress.get('processed_areas', []):
            logger.info(f"Skipping already processed area: {area['name']}")
            continue
        
        # Download the area page
        html_content = download_page(area['url'])
        if not html_content:
            logger.error(f"Failed to download area page: {area['url']}")
            continue
        
        # Extract subtasks from the area page
        subtasks = extract_subtasks_from_area_page(area, html_content)
        
        # Process each subtask
        for subtask in subtasks:
            # Skip if already processed
            if subtask['url'] in progress.get('processed_subtasks', []):
                logger.info(f"Skipping already processed subtask: {subtask['name']}")
                continue
            
            # Download the subtask page
            html_content = download_page(subtask['url'])
            if not html_content:
                logger.error(f"Failed to download subtask page: {subtask['url']}")
                continue
            
            # Extract tasks from the subtask page
            tasks = extract_tasks_from_subtask_page(subtask, html_content)
            
            # Process each task
            for task in tasks:
                # Skip if already processed
                if task['url'] in progress.get('processed_tasks', []):
                    logger.info(f"Skipping already processed task: {task['name']}")
                    continue
                
                # Download the task page
                html_content = download_page(task['url'])
                if not html_content:
                    logger.error(f"Failed to download task page: {task['url']}")
                    continue
                
                # Extract datasets from the task page
                datasets = extract_datasets_from_task_page(task, html_content)
                
                # Process each dataset
                for dataset in datasets:
                    # Skip if already processed
                    if dataset['url'] in progress.get('processed_datasets', []):
                        logger.info(f"Skipping already processed dataset: {dataset['name']}")
                        continue
                    
                    # Save the dataset page
                    if save_dataset_page(dataset):
                        # Update progress
                        if 'downloaded_datasets' not in progress:
                            progress['downloaded_datasets'] = []
                        progress['downloaded_datasets'].append(dataset['url'])
                        save_progress(progress)
                    
                    # Add to processed datasets
                    if 'processed_datasets' not in progress:
                        progress['processed_datasets'] = []
                    progress['processed_datasets'].append(dataset['url'])
                    save_progress(progress)
                    
                    # Sleep to avoid overloading the server
                    time.sleep(random.uniform(1, 3))
                
                # Add to processed tasks
                if 'processed_tasks' not in progress:
                    progress['processed_tasks'] = []
                progress['processed_tasks'].append(task['url'])
                save_progress(progress)
            
            # Add to processed subtasks
            if 'processed_subtasks' not in progress:
                progress['processed_subtasks'] = []
            progress['processed_subtasks'].append(subtask['url'])
            save_progress(progress)
        
        # Add to processed areas
        if 'processed_areas' not in progress:
            progress['processed_areas'] = []
        progress['processed_areas'].append(area['url'])
        save_progress(progress)
    
    logger.info("Finished scraping benchmarks")

if __name__ == "__main__":
    try:
        scrape_paperswithcode()
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
