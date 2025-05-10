from playwright.sync_api import sync_playwright
import json

COOKIES_PATH = "cookies.json"
BASE_URL = "https://cursoriesgoslaborales.com/lecciones/introduccion-al-curso-de-prevencion-de-riesgos-laborales/"
BASE_URL_QUIRON_PREVENCION = "https://campus.quironprevencion.com/FrontEnd/MyCampus.aspx"

with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)  # Use chromium instead of firefox
    context = browser.new_context()
    page = context.new_page()
    page.goto(BASE_URL)
    cookies = context.cookies()
    with open(COOKIES_PATH, "w",encoding="utf-8") as f:
        json.dump(cookies, f)
    browser.close()