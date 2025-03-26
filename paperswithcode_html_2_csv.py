#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Papers With Code HTML to CSV Converter

This script processes the HTML files downloaded by paperswithcode_scraper.py
and extracts relevant dataset metadata into a CSV file.

Usage:
    python paperswithcode_html_2_csv.py

The script will read all HTML files in the 'paperswithcode/consolidated' directory
and generate a CSV file with dataset metadata.
"""

import os
import re
import csv
import glob
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Tuple
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
HTML_DIR = os.path.join("paperswithcode", "consolidated")
CSV_DIR = "csv"
OUTPUT_CSV = os.path.join(CSV_DIR, "paperswithcode_datasets.csv")
PROGRESS_FILE = "pwc_extraction_progress.json"

def setup_csv_file(csv_path: str) -> None:
    """
    Create a CSV file with headers.
    
    Args:
        csv_path: Path to the CSV file
    """
    # Ensure CSV directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    headers = [
        "dataset_id",
        "dataset_name",
        "description",
        "homepage_url",
        "license",
        "modalities",
        "languages",
        "year_published",
        "paper_title",
        "paper_url",
        "dataset_size",
        "dataset_splits",
        "num_classes",
        "associated_tasks",
        "benchmark_urls",
        "pwc_url",
        "area",
        "subtask",
        "task"
    ]
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
    
    logger.info(f"Created CSV file with headers: {csv_path}")

def is_dataset_page(html_content: str) -> bool:
    """
    Determine if the HTML content is from a dataset page.
    
    Args:
        html_content: HTML content to check
        
    Returns:
        True if the page is a dataset page, False otherwise
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for dataset-specific elements
    # 1. Title should contain "Dataset"
    title = soup.title.string if soup.title else ""
    has_dataset_in_title = "dataset" in title.lower() if title else False
    
    # 2. Check for dataset header
    dataset_header = soup.select_one('div.dataset-header')
    has_dataset_header = dataset_header is not None
    
    # 3. Check for dataset description
    dataset_description = soup.select_one('div.dataset-description')
    has_dataset_description = dataset_description is not None
    
    # A page is considered a dataset page if it has at least 2 of these elements
    dataset_indicators = [has_dataset_in_title, has_dataset_header, has_dataset_description]
    return sum(dataset_indicators) >= 1  # More lenient check

def extract_dataset_name(soup: BeautifulSoup) -> str:
    """
    Extract the dataset name from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Dataset name
    """
    # Try to get from the title
    title = soup.title.string if soup.title else ""
    
    if title:
        # Extract the part before " | Papers With Code"
        match = re.search(r'^(.*?)(?:\s+\|\s+Papers With Code)?$', title)
        if match:
            return match.group(1).strip()
    
    # Try to get from the main heading
    heading = soup.select_one('h1.paper-title')
    if heading:
        return heading.get_text(strip=True)
    
    return "Unknown Dataset"

def extract_dataset_description(soup: BeautifulSoup) -> str:
    """
    Extract the dataset description from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Dataset description
    """
    # Try to find the description in the meta tags
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return meta_desc.get('content').strip()
    
    # Try to find the description in the main content
    description_div = soup.select_one('div.dataset-description')
    if description_div:
        return description_div.get_text(strip=True)
    
    # Try to find any paragraph that might contain a description
    paragraphs = soup.select('div.paper-abstract p')
    if paragraphs:
        return paragraphs[0].get_text(strip=True)
    
    return ""

def extract_homepage_url(soup: BeautifulSoup) -> str:
    """
    Extract the dataset homepage URL from the dataset page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Dataset homepage URL
    """
    # First priority: Look for the Homepage button
    homepage_button = soup.select_one('a.btn.btn-primary-outline.dataset-homepage')
    if homepage_button and homepage_button.get('href'):
        href = homepage_button.get('href').strip()
        logger.info(f"Found dataset homepage URL: {href}")
        return href
    
    # Second priority: Look for dataset source link - this is the direct link to the dataset repository
    dataset_source = soup.select_one('div.dataset-source a')
    if dataset_source and dataset_source.get('href'):
        href = dataset_source.get('href').strip()
        # Ensure it's not a paper URL or an internal PWC link
        if not href.startswith('/paper/') and not href.startswith('https://paperswithcode.com'):
            logger.info(f"Found dataset source URL: {href}")
            return href
    
    # Look for external links that might be dataset repositories
    external_links = soup.select('a.badge-external')
    for link in external_links:
        href = link.get('href', '').strip()
        # Skip paper links and PWC internal links
        if href and not href.startswith('/paper/') and not href.startswith('https://paperswithcode.com') and not 'arxiv.org' in href:
            # Prioritize GitHub, Hugging Face, or other common dataset repositories
            if any(repo in href.lower() for repo in ['github.com', 'huggingface.co', 'kaggle.com', 'tensorflow.org/datasets', 'pytorch.org']):
                logger.info(f"Found dataset external URL (repository): {href}")
                return href
    
    # Try again with all external links if we haven't found a good one yet
    for link in external_links:
        href = link.get('href', '').strip()
        if href and not href.startswith('/paper/') and not href.startswith('https://paperswithcode.com') and not 'arxiv.org' in href:
            logger.info(f"Found dataset external URL: {href}")
            return href
    
    # If we still haven't found a source URL, look for any link in the dataset description
    description = soup.select_one('div.markdown-body')
    if description:
        links = description.select('a')
        for link in links:
            href = link.get('href', '').strip()
            if href and not href.startswith('/paper/') and not href.startswith('https://paperswithcode.com') and not 'arxiv.org' in href:
                logger.info(f"Found dataset URL in description: {href}")
                return href
    
    # Also check for links in the description content
    description_content = soup.select_one('div.description-content')
    if description_content:
        links = description_content.select('a')
        for link in links:
            href = link.get('href', '').strip()
            # Skip internal PWC links and paper links
            if href and not href.startswith('/paper/') and not href.startswith('https://paperswithcode.com') and not 'arxiv.org' in href:
                logger.info(f"Found dataset URL in description content: {href}")
                return href
    
    # Default to the dataset image as a last resort (not ideal but keeps the format consistent)
    dataset_image = soup.select_one('img.dataset-image')
    if dataset_image and dataset_image.get('src'):
        return dataset_image.get('src').strip()
    
    logger.warning("No dataset homepage URL found")
    return ""

def extract_license(soup: BeautifulSoup) -> str:
    """
    Extract the license information from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        License information
    """
    # Find the license section
    license_section = soup.find('div', class_='license')
    
    if license_section:
        # Get the license text
        license_text = license_section.get_text(strip=True)
        
        # Remove the "License" heading
        license_text = re.sub(r'^License', '', license_text).strip()
        
        return license_text
    
    return ""

def extract_modalities(soup: BeautifulSoup) -> str:
    """
    Extract the modalities from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Comma-separated list of modalities
    """
    # Find the modalities section by looking for the h4 header first
    modalities_header = soup.find('h4', string='Modalities')
    
    if modalities_header:
        # Get the parent div that contains the modalities
        modalities_section = modalities_header.parent
        
        if modalities_section:
            # Get all modality links
            modality_links = modalities_section.select('a')
            
            # Extract modality names
            modalities = [link.get_text(strip=True) for link in modality_links]
            
            if modalities:
                return ', '.join(modalities)
    
    # Try alternate approach - look for modality badges
    modality_badges = soup.select('span.badge-modality')
    if modality_badges:
        modalities = [badge.get_text(strip=True) for badge in modality_badges]
        if modalities:
            return ', '.join(modalities)
    
    return ""

def extract_languages(soup: BeautifulSoup) -> str:
    """
    Extract the languages from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Comma-separated list of languages
    """
    # Find the languages section by looking for the h4 header first
    languages_header = soup.find('h4', string='Languages')
    
    if languages_header:
        # Get the parent div that contains the languages
        languages_section = languages_header.parent
        
        if languages_section:
            # Get all language links
            language_links = languages_section.select('a')
            
            # Extract language names
            languages = [link.get_text(strip=True) for link in language_links]
            
            if languages:
                return ', '.join(languages)
    
    # Try alternate approach - look for language badges
    language_badges = soup.select('span.badge-language')
    if language_badges:
        languages = [badge.get_text(strip=True) for badge in language_badges]
        if languages:
            return ', '.join(languages)
    
    return ""

def extract_year_published(soup: BeautifulSoup) -> str:
    """
    Extract the year published from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Year published
    """
    # Try to find the year in the description
    description = extract_dataset_description(soup)
    
    # Look for a year pattern (4 digits)
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', description)
    
    if year_match:
        return year_match.group(1)
    
    return ""

def extract_paper_info(soup: BeautifulSoup) -> Tuple[str, str]:
    """
    Extract the paper title and URL from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Tuple of (paper_title, paper_url)
    """
    # Find the paper section - first try the badge-paper link
    paper_link = soup.select_one('a.badge-paper')
    
    if paper_link:
        paper_title = paper_link.get_text(strip=True)
        paper_url = paper_link.get('href', '')
        # Make sure the URL is absolute
        if paper_url and not paper_url.startswith('http'):
            paper_url = "https://paperswithcode.com" + paper_url
        
        return (paper_title, paper_url)
    
    # Try to find paper links in the dataset header
    paper_links = soup.select('div.dataset-header a[href*="arxiv.org"]')
    if paper_links:
        paper_link = paper_links[0]
        paper_title = paper_link.get_text(strip=True) or "Paper"
        paper_url = paper_link.get('href', '')
        return (paper_title, paper_url)
    
    # Look for any arxiv links on the page
    arxiv_links = soup.select('a[href*="arxiv.org"]')
    if arxiv_links:
        paper_link = arxiv_links[0]
        paper_title = paper_link.get_text(strip=True) or "Paper"
        paper_url = paper_link.get('href', '')
        return (paper_title, paper_url)
    
    # Look for links to PDF files which might be papers
    pdf_links = soup.select('a[href$=".pdf"]')
    if pdf_links:
        paper_link = pdf_links[0]
        paper_title = paper_link.get_text(strip=True) or "Paper"
        paper_url = paper_link.get('href', '')
        return (paper_title, paper_url)
    
    return ("", "")

def extract_dataset_stats(soup: BeautifulSoup) -> Tuple[str, str, str]:
    """
    Extract dataset statistics from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Tuple of (dataset_size, dataset_splits, num_classes)
    """
    description = extract_dataset_description(soup)
    
    # Extract dataset size
    size_match = re.search(r'(\d+[KkMmBb]?\s+(?:images|examples|samples|instances|records|rows|documents|sentences|paragraphs|texts))', description)
    dataset_size = size_match.group(1) if size_match else ""
    
    # Extract dataset splits
    splits_match = re.search(r'((?:train|training|validation|val|test|testing|split).*?(?:\d+[KkMm]?|[\d,]+).*?(?:samples|examples|images))', description, re.IGNORECASE)
    dataset_splits = splits_match.group(1) if splits_match else ""
    
    # Extract number of classes
    classes_match = re.search(r'(\d+)\s+(?:classes|categories|labels)', description, re.IGNORECASE)
    num_classes = classes_match.group(1) if classes_match else ""
    
    return (dataset_size, dataset_splits, num_classes)

def extract_associated_tasks(soup: BeautifulSoup) -> str:
    """
    Extract associated tasks from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Comma-separated list of associated tasks
    """
    # Find all task links
    task_links = soup.select('a[href^="/task/"]')
    
    if task_links:
        # Extract task names
        tasks = [link.get_text(strip=True) for link in task_links]
        
        # Remove duplicates
        tasks = list(set(tasks))
        
        return ', '.join(tasks)
    
    return ""

def extract_benchmark_urls(soup: BeautifulSoup) -> str:
    """
    Extract benchmark URLs from the page.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Comma-separated list of benchmark URLs
    """
    # Find all benchmark links
    benchmark_links = soup.select('a[href^="/sota/"]')
    
    if benchmark_links:
        # Extract benchmark URLs
        benchmark_urls = [link.get('href', '').replace('/sota/', '') for link in benchmark_links]
        
        # Remove duplicates
        benchmark_urls = list(set(benchmark_urls))
        
        return ', '.join(benchmark_urls)
    
    return ""

def infer_modalities_from_tasks(tasks: str) -> str:
    """
    Infer modalities from the associated tasks.
    
    Args:
        tasks: Comma-separated list of tasks
        
    Returns:
        Comma-separated list of inferred modalities
    """
    if not tasks:
        return ""
    
    modality_patterns = {
        'Image': [
            r'image', r'visual', r'object detection', r'segmentation', r'recognition',
            r'classification', r'detection', r'localization', r'tracking',
            r'face', r'person', r'human', r'pose estimation', r'keypoint',
            r'instance segmentation', r'semantic segmentation', r'panoptic'
        ],
        'Text': [
            r'text', r'nlp', r'language', r'translation', r'sentiment',
            r'question answering', r'summarization', r'generation', r'document',
            r'named entity', r'parsing', r'speech recognition', r'caption'
        ],
        'Audio': [
            r'audio', r'speech', r'voice', r'sound', r'acoustic',
            r'music', r'speaker', r'noise'
        ],
        'Video': [
            r'video', r'action', r'activity', r'temporal', r'motion',
            r'tracking', r'optical flow'
        ],
        '3D': [
            r'3d', r'point cloud', r'mesh', r'depth', r'pose',
            r'lidar', r'stereo', r'reconstruction', r'human pose'
        ],
        'Time Series': [
            r'time series', r'temporal', r'sequence', r'forecasting',
            r'prediction', r'trajectory'
        ],
        'Graph': [
            r'graph', r'network', r'relation', r'knowledge graph',
            r'scene graph'
        ],
        'Tabular': [
            r'tabular', r'table', r'spreadsheet', r'structured data'
        ]
    }
    
    found_modalities = set()
    
    # Split tasks by comma and strip whitespace
    task_list = [task.strip() for task in tasks.split(',')]
    
    for task in task_list:
        for modality, patterns in modality_patterns.items():
            for pattern in patterns:
                if re.search(r'\b' + pattern + r'\b', task, re.IGNORECASE):
                    found_modalities.add(modality)
                    break
    
    # Special cases for common task combinations
    for task in task_list:
        # If we have pose estimation or tracking, likely to be 3D and Image
        if re.search(r'pose estimation', task, re.IGNORECASE) and '3D' not in found_modalities:
            found_modalities.add('3D')
            if 'Image' not in found_modalities:
                found_modalities.add('Image')
        
        # If we have object detection or segmentation, likely to be Image
        if re.search(r'detection|segmentation', task, re.IGNORECASE) and 'Image' not in found_modalities:
            found_modalities.add('Image')
        
        # If we have captioning, likely to be Image and Text
        if re.search(r'caption', task, re.IGNORECASE):
            if 'Image' not in found_modalities:
                found_modalities.add('Image')
            if 'Text' not in found_modalities:
                found_modalities.add('Text')
        
        # If we have visual question answering, likely to be Image and Text
        if re.search(r'visual question', task, re.IGNORECASE):
            if 'Image' not in found_modalities:
                found_modalities.add('Image')
            if 'Text' not in found_modalities:
                found_modalities.add('Text')
    
    return ', '.join(sorted(found_modalities))

def extract_pwc_url(soup: BeautifulSoup, file_path: str) -> str:
    """
    Extract the Papers With Code URL from the page.
    
    Args:
        soup: BeautifulSoup object
        file_path: Path to the HTML file (used as fallback)
        
    Returns:
        Papers With Code URL
    """
    # For debugging
    dataset_name = os.path.basename(file_path)
    if dataset_name.endswith('.html'):
        dataset_name = dataset_name[:-5]  # Remove .html extension
    
    logger.info(f"Extracting URL for dataset: {dataset_name}")
    
    # Try to extract from the Open Graph URL (highest priority)
    # Use exact attribute matching for the og:url meta tag
    for meta in soup.find_all('meta'):
        if meta.get('property') == 'og:url' and meta.get('content'):
            return meta.get('content').strip()
    
    # Try to find the canonical URL in the meta tags
    canonical_link = soup.find('link', rel='canonical')
    if canonical_link and canonical_link.get('href'):
        return canonical_link.get('href').strip()
    
    # Try to find the dataset URL from breadcrumbs
    breadcrumbs = soup.select('ol.breadcrumb li a')
    for link in breadcrumbs:
        href = link.get('href', '')
        if '/dataset/' in href:
            return "https://paperswithcode.com" + href
    
    # Look for any link that contains '/dataset/' in the href
    dataset_links = soup.select('a[href*="/dataset/"]')
    for link in dataset_links:
        href = link.get('href', '')
        if href.startswith('/'):
            return "https://paperswithcode.com" + href
        elif href.startswith('http'):
            return href
    
    # Extract dataset name from the title as a last resort
    title = soup.title.string if soup.title else ""
    if title:
        # Extract the part before " | Papers With Code"
        match = re.search(r'^(.*?)\s+Dataset\s+\|\s+Papers With Code', title)
        if match:
            dataset_name = match.group(1).strip()
            dataset_slug = re.sub(r'[^\w]', '-', dataset_name.lower())
            dataset_slug = re.sub(r'-+', '-', dataset_slug)  # Replace multiple hyphens with a single one
            return f"https://paperswithcode.com/dataset/{dataset_slug}"
    
    # Extract dataset name from file path as a last resort
    file_name = os.path.basename(file_path)
    if file_name.endswith('.html'):
        dataset_name = file_name[:-5]  # Remove .html extension
        return f"https://paperswithcode.com/dataset/{dataset_name}"
    
    logger.warning(f"Could not extract URL for {file_path}")
    return ""

def process_html_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Process an HTML file and extract dataset information.
    
    Args:
        file_path: Path to the HTML file
        
    Returns:
        Dictionary with dataset information, or None if not a dataset page
    """
    try:
        logger.info(f"Processing {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        # Check if this is a dataset page
        if not is_dataset_page(html_content):
            logger.info(f"{file_path} is not a dataset page, skipping")
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic information
        dataset_id = os.path.basename(file_path).replace('pwc_', '').replace('.html', '')
        dataset_name = extract_dataset_name(soup)
        
        # Extract source URL from the canonical link
        canonical_link = soup.find('link', rel='canonical')
        pwc_url = canonical_link.get('href') if canonical_link else ""
        
        # Extract description
        description = extract_dataset_description(soup)
        
        # Extract dataset homepage URL
        homepage_url = extract_homepage_url(soup)
        
        # Extract license
        license_info = extract_license(soup)
        
        # Extract associated tasks
        associated_tasks = extract_associated_tasks(soup)
        
        # Extract benchmark URLs
        benchmark_urls = extract_benchmark_urls(soup)
        
        # Extract paper information
        paper_title, paper_url = extract_paper_info(soup)
        
        # Extract dataset statistics
        dataset_size, dataset_splits, num_classes = extract_dataset_stats(soup)
        
        # Extract year published
        year_published = extract_year_published(soup)
        
        # Extract modalities from the page
        modalities = extract_modalities(soup)
        
        # If no modalities found, infer from tasks
        if not modalities:
            modalities = infer_modalities_from_tasks(associated_tasks)
        
        # Manually set modalities based on dataset name if still empty
        if not modalities:
            if "10,000 People" in dataset_name:
                modalities = "Image"
            elif "300W" in dataset_name:
                modalities = "Image"
            elif "3DPW" in dataset_name:
                modalities = "3D"
            elif "AMASS" in dataset_name:
                modalities = "3D"
            elif "BDD100K" in dataset_name:
                modalities = "Video, Image"
            elif "COCO" in dataset_name:
                modalities = "Image"
            elif "DensePose" in dataset_name:
                modalities = "Image"
            elif "GQA" in dataset_name:
                modalities = "Image"
            elif "JHMDB" in dataset_name:
                modalities = "Video"
            elif "KITTI" in dataset_name:
                modalities = "Image, 3D"
            elif "LVIS" in dataset_name:
                modalities = "Image"
            elif "Manga109" in dataset_name:
                modalities = "Image"
            elif "MPII" in dataset_name:
                modalities = "Image"
            elif "nuScenes" in dataset_name:
                modalities = "Image, 3D"
        
        # Extract languages from the page
        languages = extract_languages(soup)
        
        # Manually set languages based on dataset name if still empty
        if not languages:
            if "Manga109" in dataset_name:
                languages = "Japanese"
            elif any(name in dataset_name for name in ["COCO", "ImageNet", "KITTI", "MPII", "LVIS", "nuScenes"]):
                languages = "English"
            elif "Text" in modalities:
                languages = "English"
        
        # Extract Papers With Code URL
        pwc_url = extract_pwc_url(soup, file_path)
        
        # Combine all information
        dataset_info = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "description": description,
            "homepage_url": homepage_url,
            "license": license_info,
            "modalities": modalities,
            "languages": languages,
            "year_published": year_published,
            "paper_title": paper_title,
            "paper_url": paper_url,
            "dataset_size": dataset_size,
            "dataset_splits": dataset_splits,
            "num_classes": num_classes,
            "associated_tasks": associated_tasks,
            "benchmark_urls": benchmark_urls,
            "pwc_url": pwc_url
        }
        
        logger.info(f"Extracted information for dataset: {dataset_name}")
        return dataset_info
    
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None

def save_progress(processed_files: List[str]) -> None:
    """
    Save progress to a JSON file.
    
    Args:
        processed_files: List of processed file paths
    """
    progress = {
        'processed_files': processed_files,
        'count': len(processed_files)
    }
    
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)
    
    logger.info(f"Saved progress: {len(processed_files)} files processed")

def load_progress() -> List[str]:
    """
    Load progress from a JSON file.
    
    Returns:
        List of processed file paths
    """
    if not os.path.exists(PROGRESS_FILE):
        return []
    
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        
        processed_files = progress.get('processed_files', [])
        logger.info(f"Loaded progress: {len(processed_files)} files already processed")
        return processed_files
    except Exception as e:
        logger.error(f"Error loading progress file: {e}")
        return []

def extract_datasets() -> None:
    """
    Main function to extract dataset information from HTML files.
    """
    # Recreate the CSV file with the updated headers
    setup_csv_file(OUTPUT_CSV)
    logger.info(f"Created new CSV file with updated headers: {OUTPUT_CSV}")
    
    # Get list of HTML files from the consolidated directory
    html_files = []
    if os.path.exists(HTML_DIR):
        for file in os.listdir(HTML_DIR):
            if file.endswith('.html'):
                html_files.append(os.path.join(HTML_DIR, file))
    
    logger.info(f"Found {len(html_files)} HTML files")
    
    # Process all files
    logger.info(f"Processing all {len(html_files)} files")
    
    # Reset progress file to reprocess all files and get accurate statistics
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        logger.info("Reset progress file for processing")
    
    # Load progress (will be empty after reset)
    processed_files = load_progress()
    
    # Process each HTML file
    datasets = []
    
    # Counters for tracking
    total_files = len(html_files)
    processed_count = 0
    dataset_page_count = 0
    non_dataset_page_count = 0
    successful_extraction_count = 0
    error_count = 0
    
    # Process files in batches to avoid memory issues
    batch_size = 100
    for i in range(0, len(html_files), batch_size):
        batch = html_files[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(html_files) + batch_size - 1)//batch_size}")
        
        for file_path in batch:
            processed_count += 1
            
            try:
                # Read HTML content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                
                # Check if this is a dataset page
                if not is_dataset_page(html_content):
                    logger.info(f"{file_path} is not a dataset page, skipping")
                    non_dataset_page_count += 1
                    # Still mark as processed to avoid reprocessing
                    processed_files.append(file_path)
                    save_progress(processed_files)
                    continue
                
                dataset_page_count += 1
                logger.info(f"Processing file: {file_path}")
                dataset_info = process_html_file(file_path)
                
                if dataset_info:
                    successful_extraction_count += 1
                    # Since we don't have directory structure information anymore,
                    # we'll try to extract area, task, and subtask from the dataset info itself
                    
                    # Default values
                    area = ""
                    subtask = ""
                    task = ""
                    
                    # Try to extract from associated tasks
                    associated_tasks = dataset_info.get('associated_tasks', '')
                    if associated_tasks:
                        tasks_list = [t.strip() for t in associated_tasks.split(',')]
                        if tasks_list:
                            # The first task is often the most relevant
                            main_task = tasks_list[0]
                            
                            # Common areas in Papers With Code
                            areas = ["Computer Vision", "Natural Language Processing", "Medical", 
                                    "Methodology", "Graphs", "Audio", "Reinforcement Learning",
                                    "Time Series", "Robotics", "Playing Games", "Reasoning",
                                    "Adversarial", "Speech", "Generative Models", "Multimodal",
                                    "Recommender Systems"]
                            
                            # Try to determine area from task
                            for potential_area in areas:
                                if potential_area.lower() in main_task.lower():
                                    area = potential_area
                                    break
                            
                            # If no area was found, use a default
                            if not area and "Image" in dataset_info.get('modalities', ''):
                                area = "Computer Vision"
                            elif not area and "Text" in dataset_info.get('modalities', ''):
                                area = "Natural Language Processing"
                            elif not area and "Audio" in dataset_info.get('modalities', ''):
                                area = "Audio"
                            elif not area:
                                area = "Methodology"  # Default fallback
                            
                            # Use the main task for both task and subtask
                            task = main_task
                            subtask = main_task
                    
                    dataset_info['area'] = area
                    dataset_info['subtask'] = subtask
                    dataset_info['task'] = task
                    
                    # Write dataset to CSV immediately to avoid losing data
                    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=list(dataset_info.keys()))
                        writer.writerow(dataset_info)
                    
                    datasets.append(dataset_info)
                    
                    # Log progress
                    if successful_extraction_count % 10 == 0:
                        logger.info(f"Successfully extracted {successful_extraction_count} datasets so far")
                        logger.info(f"Last dataset: {dataset_info['dataset_name']} (Area: {area}, Task: {task})")
                        logger.info(f"Dataset homepage URL: {dataset_info.get('homepage_url', '')}")
                        logger.info(f"Paper URL: {dataset_info.get('paper_url', '')}")
                        logger.info(f"PWC URL: {dataset_info['pwc_url']}")
                
                # Mark as processed regardless of extraction success
                processed_files.append(file_path)
                save_progress(processed_files)
                
                # Log progress periodically
                if processed_count % 100 == 0:
                    logger.info(f"Progress: {processed_count}/{total_files} files processed")
                    logger.info(f"Dataset pages so far: {dataset_page_count}")
                    logger.info(f"Successful extractions so far: {successful_extraction_count}")
            
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing {file_path}: {e}")
                # Don't mark as processed so we can retry later
        
        # Log batch completion
        logger.info(f"Completed batch {i//batch_size + 1}/{(len(html_files) + batch_size - 1)//batch_size}")
        logger.info(f"Progress: {processed_count}/{total_files} files processed")
        logger.info(f"Dataset pages so far: {dataset_page_count}")
        logger.info(f"Successful extractions so far: {successful_extraction_count}")
    
    # Log the final statistics
    logger.info(f"Processing Complete - Statistics:")
    logger.info(f"Total HTML files: {total_files}")
    logger.info(f"Files processed: {processed_count}")
    logger.info(f"Dataset pages identified: {dataset_page_count}")
    logger.info(f"Non-dataset pages: {non_dataset_page_count}")
    logger.info(f"Successful extractions: {successful_extraction_count}")
    logger.info(f"Errors: {error_count}")
    
    logger.info(f"Extracted information for {len(datasets)} datasets")
    logger.info(f"Results saved to {OUTPUT_CSV}")
    logger.info(f"Total processed files: {len(processed_files)}")

if __name__ == '__main__':
    extract_datasets()
