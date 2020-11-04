# INSTALLATION AND USAGE GUIDE
1. Install conda (https://docs.conda.io/en/latest/miniconda.html) if not already installed
2. Create a new conda environment  
`conda create -n your-new-env tensorflow-gpu pip`  
This is the easiest way to enable GPU support for tensorflow.
3. Install the requirements  
`pip install requirements.txt`
4. Modify and run `main.py` to start the program. Supported command:
    1. `scrape`: return search, scrape the outer summary table, then **go to the 1st record** and scrape every tables, including ones hidden inside `...` at the bottom of the page.
    2. `scan`: return search, scrape the outer summary table, then **go to next page** and scrape the summary... repeat up to 9 pages (site doesn't return anything from page 10 onward)
    3. `scrape_all`: perform `scan` over search terms. Then, perform `scrape` over each **MST** found in `scan`
5. **TNCN Tab** is not supported yet

# STATISITCS
- The captcha solver engine achieves 98% accuracy over the whole set (5-char), or 99.5% for each char
- `scrape` takes on average 0.5 second to know if the record is empty, and extra 1.5 (to the total of 2 seconds) to scrape both **outer** and **inner** tables.
- `scan` takes on average 0.5 second to scan and scrape a single page
