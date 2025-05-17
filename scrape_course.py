from pathlib import Path
import os
from playwright.sync_api import sync_playwright
import time
import re
from PIL import Image
import pytesseract
import argparse
from urllib.parse import urlparse

KNOWLEDGE_FOLDER = "knowledge_content"

COURSES = {
    "basic": "https://cursoriesgoslaborales.com/lecciones/introduccion-al-curso-de-prevencion-de-riesgos-laborales/",
    "advanced": "https://cursoprl60.com/lecciones/introduccion-al-curso-de-prevencion-de-riesgos-laborales/"
}
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def sanitize_filename_for_image(title):
    return re.sub(r'[ ,]', "_", title).lower()

def clean_course_text(text):
    matches = re.findall(r'minutos\s*(.*?)(?=Lección|\Z)', text, re.DOTALL)
    return "".join([t.strip() for idx, t in enumerate(matches, 1)])

def extract_text_from_image(image):
    return pytesseract.image_to_string(Image.open(image))

def scrape_course(type):
    course_url = urlparse(COURSES[type])
    BASE_URL = f"{course_url.scheme}://{course_url.netloc}"
    COURSE_URL = f"{BASE_URL}{course_url.path}"
    knowledge_content = Path(KNOWLEDGE_FOLDER)
    OUTPUT_DIR = knowledge_content / type
    IMG_DIR = OUTPUT_DIR / "images"
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    knowledge_content.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
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
            # Remove a line "Lección X: resumen | X minutos"
            lesson_text = clean_course_text(lesson_text)
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
                    image_md.append(f"![img](images/{img_filename})")
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
            with open(f"{OUTPUT_DIR}/{filename}", "w", encoding="utf-8") as f:
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", choices=["basic", "advanced"], default="basic")
    args = parser.parse_args()
    scrape_course(args.course)