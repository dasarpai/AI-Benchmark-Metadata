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

def create_directories():
    """Create the output directory if it doesn't exist."""
    try:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            logger.info(f"Created directories: {OUTPUT_DIR}")
        return True
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

def load_progress():
    """Load the progress from the progress file."""
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
    """Save the progress to the progress file."""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
        logger.info(f"Saved progress to {PROGRESS_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving progress: {e}")
        return False

def download_page(url):
    """Download a page from the given URL."""
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
    """Extract areas from the SOTA page."""
    logger.info(f"Extracting areas from {SOTA_URL}")
    
    # Download the SOTA page
    html_content = download_page(SOTA_URL)
    if not html_content:
        logger.error(f"Failed to download SOTA page: {SOTA_URL}")
        # Fallback to a list of predefined areas
        logger.info("Using fallback list of areas")
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
    """Extract subtasks from an area page."""
    if not html_content:
        logger.error(f"No HTML content provided for area: {area['name']}")
        return []
    
    logger.info(f"Extracting subtasks from area: {area['name']}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the sota-all-tasks div
    sota_all_tasks = soup.find('div', class_='sota-all-tasks')
    
    subtask_links = []
    
    if sota_all_tasks:
        # Find all task links in the sota-all-tasks div
        subtask_links = sota_all_tasks.select('a[href^="/sota/"]')
    
    if not subtask_links:
        logger.warning(f"Could not find subtask links in sota-all-tasks div for area: {area['name']}, looking for task links directly")
        
        # Look for task links directly
        subtask_links = soup.select('a[href^="/task/"]')
        
        if not subtask_links:
            logger.warning(f"Could not find task links for area: {area['name']}, looking for sota links")
            
            # Look for sota links
            subtask_links = soup.select('a[href^="/sota/"]')
    
    # Extract subtask names and URLs
    unique_subtasks = {}
    
    for link in subtask_links:
        subtask_url = urljoin(BASE_URL, link.get('href', ''))
        
        # Get the text content of the link, making sure to clean it properly
        subtask_name = link.get_text(strip=True)
        
        # If the text is empty or contains only whitespace, extract from URL
        if not subtask_name:
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
    
    # If no subtasks found, create a synthetic one from the area
    if not subtasks:
        logger.warning(f"No subtasks found for area: {area['name']}, creating synthetic subtask")
        
        subtasks = [{
            'name': area['name'],
            'url': area['url'],
            'area': area['name'],
            'is_synthetic': True
        }]
    
    logger.info(f"Found {len(subtasks)} unique subtasks for area: {area['name']}")
    return subtasks

def extract_tasks_from_subtask_page(subtask, html_content):
    """Extract tasks from a subtask page."""
    # If this is a synthetic subtask, treat it as a task
    if subtask.get('is_synthetic', False) or '/task/' in subtask['url']:
        logger.info(f"Using subtask as task: {subtask['name']}")
        
        # Create a task from the subtask
        task = {
            'name': subtask['name'],
            'url': subtask['url'],
            'area': subtask['area'],
            'subtask': subtask['name'],
            'is_synthetic': True
        }
        
        return [task]
    
    if not html_content:
        logger.error(f"No HTML content provided for subtask: {subtask['name']}")
        return []
    
    logger.info(f"Extracting tasks from subtask: {subtask['name']}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all task cards
    task_cards = soup.find_all('div', class_='card-content')
    
    task_links = []
    
    if task_cards:
        # Find all task links in the task cards
        for card in task_cards:
            links = card.select('a[href^="/task/"]')
            task_links.extend(links)
    
    if not task_links:
        logger.warning(f"Could not find task links in cards for subtask: {subtask['name']}, looking for task links directly")
        
        # Look for task links directly
        task_links = soup.select('a[href^="/task/"]')
    
    # Extract task names and URLs
    unique_tasks = {}
    
    for link in task_links:
        task_url = urljoin(BASE_URL, link.get('href', ''))
        
        # Get the text content of the link, making sure to clean it properly
        task_name = link.get_text(strip=True)
        
        # If the text is empty or contains only whitespace, extract from URL
        if not task_name:
            parsed_url = urlparse(task_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) > 1:
                task_name = path_parts[-1].replace('-', ' ').title()
        
        # Clean the task name to remove any strange characters or formatting
        task_name = re.sub(r'\s+', ' ', task_name).strip()
        
        if task_url and task_name:
            unique_tasks[task_url] = {
                'name': task_name,
                'url': task_url,
                'area': subtask['area'],
                'subtask': subtask['name']
            }
    
    tasks = list(unique_tasks.values())
    
    # If no tasks found, create a synthetic one from the subtask
    if not tasks:
        logger.warning(f"No tasks found for subtask: {subtask['name']}, creating synthetic task")
        
        tasks = [{
            'name': subtask['name'],
            'url': subtask['url'],
            'area': subtask['area'],
            'subtask': subtask['name'],
            'is_synthetic': True
        }]
    
    logger.info(f"Found {len(tasks)} unique tasks for subtask: {subtask['name']}")
    return tasks

def extract_datasets_from_task_page(task, html_content):
    """Extract datasets from a task page."""
    if not html_content:
        logger.error(f"No HTML content provided for task: {task['name']}")
        return []
    
    logger.info(f"Extracting datasets from task: {task['name']}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the datasets section
    datasets_heading = soup.find('h2', string=lambda text: text and 'Datasets' in text)
    
    dataset_links = []
    
    if datasets_heading:
        # Find the next div after the datasets heading
        next_div = datasets_heading.find_next('div')
        
        if next_div:
            # Find all dataset links in the div
            dataset_links = next_div.select('a[href^="/dataset/"]')
    
    if not dataset_links:
        logger.warning(f"Could not find dataset links after datasets heading for task: {task['name']}, looking for dataset links directly")
        
        # Look for dataset links directly
        dataset_links = soup.select('a[href^="/dataset/"]')
    
    # Extract dataset names and URLs
    unique_datasets = {}
    
    for link in dataset_links:
        dataset_url = urljoin(BASE_URL, link.get('href', ''))
        
        # Get the text content of the link, making sure to clean it properly
        dataset_name = link.get_text(strip=True)
        
        # If the text is empty or contains only whitespace, extract from URL
        if not dataset_name:
            parsed_url = urlparse(dataset_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) > 1:
                dataset_name = path_parts[-1].replace('-', ' ').title()
        
        # Clean the dataset name to remove any strange characters or formatting
        dataset_name = re.sub(r'\s+', ' ', dataset_name).strip()
        
        if dataset_url and dataset_name:
            unique_datasets[dataset_url] = {
                'name': dataset_name,
                'url': dataset_url,
                'area': task['area'],
                'subtask': task['subtask'],
                'task': task['name']
            }
    
    datasets = list(unique_datasets.values())
    
    # If no datasets found, create a synthetic one from the task
    if not datasets:
        logger.warning(f"No datasets found for task: {task['name']}, creating synthetic dataset")
        
        datasets = [{
            'name': f"{task['name']} Dataset",
            'url': task['url'],
            'area': task['area'],
            'subtask': task['subtask'],
            'task': task['name'],
            'is_synthetic': True
        }]
    
    logger.info(f"Found {len(datasets)} unique datasets for task: {task['name']}")
    return datasets

def clean_name_for_directory(name):
    """Clean a name for use as a directory name."""
    # Replace non-alphanumeric characters with underscores
    clean_name = re.sub(r'[^\w\-\.]', '_', name)
    
    # Limit length to avoid excessively long filenames
    clean_name = clean_name[:50]
    
    return clean_name

def save_dataset_page(dataset):
    """Save the dataset page to a file."""
    # Create valid directory names
    area_name = clean_name_for_directory(dataset['area'])
    task_name = clean_name_for_directory(dataset['task'])
    dataset_name = clean_name_for_directory(dataset['name'])
    
    # Create directory structure - directly use area/task without subtask
    dir_path = os.path.join(OUTPUT_DIR, area_name, task_name)
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

def scrape_benchmarks():
    """Scrape benchmarks from Papers With Code."""
    # Create directories
    if not create_directories():
        logger.error("Failed to create directories")
        return
    
    # Load progress
    progress = load_progress()
    
    # Extract areas
    areas = extract_areas_from_sota_page()
    
    # Process each area
    for area in areas:
        # Skip if already processed
        if area['url'] in progress.get('processed_areas', []):
            logger.info(f"Skipping already processed area: {area['name']}")
            continue
        
        # Download area page
        html_content = download_page(area['url'])
        if not html_content:
            logger.error(f"Failed to download area page: {area['url']}")
            continue
        
        # Extract subtasks
        subtasks = extract_subtasks_from_area_page(area, html_content)
        
        # Process each subtask
        for subtask in subtasks:
            # Skip if already processed
            if subtask['url'] in progress.get('processed_subtasks', []):
                logger.info(f"Skipping already processed subtask: {subtask['name']}")
                continue
            
            # Download subtask page
            html_content = download_page(subtask['url'])
            
            # Extract tasks
            tasks = extract_tasks_from_subtask_page(subtask, html_content)
            
            # Process each task
            for task in tasks:
                # Skip if already processed
                if task['url'] in progress.get('processed_tasks', []):
                    logger.info(f"Skipping already processed task: {task['name']}")
                    continue
                
                # Download task page
                html_content = download_page(task['url'])
                
                # Extract datasets
                datasets = extract_datasets_from_task_page(task, html_content)
                
                # Process each dataset
                for dataset in datasets:
                    # Skip if already processed
                    if dataset['url'] in progress.get('processed_datasets', []):
                        logger.info(f"Skipping already processed dataset: {dataset['name']}")
                        continue
                    
                    # Save dataset page
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
        scrape_benchmarks()
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
