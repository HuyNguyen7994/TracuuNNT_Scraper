from fastapi import FastAPI
from webapp import main

app = FastAPI()

@app.get(r'/get_business')
async def scrape_business_record(command, term_value):
    return main('business', command, term_value)

@app.get(r'/get_personal')
async def scrape_personal_record(command, term_value):
    return main('personal', command, term_value)

