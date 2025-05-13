from pathlib import Path
import os
from playwright.sync_api import sync_playwright
import json
import time
import re
from PIL import Image
import pytesseract

BASE_URL = "https://cursoriesgoslaborales.com"
COURSE_URL = f"{BASE_URL}/lecciones/introduccion-al-curso-de-prevencion-de-riesgos-laborales/"
COOKIES_PATH = "cookies.json"
OUTPUT_DIR = Path("cursoriesgoslaborales")
IMG_DIR = OUTPUT_DIR / "images"
TEXT_DIR = OUTPUT_DIR / "texts"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def sanitize_filename_for_image(title):
    return re.sub(r'[ ,]', "_", title).lower()
def clean_course_text(text):
    matches = re.findall(r'minutos\s*(.*?)(?=Lección|\Z)', text, re.DOTALL)
    return "".join([t.strip() for idx, t in enumerate(matches, 1)])

def extract_text_from_image(image):
    return pytesseract.image_to_string(Image.open(image))

def scrape_courses():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        if not os.path.exists(COOKIES_PATH):
            print("cookies.json doesn't exist")
            return
        with open(COOKIES_PATH, "r", encoding="utf-8") as f:
            context.add_cookies(json.load(f))

        page = context.new_page()
        page.goto(COURSE_URL)
        page.wait_for_selector("div#contenido")
        time.sleep(2)

        lesson_links = page.query_selector_all("ul#lessonNav li:not(.disabled) > a")
        lessons = []
        for link in lesson_links:
            title = link.get_attribute("data-original-title").strip().replace("\n", " ")
            href = link.get_attribute("href")
            lessons.append({"title": title, "href": href})
        print(f"Founds {len(lessons)} lessons")
        # lessons = lessons[6:7]

        for lesson_idx, lesson in enumerate(lessons):
            lesson_title = sanitize_filename(lesson["title"])
            lesson_url = f"{BASE_URL}{lesson['href']}"
            page.goto(lesson_url)
            page.wait_for_selector("body")
            time.sleep(2)

            lesson_text = page.evaluate("""
                () => {
                    function convert_html_table(tableNode) {
                        const rows = Array.from(tableNode.querySelectorAll('tr'));
                        if (rows.length === 0) return '';
                        const table = rows.map(row => {
                            const cells = row.querySelectorAll('th, td');
                            return Array.from(cells).map(cell => cell.innerText.trim());
                        });
                        let markdown = '| ' + table[0].join(' | ') + ' |\\n';
                        markdown += '| ' + table[0].map(col => '-'.repeat(col.length)).join(' | ') + ' |\\n';
                
                        for (let i = 1; i < table.length; i++) {
                            markdown += '| ' + table[i].join(' | ') + ' |\\n';
                        }
                        return markdown;
                    }
                    let main = document.querySelectorAll('#short, #long');
                    if (!main) main = document.body;
                    const nodeLists = Array.from(main).map(i => i.querySelectorAll('p, h2, h3, h4, ol, ul, table'));
                    return nodeLists.flatMap(list => Array.from(list)).map(node => {
                        if (node.tagName === "TABLE") {
                            return convert_html_table(node);
                        } else {
                            return node.innerText;
                        }
                    }).filter(Boolean).join('\\n\\n');
                }
            """)
            # print(f"lesson text: {lesson_text}")
            # Remove a line "Lección X: resumen | X minutos"
            lesson_text = clean_course_text(lesson_text)
            # print(f"lesson text: {lesson_text}")
            image_elements = page.query_selector_all("img.img-fluid")
            image_elements = image_elements[2:]
            image_md = []
            ocr_md = []
            for img_idx, img_elem in enumerate(image_elements):
                try:
                    box = img_elem.bounding_box()
                    if not box or box['width'] < 1000 or box['height'] == 0:
                        print(f"Skipping invisible or small image {img_idx}")
                        continue
                    img_title = sanitize_filename_for_image(lesson_title)
                    img_filename = f"{img_title}_lesson_{lesson_idx:02d}_img_{img_idx}.png"
                    img_path = IMG_DIR / img_filename
                    img_elem.screenshot(path=str(img_path))
                    image_md.append(f"![img](../images/{img_filename})")
                    extracted = extract_text_from_image(img_path)
                    if extracted:
                        ocr_md.append(f"### Image {img_idx}\n\n{extracted}")
                    else:
                        if os.path.exists(img_path):
                            os.remove(img_path)
                        image_md.pop()

                except Exception as e:
                    print(f"Failed to screenshot or OCR image: {img_filename} - {e}")
            filename = f"{lesson_title}.md"
            with open(f"{TEXT_DIR}/{filename}", "w", encoding="utf-8") as f:
                f.write(f"# {lesson_title}\n\n")
                f.write(f"URL: {lesson_url}\n\n")
                f.write("## Main content\n\n")
                f.write(lesson_text + "\n\n")
                if image_md:
                    f.write("## Images\n\n")
                    f.write("\n\n".join(image_md) + "\n\n")
                if ocr_md:
                    f.write("## Image OCR Text\n\n")
                    f.write("\n\n".join(ocr_md))
            print(f"Saved: {filename}")

if __name__ == "__main__":
    scrape_courses()