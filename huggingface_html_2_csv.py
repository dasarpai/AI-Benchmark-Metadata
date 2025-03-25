#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hugging Face HTML to CSV Converter

This script extracts detailed information from Hugging Face dataset HTML files
and saves it to a CSV file. It's designed to help researchers select appropriate
benchmarks for their specific problems by providing comprehensive metadata.

Usage:
    python huggingface_html_2_csv.py

The script will:
1. Read all HTML files in the huggingface directory
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
DATASETS_DIR = "huggingface"
CSV_DIR = "csv"
CSV_FILENAME = "huggingface_datasets_comprehensive.csv"

# Define the benchmark fields
BENCHMARK_FIELDS = [
    'benchmark_name',
    'modality',
    'task_type',
    'domain',
    'output_type',
    'evaluation_metrics',
    'paper_link',
    'dataset_link',
    'languages',
    'dataset_size',
    'num_train_examples',
    'num_val_examples',
    'num_test_examples',
    'sota_performance',
    'sota_model',
    'license_details',
    'last_updated',
    'citation_count',
    'downloads',
    'example_code_link',
    'similar_benchmarks',
    'data_format',
    'preprocessing_notes',
    'ethical_considerations',
    'model_architectures',
    'hardware_requirements',
    'training_time'
]

# Common evaluation metrics by task type
EVALUATION_METRICS_BY_TASK = {
    'Classification': 'Accuracy, F1 Score, Precision, Recall',
    'Question Answering': 'Exact Match, F1 Score',
    'Summarization': 'ROUGE, BLEU, BERTScore',
    'Translation': 'BLEU, METEOR, TER',
    'Sentiment Analysis': 'Accuracy, F1 Score',
    'Detection': 'mAP, IoU',
    'Segmentation': 'IoU, Pixel Accuracy',
    'Captioning': 'BLEU, METEOR, CIDEr, ROUGE',
    'Reasoning': 'Accuracy, F1 Score',
    'General': 'Accuracy, F1 Score'
}

# Model architectures by task type
MODEL_ARCHITECTURES_BY_TASK = {
    'Classification': 'BERT, RoBERTa, DeBERTa, XLNet',
    'Question Answering': 'BERT, RoBERTa, T5, BART',
    'Summarization': 'BART, T5, Pegasus, ProphetNet',
    'Translation': 'T5, mBART, M2M100',
    'Sentiment Analysis': 'BERT, RoBERTa, DistilBERT',
    'Detection': 'DETR, Faster R-CNN, YOLO',
    'Segmentation': 'Mask R-CNN, DeepLab, U-Net',
    'Captioning': 'CLIP, VL-BERT, ViLBERT',
    'Reasoning': 'T5, UnifiedQA, BART',
    'General': 'BERT, RoBERTa, T5'
}

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

def extract_dataset_info(dataset_name, html_content) -> Dict[str, Any]:
    """
    Extract detailed information from a dataset page.
    
    Args:
        dataset_name: Name of the dataset
        html_content: HTML content of the dataset page
        
    Returns:
        Dictionary containing extracted dataset information
    """
    logger.info(f"Extracting information for {dataset_name}")
    
    # Initialize dataset data
    dataset_data = {field: "" for field in BENCHMARK_FIELDS}
    dataset_data['benchmark_name'] = dataset_name
    dataset_data['dataset_link'] = f"https://huggingface.co/datasets/{dataset_name}"
    
    # Check if HTML content is empty
    if not html_content:
        logger.warning(f"Empty HTML content for {dataset_name}")
        return dataset_data
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Method 1: Extract from JSON-LD metadata
        json_ld_script = soup.find('script', type='application/ld+json')
        if json_ld_script and json_ld_script.string:
            try:
                json_ld_data = json.loads(json_ld_script.string)
                
                if 'description' in json_ld_data:
                    description = json_ld_data['description']
                    
                    # Extract the dataset summary section
                    summary_match = re.search(r'Dataset Summary\s*\n\s*\n(.*?)(?:\n\s*\n\s*\n\s*\n\s*\n\s*\t\t\S|\Z)', 
                                             description, re.DOTALL)
                    if summary_match:
                        summary_text = summary_match.group(1).strip()
                        logger.info(f"Found summary for {dataset_name}: {summary_text[:100]}...")
                        
                        # Try to determine modality from summary
                        if any(term in summary_text.lower() for term in ['image', 'visual', 'picture']):
                            if any(term in summary_text.lower() for term in ['text', 'language']):
                                dataset_data['modality'] = 'Image-Text'
                            else:
                                dataset_data['modality'] = 'Image'
                        elif any(term in summary_text.lower() for term in ['video', 'motion']):
                            dataset_data['modality'] = 'Video'
                        elif any(term in summary_text.lower() for term in ['audio', 'sound', 'speech']):
                            dataset_data['modality'] = 'Audio'
                        elif any(term in summary_text.lower() for term in ['text', 'language', 'nlp']):
                            dataset_data['modality'] = 'Text'
                        else:
                            dataset_data['modality'] = 'Text'  # Default to Text
                        
                        # Try to determine domain from summary
                        if any(term in summary_text.lower() for term in ['scientific', 'science', 'research']):
                            dataset_data['domain'] = 'Scientific'
                        elif any(term in summary_text.lower() for term in ['ui', 'interface', 'gui']):
                            dataset_data['domain'] = 'UI'
                        elif any(term in summary_text.lower() for term in ['document', 'pdf', 'ocr']):
                            dataset_data['domain'] = 'Document'
                        else:
                            dataset_data['domain'] = 'General'
                        
                        # Try to determine task type from summary
                        if 'question answering' in summary_text.lower():
                            dataset_data['task_type'] = 'Question Answering'
                        elif 'classification' in summary_text.lower():
                            dataset_data['task_type'] = 'Classification'
                        elif 'detection' in summary_text.lower():
                            dataset_data['task_type'] = 'Detection'
                        elif 'segmentation' in summary_text.lower():
                            dataset_data['task_type'] = 'Segmentation'
                        elif 'captioning' in summary_text.lower():
                            dataset_data['task_type'] = 'Captioning'
                        elif 'translation' in summary_text.lower():
                            dataset_data['task_type'] = 'Translation'
                        elif 'summarization' in summary_text.lower():
                            dataset_data['task_type'] = 'Summarization'
                        elif 'reasoning' in summary_text.lower():
                            dataset_data['task_type'] = 'Reasoning'
                        elif 'sentiment' in summary_text.lower():
                            dataset_data['task_type'] = 'Sentiment Analysis'
                        else:
                            dataset_data['task_type'] = 'General'
                        
                        # Try to determine output type from task type
                        if dataset_data['task_type'] in ['Classification', 'Sentiment Analysis']:
                            dataset_data['output_type'] = 'Label'
                        elif dataset_data['task_type'] in ['Detection', 'Segmentation']:
                            dataset_data['output_type'] = 'Bounding Box/Mask'
                        elif dataset_data['task_type'] in ['Question Answering', 'Captioning', 'Translation', 'Summarization']:
                            dataset_data['output_type'] = 'Text'
                        else:
                            dataset_data['output_type'] = 'Text'
                            
                        # Extract languages from summary
                        language_pattern = re.compile(r'languages?:?\s*([^\.]+)', re.IGNORECASE)
                        language_match = language_pattern.search(summary_text)
                        if language_match:
                            languages = language_match.group(1).strip()
                            dataset_data['languages'] = clean_text(languages)
                        else:
                            # Try another pattern for languages
                            language_pattern2 = re.compile(r'in\s+(\w+(?:,\s+\w+)*)\s+languages?', re.IGNORECASE)
                            language_match2 = language_pattern2.search(summary_text)
                            if language_match2:
                                dataset_data['languages'] = clean_text(language_match2.group(1))
                            elif 'english' in summary_text.lower():
                                dataset_data['languages'] = 'English'
                        
                        # Extract dataset size information
                        size_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(GB|MB|KB|TB)', re.IGNORECASE)
                        size_matches = size_pattern.findall(summary_text)
                        if size_matches:
                            size_info = ', '.join([f"{size} {unit}" for size, unit in size_matches])
                            dataset_data['dataset_size'] = clean_text(size_info)
                        
                        # Extract number of examples for different splits
                        train_pattern = re.compile(r'train(?:ing)?\s*(?:set|split)?:?\s*(\d+(?:,\d+)*)\s*(?:examples|samples|instances|rows|records)', re.IGNORECASE)
                        train_match = train_pattern.search(summary_text)
                        if train_match:
                            dataset_data['num_train_examples'] = train_match.group(1).replace(',', '')
                        
                        val_pattern = re.compile(r'(?:val(?:idation)?|dev(?:elopment)?)\s*(?:set|split)?:?\s*(\d+(?:,\d+)*)\s*(?:examples|samples|instances|rows|records)', re.IGNORECASE)
                        val_match = val_pattern.search(summary_text)
                        if val_match:
                            dataset_data['num_val_examples'] = val_match.group(1).replace(',', '')
                        
                        test_pattern = re.compile(r'test(?:ing)?\s*(?:set|split)?:?\s*(\d+(?:,\d+)*)\s*(?:examples|samples|instances|rows|records)', re.IGNORECASE)
                        test_match = test_pattern.search(summary_text)
                        if test_match:
                            dataset_data['num_test_examples'] = test_match.group(1).replace(',', '')
                        
                        # If we couldn't find specific splits, try to find total examples
                        if not any([dataset_data['num_train_examples'], dataset_data['num_val_examples'], dataset_data['num_test_examples']]):
                            examples_pattern = re.compile(r'(?:total|contains|consists of)?\s*(\d+(?:,\d+)*)\s*(?:examples|samples|instances|rows|records)', re.IGNORECASE)
                            examples_match = examples_pattern.search(summary_text)
                            if examples_match:
                                dataset_data['num_train_examples'] = examples_match.group(1).replace(',', '')
                        
                        # Extract SOTA performance
                        sota_pattern = re.compile(r'(?:state-of-the-art|sota|best).+?(\d+(?:\.\d+)?%?)', re.IGNORECASE)
                        sota_match = sota_pattern.search(summary_text)
                        if sota_match:
                            dataset_data['sota_performance'] = clean_text(sota_match.group(1))
                        
                        # Extract ethical considerations
                        ethics_pattern = re.compile(r'(?:ethical|bias|fairness|demographic).+?([^\.]+)', re.IGNORECASE)
                        ethics_match = ethics_pattern.search(summary_text)
                        if ethics_match:
                            dataset_data['ethical_considerations'] = clean_text(ethics_match.group(1))
                        
                        # Extract preprocessing notes
                        preproc_pattern = re.compile(r'(?:preprocess|tokeniz|clean).+?([^\.]+)', re.IGNORECASE)
                        preproc_match = preproc_pattern.search(summary_text)
                        if preproc_match:
                            dataset_data['preprocessing_notes'] = clean_text(preproc_match.group(1))
                        
                        # Extract hardware requirements
                        hardware_pattern = re.compile(r'(?:hardware|gpu|cpu|memory|ram).+?([^\.]+)', re.IGNORECASE)
                        hardware_match = hardware_pattern.search(summary_text)
                        if hardware_match:
                            dataset_data['hardware_requirements'] = clean_text(hardware_match.group(1))
                        
                        # Extract training time
                        time_pattern = re.compile(r'(?:train(?:ing)? time|hours|minutes).+?([^\.]+)', re.IGNORECASE)
                        time_match = time_pattern.search(summary_text)
                        if time_match:
                            dataset_data['training_time'] = clean_text(time_match.group(1))
                
                # Extract paper link from JSON-LD metadata
                if 'keywords' in json_ld_data:
                    for keyword in json_ld_data['keywords']:
                        if keyword.startswith('arxiv:'):
                            dataset_data['paper_link'] = f"https://arxiv.org/abs/{keyword.replace('arxiv:', '')}"
                            break
                
                # Extract license from JSON-LD metadata
                if 'license' in json_ld_data:
                    license_url = json_ld_data['license']
                    dataset_data['license_details'] = license_url
                
                # Extract sameAs URL if available
                if 'sameAs' in json_ld_data:
                    dataset_data['paper_link'] = json_ld_data['sameAs']
                
                # Extract dateModified if available
                if 'dateModified' in json_ld_data:
                    dataset_data['last_updated'] = json_ld_data['dateModified']
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON-LD data for {dataset_name}")
        
        # Method 2: Extract from HTML if JSON-LD failed
        if not dataset_data['modality']:
            # Find the dataset summary section
            summary_heading = soup.find(string=lambda text: text and "Dataset Summary" in text)
            
            if summary_heading:
                # Find the parent element that contains the summary
                summary_parent = summary_heading.find_parent()
                if summary_parent:
                    # Get the next sibling which should contain the summary text
                    summary_text = ""
                    next_element = summary_parent.find_next_sibling()
                    if next_element:
                        summary_text = next_element.get_text(strip=True)
                    
                    logger.info(f"Found summary from HTML: {summary_text[:100]}...")
                    
                    # Apply the same logic as above to determine modality, domain, etc.
                    if any(term in summary_text.lower() for term in ['image', 'visual', 'picture']):
                        if any(term in summary_text.lower() for term in ['text', 'language']):
                            dataset_data['modality'] = 'Image-Text'
                        else:
                            dataset_data['modality'] = 'Image'
                    elif any(term in summary_text.lower() for term in ['video', 'motion']):
                        dataset_data['modality'] = 'Video'
                    elif any(term in summary_text.lower() for term in ['audio', 'sound', 'speech']):
                        dataset_data['modality'] = 'Audio'
                    elif any(term in summary_text.lower() for term in ['text', 'language', 'nlp']):
                        dataset_data['modality'] = 'Text'
                    else:
                        dataset_data['modality'] = 'Text'  # Default to Text
        
        # Extract additional information from HTML
        
        # Find download statistics
        downloads_element = soup.select_one('span:-soup-contains("downloads")')
        if downloads_element:
            downloads_text = downloads_element.get_text(strip=True)
            downloads_match = re.search(r'(\d+(?:,\d+)*)', downloads_text)
            if downloads_match:
                dataset_data['downloads'] = downloads_match.group(1).replace(',', '')
        
        # Find citation count
        citation_element = soup.select_one('span:-soup-contains("citations")')
        if citation_element:
            citation_text = citation_element.get_text(strip=True)
            citation_match = re.search(r'(\d+(?:,\d+)*)', citation_text)
            if citation_match:
                dataset_data['citation_count'] = citation_match.group(1).replace(',', '')
        
        # Find data format information
        format_element = soup.select_one('div:-soup-contains("Data Format")')
        if format_element:
            format_text = format_element.get_text(strip=True)
            format_match = re.search(r'Data Format[:\s]*([^\.]+)', format_text, re.IGNORECASE)
            if format_match:
                dataset_data['data_format'] = clean_text(format_match.group(1))
        
        # Find similar benchmarks
        similar_section = soup.select_one('section:-soup-contains("Similar Datasets")')
        if similar_section:
            similar_links = similar_section.select('a[href*="/datasets/"]')
            if similar_links:
                similar_benchmarks = [link.get_text(strip=True) for link in similar_links[:5]]  # Get up to 5 similar benchmarks
                dataset_data['similar_benchmarks'] = ', '.join(similar_benchmarks)
        
        # Find example code links
        code_links = soup.select('a[href*="github.com"]')
        if code_links:
            for link in code_links:
                href = link.get('href', '')
                if 'example' in href.lower() or 'code' in href.lower() or 'implementation' in href.lower():
                    dataset_data['example_code_link'] = href
                    break
        
        # Find SOTA model information
        sota_element = soup.select_one('div:-soup-contains("State-of-the-Art") strong, div:-soup-contains("SOTA") strong')
        if sota_element:
            dataset_data['sota_model'] = clean_text(sota_element.get_text(strip=True))
        
        # Find dataset card for additional information
        dataset_card = soup.select_one('div[class*="dataset-card"]')
        if dataset_card:
            # Look for task tags
            task_tags = dataset_card.select('span[class*="tag"]')
            if task_tags:
                task_texts = [tag.get_text(strip=True).lower() for tag in task_tags]
                
                # Determine task type from tags
                if any('classification' in tag for tag in task_texts):
                    dataset_data['task_type'] = 'Classification'
                elif any('question' in tag for tag in task_texts):
                    dataset_data['task_type'] = 'Question Answering'
                elif any('summarization' in tag for tag in task_texts):
                    dataset_data['task_type'] = 'Summarization'
                elif any('translation' in tag for tag in task_texts):
                    dataset_data['task_type'] = 'Translation'
                elif any('sentiment' in tag for tag in task_texts):
                    dataset_data['task_type'] = 'Sentiment Analysis'
        
        # Fill in evaluation metrics based on task type if not already present
        if dataset_data['task_type'] and not dataset_data['evaluation_metrics']:
            task_type = dataset_data['task_type']
            if task_type in EVALUATION_METRICS_BY_TASK:
                dataset_data['evaluation_metrics'] = EVALUATION_METRICS_BY_TASK[task_type]
        
        # Fill in model architectures based on task type
        if dataset_data['task_type'] and not dataset_data['model_architectures']:
            task_type = dataset_data['task_type']
            if task_type in MODEL_ARCHITECTURES_BY_TASK:
                dataset_data['model_architectures'] = MODEL_ARCHITECTURES_BY_TASK[task_type]
    
    except Exception as e:
        logger.error(f"Error extracting information for {dataset_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return dataset_data

def extract_from_html_files():
    """
    Extract dataset information from all HTML files in the huggingface folder.
    
    Returns:
        List of dictionaries containing dataset metadata
    """
    logger.info("Extracting information from HTML files in the huggingface folder...")
    
    # Find all HTML files
    html_files = [f for f in os.listdir(DATASETS_DIR) if f.endswith('.html') and not f.startswith('huggingface_page_')]
    logger.info(f"Found {len(html_files)} HTML files")
    
    # Initialize list to store dataset information
    datasets = []
    
    # Track processed dataset names to avoid duplicates
    processed_datasets = set()
    
    for html_file in html_files:
        try:
            # Extract dataset name from filename
            filename = os.path.basename(html_file)
            
            # Handle different filename patterns
            if "huggingface_debug_" in filename:
                dataset_name = filename.replace("huggingface_debug_", "").replace(".html", "")
            elif "huggingface_" in filename:
                dataset_name = filename.replace("huggingface_", "").replace(".html", "")
            else:
                # For files without any prefix
                dataset_name = filename.replace(".html", "")
                
            # Skip if we've already processed this dataset
            if dataset_name in processed_datasets:
                logger.info(f"Skipping already processed dataset: {dataset_name}")
                continue
                
            logger.info(f"Processing {dataset_name} from {filename}")
            
            # Check file size to make sure it's not an error page
            file_path = os.path.join(DATASETS_DIR, html_file)
            file_size = os.path.getsize(file_path)
            if file_size < 5000:  # If file is too small, it might be an error page
                logger.warning(f"File {filename} is too small ({file_size} bytes), might be an error page. Skipping.")
                continue
            
            # Read HTML file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # Extract information from HTML content
            dataset_data = extract_dataset_info(dataset_name, html_content)
            
            # Add dataset to our list
            datasets.append(dataset_data)
            processed_datasets.add(dataset_name)
            logger.info(f"Added dataset: {dataset_data['benchmark_name']}")
            
        except Exception as e:
            logger.error(f"Error processing file {html_file}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info(f"Completed extracting information from HTML files. Found {len(datasets)} datasets.")
    return datasets

def save_to_csv(data, filename):
    """
    Save benchmark metadata to a CSV file.
    
    Args:
        data: List of dictionaries containing benchmark metadata
        filename: Name of the CSV file to save to
    """
    # Create csv directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=BENCHMARK_FIELDS)
        writer.writeheader()
        for item in data:
            # Create a new dict with only the fields we want to save
            filtered_item = {field: item.get(field, '') for field in BENCHMARK_FIELDS}
            writer.writerow(filtered_item)
    logger.info(f"Saved {len(data)} datasets to {filename}")

def main():
    """
    Main function to extract dataset information from HTML files and save to CSV.
    """
    # Create necessary directories
    os.makedirs(CSV_DIR, exist_ok=True)
    
    # Extract data from HTML files
    datasets = extract_from_html_files()
    
    # Save to CSV
    csv_path = os.path.join(CSV_DIR, CSV_FILENAME)
    save_to_csv(datasets, csv_path)
    logger.info(f"Completed extraction. Saved {len(datasets)} datasets to {csv_path}")

if __name__ == '__main__':
    main()
