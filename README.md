# AI Benchmark Metadata Scraper

This tool scrapes metadata about multimodal AI benchmarks from websites like HuggingFace Datasets and PapersWithCode, and saves the data to a CSV file.

## Features

- Scrapes benchmark metadata from multiple sources
- Extracts key information such as:
  - Benchmark name
  - Modality (e.g., Image, Text, Video)
  - Task Type (e.g., VQA, OCR, Reasoning)
  - Domain (e.g., Scientific, UI, Document, General)
  - Output Type (e.g., Text, Action, Label)
  - Evaluation Metrics (e.g., Accuracy, EM, F1, mIoU)
  - Paper link
  - Dataset link
- Saves data to CSV format
- Includes error handling and retry mechanisms
- Uses rotating user-agent headers to avoid blocking
- Easily extendable to add more websites

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with:

```bash
python benchmark_scraper.py
```

The script will:
1. Scrape benchmark metadata from PapersWithCode
2. Scrape benchmark metadata from HuggingFace Datasets
3. Save all collected data to `benchmark_metadata.csv`

## Extending the Scraper

To add support for a new website:

1. Create a new function following the pattern of `scrape_paperswithcode()` or `scrape_huggingface_datasets()`
2. Implement the website-specific scraping logic
3. Add a call to your new function in the `main()` function
4. Extend the results to the `all_benchmarks` list

## License

MIT
