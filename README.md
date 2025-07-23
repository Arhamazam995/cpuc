# CPUC Scraper

A Scrapy-based web scraper to extract docket-level proceeding data, filings, and downloadable documents from the California Public Utilities Commission (CPUC).
## Features

- Scrape proceeding metadata including staff, industry, status, and parties
- Extract detailed filings and associated documents
- Supports date filtering using datefrom and dateto parameters
- Automatically paginates search results and fetches all related documents

## Getting Started

### Prerequisites

- Python (version 3.13) "https://www.python.org/downloads/"
- pip (version 25.1.1) "https://packaging.python.org/tutorials/installing-packages/"
- Git "https://github.com/"

### Installation

1. Clone the repository:

- git clone https://github.com/Arhamazam995/cpuc
- cd cpuc

2.(Optional) Create and activate a virtual environment:

- python -m venv venv
- source venv/bin/activate

3.Install dependencies:

- pip install -r requirements.txt
- create virtual environment 
- setup your virtual environment 
- active your virtual environment

### Usage

- run this command "scrapy crawl cpuc -a datefrom=01/01/2023 -a dateto=12/31/2023 -o output.json"
- datefrom: Start date for filtering proceedings (format: MM/DD/YYYY)
- dateto: End date for filtering proceedings
- -o: Output format (e.g., JSON, CSV)

### Output data

Each scraped item contains detailed information about a CPUC docket, including filings and documents. See Data Fields below.

###  Data field

#### 🧾 Docket-Level

- assignees
- filled on
- crawled at
- industries
- major parties
- proceeding type
- slug
- source title
- source url 
- status 
- title 
- spider name 
- start_time 
- state 
- state id

📑 Filings

- filed_on
- description
- type 
- filing_parties 
- source_filing_parties 
- state_id 
- document (list of related files)

📎 Document Details
 
- blob_name 
- extension 
- name 
- source_url 
- title