# INSTALLATION AND USAGE GUIDE
1. Install conda (https://docs.conda.io/en/latest/miniconda.html) if not already installed
2. Create a new conda environment  
`conda create -n your-new-env tensorflow-gpu pip`  
This is the easiest way to enable GPU support for tensorflow.
3. Install the requirements with 
`pip install requirements.txt`
4. Run the program from command line `python tct.py -h` 
5. Supported command:
    1. `scrape`: return search, scrape the outer summary table, then **go to the 1st record** and scrape every tables, including ones hidden inside `...` at the bottom of the page.
    2. `scan`: return search, scrape the outer summary table, then **go to next page** and scrape the summary... repeat up to 9 pages (site doesn't return anything from page 10 onward)
    3. `scrape_all`: perform `scan` over search terms. Then, perform `scrape` over each **MST** found in `scan`
5. **TNCN Tab** is not supported yet

# STATISITCS
- The captcha solver engine achieves 98% accuracy over the whole set (5-char), or 99.5% for each char
- `scrape` takes on average 0.5 second to know if the record is empty, and extra 1.5 (to the total of 2 seconds) to scrape both **outer** and **inner** tables.
- `scan` takes on average 0.5 second to scan and scrape a single page

# EXAMPLES
Below are expected log of 3 correctly-running program
```
(test) .\TracuuNNT_main>python tct.py scrape 030344323 .\output\scrape
2020-11-06 10:44:07,767 : INFO : TracuuNNT : Initialising webdriver...
2020-11-06 10:44:12,378 : INFO : TracuuNNT.WebDriver : Loading solver at .\solver\CNN5_v10_acc_98.h5
2020-11-06 10:44:13,536 : INFO : TracuuNNT : Start scraping...
2020-11-06 10:44:13,536 : INFO : TracuuNNT.WebDriver : Scraping single record... Provided search terms={'TaxNumber': '030344323'}
2020-11-06 10:44:18,354 : INFO : TracuuNNT.WebDriver : Finished scraping. Record is present.
2020-11-06 10:44:18,354 : INFO : TracuuNNT : Finished scraping.
2020-11-06 10:44:19,391 : INFO : TracuuNNT : Finished writing to output\scrape\result.json.

(test) .\TracuuNNT_main>python tct.py scrape_all 030344323 .\output\scrape_all
2020-11-06 10:44:40,190 : INFO : TracuuNNT : Initialising webdriver...
2020-11-06 10:44:45,127 : INFO : TracuuNNT.WebDriver : Loading solver at .\solver\CNN5_v10_acc_98.h5
2020-11-06 10:44:46,216 : INFO : TracuuNNT : Start scraping...
2020-11-06 10:44:46,216 : INFO : TracuuNNT.WebDriver : Scanning for possible records... Provided search terms={'TaxNumber': '030344323'}
2020-11-06 10:44:49,160 : INFO : TracuuNNT.WebDriver : Finished scanning. 3 records found
2020-11-06 10:44:49,161 : INFO : TracuuNNT.WebDriver : Scraping single record... Provided search terms={'TaxNumber': '0303443233'}
2020-11-06 10:44:51,447 : INFO : TracuuNNT.WebDriver : Finished scraping. Record is present.
2020-11-06 10:44:51,447 : INFO : TracuuNNT.WebDriver : Scraping single record... Provided search terms={'TaxNumber': '0303443233-001'}
2020-11-06 10:44:53,707 : INFO : TracuuNNT.WebDriver : Finished scraping. Record is present.
2020-11-06 10:44:53,707 : INFO : TracuuNNT.WebDriver : Scraping single record... Provided search terms={'TaxNumber': '0303443233-002'}
2020-11-06 10:44:55,967 : INFO : TracuuNNT.WebDriver : Finished scraping. Record is present.
2020-11-06 10:44:55,967 : INFO : TracuuNNT : Finished scraping.
2020-11-06 10:44:56,942 : INFO : TracuuNNT : Finished writing to output\scrape_all\result.json.

(test) .\TracuuNNT_main>python tct.py scan 030344323 .\output\scan
2020-11-06 10:45:10,218 : INFO : TracuuNNT : Initialising webdriver...
2020-11-06 10:45:15,102 : INFO : TracuuNNT.WebDriver : Loading solver at .\solver\CNN5_v10_acc_98.h5
2020-11-06 10:45:16,228 : INFO : TracuuNNT : Start scraping...
2020-11-06 10:45:16,228 : INFO : TracuuNNT.WebDriver : Scanning for possible records... Provided search terms={'TaxNumber': '030344323'}
2020-11-06 10:45:19,119 : INFO : TracuuNNT.WebDriver : Finished scanning. 3 records found
2020-11-06 10:45:19,120 : INFO : TracuuNNT : Finished scraping.
2020-11-06 10:45:19,680 : INFO : TracuuNNT : Finished writing to output\scan\result.json.
```
