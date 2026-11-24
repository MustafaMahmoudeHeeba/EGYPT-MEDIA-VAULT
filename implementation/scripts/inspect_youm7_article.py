import sys
from pathlib import Path

from bs4 import BeautifulSoup

# Add project root to Python path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from pipeline.egypt_media_vault.scrapers.http_client import HttpClient


URL = (
    "https://www.youm7.com/story/2026/11/19/"
    "فيفا-يعلن-إيقاف-قيد-نادي-مودرن-سبورت/7624719"
)


html = HttpClient().get(URL)

print("HTML length:", len(html))


soup = BeautifulSoup(html, "html.parser")


print("\n===== TITLE =====")

print(
    soup.title.get_text(strip=True)
    if soup.title
    else "NOT FOUND"
)


print("\n===== META TAGS =====")

for meta in soup.find_all("meta"):

    name = meta.get("name")
    property_name = meta.get("property")
    content = meta.get("content")

    if name or property_name:
        print(
            f"name={name!r} "
            f"property={property_name!r} "
            f"content={content!r}"
        )


print("\n===== JSON-LD =====")

for script in soup.find_all(
    "script",
    type="application/ld+json",
):
    print(script.get_text(strip=True)[:3000])