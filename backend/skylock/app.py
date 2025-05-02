from fastapi import FastAPI

from skylock.pages.page_router import html_handler
from skylock.api.app import api

app = FastAPI()


app.mount("/api/v1", api)
app.mount("/", html_handler)
