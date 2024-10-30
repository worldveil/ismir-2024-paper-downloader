import re
import os
from urllib.error import URLError
from urllib.request import urlretrieve
from pathlib import Path
import time
from difflib import SequenceMatcher
import requests

import arxiv

WAIT_TIME_SECS = 3
MAX_RESULTS = 10
DEFAULT_SIMILARITY_THRESHOLD = 0.8

def extract_url_and_title(title_text: str) -> tuple[str | None, str]:
    """
    Extract URL and clean title from a title string.
    Returns tuple of (url, clean_title) where url may be None.
    """
    # Match URLs in the title
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+\.[^\s<>"]+'
    match = re.search(url_pattern, title_text)
    
    if match:
        url = match.group(0)
        # Remove the URL from the title and clean up
        clean_title = re.sub(url_pattern, '', title_text).strip()
        return url, clean_title
    
    return None, title_text

def download_from_url(url: str, filepath: Path) -> bool:
    """
    Download a PDF from a direct URL.
    Returns True if successful, False otherwise.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Check if it's actually a PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type:
            print(f"❌ URL does not point to a PDF: {url}")
            return False
            
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"❌ Error downloading from URL {url}: {str(e)}")
        return False

def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate similarity ratio between two titles after normalization.
    """
    # Normalize titles for comparison
    def normalize_title(title):
        # Convert to lowercase
        title = title.lower()
        # Remove special characters and extra whitespace
        title = re.sub(r'[^\w\s]', '', title)
        # Replace multiple spaces with single space
        title = re.sub(r'\s+', ' ', title)
        return title.strip()
    
    normalized_title1 = normalize_title(title1)
    normalized_title2 = normalize_title(title2)
    
    return SequenceMatcher(None, normalized_title1, normalized_title2).ratio()

def sanitize_filename(title: str) -> str:
    """Convert title to a valid filename."""
    # Remove invalid filename characters
    clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace spaces with underscores
    clean_title = clean_title.replace(' ', '_')
    # Limit filename length
    return clean_title[:240] + '.pdf'

def download_papers(titles, similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD):
    """
    Search for and download papers from arXiv based on titles.
    
    Args:
        titles (list): List of paper titles to search for
        similarity_threshold (float): Minimum similarity ratio required to accept a paper match
    """
    # Create downloads directory if it doesn't exist
    download_dir = Path('paper_downloads')
    download_dir.mkdir(exist_ok=True)
    
    # Keep track of results
    successful_downloads = []
    failed_downloads = []
    title_mismatches = []
    
    for title_text in titles:
        # Check for URL in title
        url, title = extract_url_and_title(title_text)
        
        if url:
            print(f"\nDownloading from URL: {url}")
            filename = sanitize_filename(title)
            filepath = download_dir / filename
            
            if filepath.exists():
                print(f"✅ Skipping download of {filename} because it already exists")
                successful_downloads.append(f"{title} (URL: {url})")
                continue
                
            if download_from_url(url, filepath):
                print(f"✅ Successfully downloaded: {filename}")
                successful_downloads.append(f"{title} (URL: {url})")
                time.sleep(WAIT_TIME_SECS)
                continue
            else:
                failed_downloads.append(f"{title} (URL: {url})")
                continue
        
        try:
            # Clean up title for search
            search_title = title.replace(':', ' ').replace('-', ' ')
            print(f"\nSearching for: {title}")
            
            # Search arXiv with more results to find better matches
            search = arxiv.Search(
                query=search_title,
                max_results=MAX_RESULTS,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            # Try to find the best matching paper
            best_match = None
            best_similarity = 0
            
            try:
                for paper in search.results():
                    similarity = calculate_title_similarity(title, paper.title)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = paper
                
                if best_match is None or best_similarity < similarity_threshold:
                    print(f"❌ No sufficiently similar match found for: {title}")
                    title_mismatches.append(f"{title}")
                    continue
                
                # Create filename from original title
                filename = sanitize_filename(title)
                filepath = download_dir / filename
                if filepath.exists():
                    print(f"✅ Skipping download of {filename} because it already exists")
                    successful_downloads.append(f"{title} (ArXiv title: {best_match.title})")
                    continue
                
                # Download the paper
                try:
                    best_match.download_pdf(filename=filepath)
                    print(f"✅ Successfully downloaded: {filename}")
                    print(f"Match similarity: {best_similarity:.2f}")
                    successful_downloads.append(f"{title} (ArXiv title: {best_match.title})")
                    time.sleep(WAIT_TIME_SECS)
                except URLError as e:
                    print(f"❌ Failed to download {title}: {str(e)}")
                    failed_downloads.append(title)
                    
            except StopIteration:
                print(f"No results found for: {title}")
                continue
                
        except Exception as e:
            print(f"Error processing {title}: {str(e)}")
            failed_downloads.append(title)
    
    # Print summary
    print("\n=== Download Summary ===")
    print(f"✅ Successfully downloaded: {len(successful_downloads)} papers")
    print(f"❌ Failed downloads: {len(failed_downloads)} papers")
    print(f"❌ Not found: {len(title_mismatches)} papers")
    
    # Write detailed results to a log file
    with open('download_results.log', 'w') as f:
        f.write("=== Successfully Downloaded ===\n")
        f.write("\n".join(successful_downloads))
        f.write("\n\n=== Failed Downloads ===\n")
        f.write("\n".join(failed_downloads))
        f.write("\n\n=== Not found / title mismatches ===\n")
        f.write("\n".join(title_mismatches))

# Load papers from file
with open('papers.txt', 'r') as file:
    input_text = file.read()

# Extract titles
titles = [
    line.split('\t')[0].strip() 
    for line in input_text.split('\n') 
    if line.strip() and 'Paper Title' not in line
]

# Run the downloader
if __name__ == "__main__":
    download_papers(titles, similarity_threshold=0.8)