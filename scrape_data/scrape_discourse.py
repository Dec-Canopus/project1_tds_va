import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_URL = f"{BASE_URL}/c/courses/tds-kb/34"
OUTPUT_FILE = "data/discourse_forum.json"

MANUAL_COOKIES = {
    "_forum_session": os.getenv("_FORUM_SESSION"),
    "_t": os.getenv("_T")
}

START_DATE = datetime(2025, 1, 1).date()
END_DATE = datetime(2025, 5, 1).date()

def get_authenticated_session():
    session = requests.Session()
    session.cookies.update(MANUAL_COOKIES)
    print(session)
    return session

def extract_topic_urls(session, page_number):
    url = f"{CATEGORY_URL}?page={page_number}"
    res = session.get(url)
    if res.status_code != 200:
        print(f"❌ Failed to load page {page_number}")
        return []

    print(res.text)
    soup = BeautifulSoup(res.text, "html.parser")
    rows = soup.select("tr.topic-list-item")
    topics = []

    for row in rows:
        link = row.select_one("a.title.raw-link")
        if link and link.get("href", ""):
            topics.append({
                "title": link.text.strip(),
                "url": link["href"]
            })

    return topics

def fetch_post_json(session, post_url):
    json_url = f"{post_url}.json"
    res = session.get(json_url)
    if res.status_code == 200:
        return res.json()
    else:
        print(f"⚠️ Could not fetch {json_url}")
        return None
    
def is_valid_post(created_at_str, topic_slug):
    try:
        # Check created_at date
        if created_at_str:
            # created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            created_at_str = datetime.fromisoformat(created_at_str.replace("Z", ""))
            created_at_str = created_at_str.date()
            if START_DATE <= created_at_str <= END_DATE:
                return True
        # Fallback: Check topic_slug for "jan-2025"
        if topic_slug and "jan-2025" in topic_slug.lower():
            return True
    except Exception as e:
        print(e)
        print(f"⚠️ Date parse error: {created_at_str}")
    return False

def fetch_all_posts(session, topic):
    all_posts = []
    seen_post_numbers = set()
    post_number = 1
    posts_count = None

    def strip_html(html_string):
        soup = BeautifulSoup(html_string, "html.parser")
        return soup.get_text()

    while True:
        post_url = f"{topic['url']}/{post_number}"
        data = fetch_post_json(session, post_url)

        if not data:
            print("🚫 Failed to fetch:", post_url)
            break

        posts = data.get("post_stream", {}).get("posts", [])
        if not posts:
            print("⚠️ No posts in stream:", post_url)
            break

        created_at = data.get("created_at", "")
        slug = data.get("slug", "")
        # print(data)

        if is_valid_post(created_at_str=created_at, topic_slug=slug):
            for post in posts:
                pn = post.get("post_number")
                if pn not in seen_post_numbers:
                    all_posts.append({
                        "title": post.get("topic_slug", ""),
                        "url": BASE_URL + post.get("post_url", ""),
                        # "post_number": pn,
                        "content": strip_html(post.get("cooked", ""))
                    })
                    seen_post_numbers.add(pn)

            if posts_count is None and posts:
                posts_count = posts[0].get("posts_count")
            post_number = posts[-1].get("post_number")

            # print(posts[0].get("post_number"))

            if posts_count and len(seen_post_numbers) >= posts_count:
                print(f"✅ Fetched all available posts in {posts_count} posts for topic.")
                break
        else:
            break

    return sorted(all_posts, key=lambda x: x["url"])


def scrape_discourse_forum():
    session = get_authenticated_session()
    all_data = []

    for page in range(1, 3):
        print(f"📄 Scraping Page {page}")
        topics = extract_topic_urls(session, page)
        if not topics:
            print("❌ No Topics found")
            break

        for topic in topics:
            print(f"🧵 {topic['title']}")
            posts = fetch_all_posts(session, topic)
            all_data.extend(posts)

    save_data(all_data, OUTPUT_FILE)

def save_data(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(data)} posts to {path}")

if __name__ == "__main__":
    scrape_discourse_forum()
