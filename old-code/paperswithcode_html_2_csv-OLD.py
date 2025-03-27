#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Papers With Code HTML to CSV Converter

This script extracts detailed information from Papers With Code benchmark HTML files
and saves it to a CSV file. It's designed to help researchers select appropriate
benchmarks for their specific problems by providing comprehensive metadata.

Usage:
    python paperswithcode_html_2_csv.py

The script will:
1. Read all HTML files in the paperswithcode directory
2. Extract detailed information from each file
3. Save the extracted information to a CSV file in the csv directory
"""

import os
import csv
import json
import re
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BENCHMARKS_DIR = "paperswithcode"
CSV_DIR = "csv"
CSV_FILENAME = "paperswithcode_benchmarks_comprehensive.csv"

# Define the benchmark fields
BENCHMARK_FIELDS = [
    'benchmark_name',
    'full_name',
    'modality',
    'task_type',
    'domain',
    'description',
    'paper_link',
    'dataset_link',
    'github_link',
    'homepage_link',
    'languages',
    'dataset_size',
    'num_train_examples',
    'num_val_examples',
    'num_test_examples',
    'sota_performance',
    'sota_model',
    'sota_paper_title',
    'sota_paper_link',
    'sota_code_link',
    'evaluation_metrics',
    'metric_description',
    'license_details',
    'last_updated',
    'citation_count',
    'similar_benchmarks',
    'data_format',
    'preprocessing_notes',
    'ethical_considerations',
    'model_architectures',
    'hardware_requirements',
    'training_time'
]

def clean_text(text):
    """
    Clean and standardize text by removing extra whitespace and normalizing.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Replace newlines and tabs with spaces
    text = re.sub(r'[\n\t\r]+', ' ', text)
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Trim
    return text.strip()

def is_area_page(html_content):
    """
    Determine if the HTML content is from an area page or a specific benchmark page.
    
    Args:
        html_content: HTML content to check
        
    Returns:
        True if it's an area page, False if it's a benchmark page
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

def extract_benchmark_info(benchmark_name, html_content) -> Dict[str, Any]:
    """
    Extract detailed information from a benchmark page.
    
    Args:
        benchmark_name: Name of the benchmark
        html_content: HTML content of the benchmark page
        
    Returns:
        Dictionary containing extracted benchmark information
    """
    logger.info(f"Extracting information for {benchmark_name}")
    
    # Initialize benchmark data
    benchmark_data = {field: "" for field in BENCHMARK_FIELDS}
    benchmark_data['benchmark_name'] = benchmark_name
    
    # Check if HTML content is empty
    if not html_content:
        logger.warning(f"Empty HTML content for {benchmark_name}")
        return benchmark_data
    
    # Check if this is an area page instead of a benchmark page
    if is_area_page(html_content):
        logger.info(f"{benchmark_name} is an area page, not a specific benchmark")
        return None
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract benchmark full name from title
        title_element = soup.find('title')
        if title_element:
            title_text = title_element.get_text()
            # Extract the benchmark name from the title
            if '|' in title_text:
                full_name = title_text.split('|')[0].strip()
                benchmark_data['full_name'] = full_name
        
        # Extract description from meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            benchmark_data['description'] = clean_text(meta_desc.get('content'))
        
        # Extract task type from breadcrumbs or title
        task_element = soup.select_one('.general-breadcrumb a')
        if task_element:
            benchmark_data['task_type'] = clean_text(task_element.get_text())
        elif title_element and '(' in title_element.get_text() and ')' in title_element.get_text():
            # Extract task from title, e.g., "LibriSpeech test-clean Benchmark (Speech Recognition)"
            task_match = re.search(r'\((.*?)\)', title_element.get_text())
            if task_match:
                benchmark_data['task_type'] = task_match.group(1)
        
        # Determine modality from task type
        if benchmark_data['task_type']:
            task_lower = benchmark_data['task_type'].lower()
            if any(term in task_lower for term in ['image', 'visual', 'vision']):
                benchmark_data['modality'] = 'Image'
            elif any(term in task_lower for term in ['text', 'nlp', 'language', 'translation', 'sentiment']):
                benchmark_data['modality'] = 'Text'
            elif any(term in task_lower for term in ['audio', 'speech', 'sound']):
                benchmark_data['modality'] = 'Audio'
            elif any(term in task_lower for term in ['video']):
                benchmark_data['modality'] = 'Video'
            elif any(term in task_lower for term in ['graph']):
                benchmark_data['modality'] = 'Graph'
            else:
                benchmark_data['modality'] = 'Other'
        
        # Extract domain based on task or title
        if benchmark_data['task_type'] or benchmark_data['full_name']:
            text_to_check = (benchmark_data['task_type'] + ' ' + benchmark_data['full_name']).lower()
            if any(term in text_to_check for term in ['medical', 'healthcare', 'clinical', 'brats']):
                benchmark_data['domain'] = 'Medical'
            elif any(term in text_to_check for term in ['scientific', 'science']):
                benchmark_data['domain'] = 'Scientific'
            elif any(term in text_to_check for term in ['document', 'pdf']):
                benchmark_data['domain'] = 'Document'
            elif any(term in text_to_check for term in ['code', 'programming']):
                benchmark_data['domain'] = 'Code'
            else:
                benchmark_data['domain'] = 'General'
        
        # Extract links from JSON-LD data if available
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                ld_data = json.loads(json_ld.string)
                if isinstance(ld_data, dict) and '@graph' in ld_data:
                    ld_data = ld_data['@graph']
                
                if isinstance(ld_data, dict):
                    if 'url' in ld_data:
                        benchmark_data['homepage_link'] = ld_data['url']
                    if 'description' in ld_data and not benchmark_data['description']:
                        benchmark_data['description'] = clean_text(ld_data['description'])
            except json.JSONDecodeError:
                logger.warning(f"Could not parse JSON-LD for {benchmark_name}")
        
        # Extract SOTA information from the leaderboard
        leaderboard = soup.select_one('.leaderboard-table-container')
        if leaderboard:
            # Find the first row which should be the SOTA
            sota_row = leaderboard.select_one('tbody tr')
            if sota_row:
                # Extract model name
                model_cell = sota_row.select_one('td.model-name')
                if model_cell:
                    model_link = model_cell.select_one('a')
                    if model_link:
                        benchmark_data['sota_model'] = clean_text(model_link.get_text())
                
                # Extract performance
                metric_cells = sota_row.select('td.metric')
                if metric_cells:
                    performance_values = []
                    for cell in metric_cells:
                        performance_values.append(clean_text(cell.get_text()))
                    benchmark_data['sota_performance'] = ', '.join(performance_values)
                
                # Extract paper title and link
                paper_cell = sota_row.select_one('td.paper-title')
                if paper_cell:
                    paper_link = paper_cell.select_one('a')
                    if paper_link:
                        benchmark_data['sota_paper_title'] = clean_text(paper_link.get_text())
                        benchmark_data['sota_paper_link'] = paper_link.get('href', '')
                
                # Extract code link
                code_cell = sota_row.select_one('td.code-link')
                if code_cell:
                    code_link = code_cell.select_one('a')
                    if code_link:
                        benchmark_data['sota_code_link'] = code_link.get('href', '')
        
        # Extract evaluation metrics from the table header
        if leaderboard:
            metric_headers = leaderboard.select('thead th.metric')
            metrics = []
            for header in metric_headers:
                metric_name = clean_text(header.get_text())
                if metric_name:
                    metrics.append(metric_name)
            benchmark_data['evaluation_metrics'] = ', '.join(metrics)
        
        # Extract dataset information
        dataset_section = soup.select_one('.dataset-section')
        if dataset_section:
            # Dataset link
            dataset_link = dataset_section.select_one('a')
            if dataset_link:
                benchmark_data['dataset_link'] = dataset_link.get('href', '')
            
            # Dataset size and splits
            dataset_stats = dataset_section.select('.dataset-stat')
            for stat in dataset_stats:
                stat_text = clean_text(stat.get_text()).lower()
                if 'train' in stat_text:
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        benchmark_data['num_train_examples'] = match.group(1)
                elif 'val' in stat_text or 'validation' in stat_text:
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        benchmark_data['num_val_examples'] = match.group(1)
                elif 'test' in stat_text:
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        benchmark_data['num_test_examples'] = match.group(1)
                elif 'total' in stat_text or 'size' in stat_text:
                    match = re.search(r'(\d+)', stat_text)
                    if match:
                        benchmark_data['dataset_size'] = match.group(1)
        
        # Extract last updated date
        updated_element = soup.select_one('.last-updated')
        if updated_element:
            benchmark_data['last_updated'] = clean_text(updated_element.get_text().replace('Last updated:', ''))
        
        # Extract similar benchmarks
        similar_section = soup.select_one('.similar-benchmarks')
        if similar_section:
            similar_links = similar_section.select('a')
            similar_benchmarks = []
            for link in similar_links:
                similar_benchmarks.append(clean_text(link.get_text()))
            benchmark_data['similar_benchmarks'] = ', '.join(similar_benchmarks)
        
        return benchmark_data
    
    except Exception as e:
        logger.error(f"Error extracting information for {benchmark_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return benchmark_data

def extract_benchmarks_from_area_page(area_name, html_content) -> List[Dict[str, Any]]:
    """
    Extract benchmark links from an area page and create stub entries.
    
    Args:
        area_name: Name of the area
        html_content: HTML content of the area page
        
    Returns:
        List of dictionaries containing basic benchmark information
    """
    logger.info(f"Extracting benchmarks from area page: {area_name}")
    
    benchmarks = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all benchmark links in the area page
        benchmark_links = soup.select('a[href^="/sota/"]')
        
        for link in benchmark_links:
            benchmark_name = link.get('href', '').split('/')[-1]
            if benchmark_name:
                # Create a basic benchmark entry
                benchmark_data = {field: "" for field in BENCHMARK_FIELDS}
                benchmark_data['benchmark_name'] = benchmark_name
                benchmark_data['full_name'] = clean_text(link.get_text())
                benchmark_data['domain'] = area_name.replace('pwc_', '').replace('.html', '')
                
                benchmarks.append(benchmark_data)
                logger.info(f"Found benchmark: {benchmark_name}")
        
        logger.info(f"Found {len(benchmarks)} benchmarks in area {area_name}")
        return benchmarks
    
    except Exception as e:
        logger.error(f"Error extracting benchmarks from area {area_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def extract_from_html_files():
    """
    Extract benchmark information from all HTML files in the paperswithcode folder.
    
    Returns:
        List of dictionaries containing benchmark metadata
    """
    logger.info("Extracting benchmark information from HTML files")
    
    benchmarks = []
    area_benchmarks = []
    
    # Check if the directory exists
    if not os.path.exists(BENCHMARKS_DIR):
        logger.error(f"Directory {BENCHMARKS_DIR} does not exist")
        return benchmarks
    
    # Get all HTML files
    html_files = [f for f in os.listdir(BENCHMARKS_DIR) if f.endswith('.html')]
    logger.info(f"Found {len(html_files)} HTML files")
    
    # First pass: Process benchmark pages
    for html_file in html_files:
        file_path = os.path.join(BENCHMARKS_DIR, html_file)
        
        # Extract benchmark name from filename
        # Example: pwc_image-classification-on-imagenet.html -> image-classification-on-imagenet
        benchmark_name = html_file.replace('pwc_', '').replace('.html', '')
        
        try:
            logger.info(f"Processing file: {html_file}")
            
            # Read the HTML content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            logger.info(f"Read {len(html_content)} bytes from {html_file}")
            
            # Check if this is an area page
            is_area = is_area_page(html_content)
            logger.info(f"Is {html_file} an area page? {is_area}")
            
            if is_area:
                # Process area page in the second pass
                continue
            
            # Extract benchmark information
            benchmark_data = extract_benchmark_info(benchmark_name, html_content)
            
            if benchmark_data:
                benchmarks.append(benchmark_data)
                logger.info(f"Successfully extracted information for {benchmark_name}")
            else:
                logger.warning(f"Failed to extract information for {benchmark_name}")
            
        except Exception as e:
            logger.error(f"Error processing {html_file}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info(f"First pass completed. Found {len(benchmarks)} benchmark pages.")
    
    # Second pass: Process area pages to find additional benchmarks
    for html_file in html_files:
        file_path = os.path.join(BENCHMARKS_DIR, html_file)
        area_name = html_file.replace('pwc_', '').replace('.html', '')
        
        try:
            # Read the HTML content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # Check if this is an area page
            if is_area_page(html_content):
                logger.info(f"Processing area page: {html_file}")
                # Extract benchmarks from area page
                area_benchmark_data = extract_benchmarks_from_area_page(area_name, html_content)
                
                # Add only benchmarks that weren't already found
                existing_benchmark_names = [b['benchmark_name'] for b in benchmarks]
                for benchmark in area_benchmark_data:
                    if benchmark['benchmark_name'] not in existing_benchmark_names:
                        area_benchmarks.append(benchmark)
                        logger.info(f"Added benchmark {benchmark['benchmark_name']} from area {area_name}")
        
        except Exception as e:
            logger.error(f"Error processing area page {html_file}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Combine benchmark data
    all_benchmarks = benchmarks + area_benchmarks
    logger.info(f"Total benchmarks found: {len(all_benchmarks)}")
    
    return all_benchmarks

def main():
    """
    Main function to extract benchmark information from HTML files and save to CSV.
    """
    try:
        # Create CSV directory if it doesn't exist
        os.makedirs(CSV_DIR, exist_ok=True)
        
        # Extract benchmark information from HTML files
        benchmarks = extract_from_html_files()
        
        if not benchmarks:
            logger.warning("No benchmark information extracted")
            return
        
        # Save to CSV
        csv_path = os.path.join(CSV_DIR, CSV_FILENAME)
        logger.info(f"Writing {len(benchmarks)} benchmarks to {csv_path}")
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=BENCHMARK_FIELDS)
            writer.writeheader()
            writer.writerows(benchmarks)
        
        logger.info(f"Saved benchmark information to {csv_path}")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
