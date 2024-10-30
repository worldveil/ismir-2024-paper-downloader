# ISMIR 2024 Paper Downloader

This script downloads papers from the ISMIR 2024 conference using the arXiv API.

Made with Claude 3.5 Sonnet in about 3 minutes, pardon the mess.

## Usage

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install arxiv

python download.py
# === Download Summary ===
# ✅ Successfully downloaded: 65 papers
# ❌ Failed downloads: 0 papers
# ❌ Not found: 59 papers
```

## Notes

`papers.txt` is just a brower select + copy paste from [ISMIR 2024 Accepted Papers](https://ismir2024.ircam.fr/accepted-papers/).

Currently not all papers are on Arxiv, and you'll find the missing ones in the `download_results.log` file after you run. I included mine from my run, but if you run yourself it will overwrite the file.

## Contributing

If you'd like to manually add any of the missing papers to help crowdsource, you can either copy paste the PDF web HTTP URL to somewhere in the title field of the paper.txt file for that entry (and the script will automatically download and rename it), or add the PDF manually to the `paper_downloads` directory. Either way make a PR, and I will happily accept!
