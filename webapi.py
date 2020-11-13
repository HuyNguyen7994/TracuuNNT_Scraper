from fastapi import FastAPI
from webapp import main
from enum import Enum

class Site(str, Enum):
    business = 'business'
    personal = 'personal'

class Command(str, Enum):
    scrape = 'scrape'
    scan = 'scan'
    scrape_all = 'scrape_all'

class SearchTerms(Enum):
    TaxNumber = 'TaxNumber'
    Name = 'Name'
    Address = 'Address'
    IdNumber = 'IdNumber'

app = FastAPI()

@app.get(r'/api/v1/{site}/{command}')
async def scrape_record(site: Site, command: Command, term: SearchTerms, value):
    return main(site.value, command.value, term.value, value)
