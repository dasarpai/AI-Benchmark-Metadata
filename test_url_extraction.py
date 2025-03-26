import os
import re
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    
    print(f"\nExtracting URL for dataset: {dataset_name}")
    
    # Try to extract from the Open Graph URL (highest priority)
    og_url = soup.find('meta', property='og:url')
    if og_url and og_url.get('content'):
        url = og_url.get('content').strip()
        print(f"Found og:url (direct): {url}")
        return url
    
    # Try alternate ways to find the og:url meta tag
    for meta in soup.find_all('meta'):
        if meta.get('property') == 'og:url' and meta.get('content'):
            url = meta.get('content').strip()
            print(f"Found og:url (iterative): {url}")
            return url
    
    # Try to find the canonical URL in the meta tags
    canonical_link = soup.find('link', rel='canonical')
    if canonical_link and canonical_link.get('href'):
        url = canonical_link.get('href').strip()
        print(f"Found canonical link: {url}")
        return url
    
    # Try to find the dataset URL from breadcrumbs
    breadcrumbs = soup.select('ol.breadcrumb li a')
    for link in breadcrumbs:
        href = link.get('href', '')
        if '/dataset/' in href:
            url = "https://paperswithcode.com" + href
            print(f"Found breadcrumb link: {url}")
            return url
    
    # Look for any link that contains '/dataset/' in the href
    dataset_links = soup.select('a[href*="/dataset/"]')
    for link in dataset_links:
        href = link.get('href', '')
        if href.startswith('/'):
            url = "https://paperswithcode.com" + href
            print(f"Found relative dataset link: {url}")
            return url
        elif href.startswith('http'):
            print(f"Found absolute dataset link: {href}")
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
            url = f"https://paperswithcode.com/dataset/{dataset_slug}"
            print(f"Constructed URL from title: {url}")
            return url
    
    # Extract dataset name from file path as a last resort
    file_name = os.path.basename(file_path)
    if file_name.endswith('.html'):
        dataset_name = file_name[:-5]  # Remove .html extension
        url = f"https://paperswithcode.com/dataset/{dataset_name}"
        print(f"Constructed URL from filename: {url}")
        return url
    
    print(f"Could not extract URL for {file_path}")
    return ""

def main():
    # Test with a few files
    html_dir = "paperswithcode/consolidated"
    test_files = [
        "100STLYE-Labelled.html",
        "20000_utterances.html",
        "10_Synthetic_Genomics_Datasets.html",
        "10_000_People_-_Human_Pose_Recognition_Data.html",
        "105_941_Images_Natural_Scenes_OCR_Data_of_12_Langu.html"
    ]
    
    for file_name in test_files:
        file_path = os.path.join(html_dir, file_name)
        if os.path.exists(file_path):
            print(f"\n{'='*50}")
            print(f"Testing file: {file_path}")
            
            # Read HTML file
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract URL
            url = extract_pwc_url(soup, file_path)
            print(f"Final URL: {url}")
            
            # Print all meta tags for debugging
            print("\nAll meta tags with property attribute:")
            for meta in soup.find_all('meta'):
                if meta.get('property'):
                    print(f"  {meta.get('property')}: {meta.get('content')}")
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()
