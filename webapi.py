from fastapi import FastAPI
from webapp import main
from enum import Enum

class Site(str, Enum):
    """Specify which site to scrape"""
    business = 'business'
    personal = 'personal'

class Command(str, Enum):
    """Scrape will only get the 1st result from the search term, 
    while scan will gather as much information outside as possible without ever going into details"""
    scrape = 'scrape'
    scan = 'scan'
    scrape_all = 'scrape_all'

class SearchTerms(Enum):
    """Search terms corresponding to its associated field"""
    TaxNumber = 'TaxNumber'
    Name = 'Name'
    Address = 'Address'
    IdNumber = 'IdNumber'

app = FastAPI()

@app.get(r'/api/v1/{site}/{command}')
async def scrape_record(site: Site, command: Command, term: SearchTerms, value):
    return main(site.value, command.value, term.value, value)
