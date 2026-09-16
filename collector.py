#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collector.py
প্রতিদিন GitHub Actions দিয়ে চলে — Google News RSS থেকে নির্দিষ্ট keyword সার্চ করে,
নতুন news খুঁজে বের করে, category/district ট্যাগ করে data/data.json এ জমা করে।

কোনো API key লাগে না (Google News RSS পাবলিক)।
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
import hashlib
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "data.json")

# ---- ১. যেসব keyword দিয়ে সার্চ হবে (দরকারমতো এখানে যোগ/বাদ দিতে পারবেন) ----
QUERIES = [
    "বিএনপি চাঁদাবাজি",
    "বিএনপি নেতা দখল",
    "বিএনপি বহিষ্কার চাঁদাবাজি",
    "বিএনপি সন্ত্রাস",
    "বিএনপি মামলা নেতা",
    "বিএনপি নেতা গ্রেফতার",
]

# ---- ২. ক্যাটাগরি চেনার জন্য keyword rule ----
CATEGORY_RULES = {
    "চাঁদাবাজি": ["চাঁদাবাজি", "চাঁদা দাবি", "চাঁদাবাজির"],
    "জমি দখল": ["জমি দখল", "দখল", "দখলবাজি", "ভূমি দখল"],
    "সন্ত্রাসী কর্মকাণ্ড": ["সন্ত্রাস", "হামলা", "ভাঙচুর", "মারধর"],
    "বহিষ্কার / দলীয় ব্যবস্থা": ["বহিষ্কার", "শোকজ", "অব্যাহতি"],
    "মামলা / গ্রেফতার": ["মামলা", "গ্রেফতার", "আটক"],
    "ঝুট ব্যবসা / চাঁদা": ["ঝুট ব্যবসা", "টেন্ডারবাজি"],
}

# ---- ৩. জেলার তালিকা (বাংলাদেশের ৬৪ জেলা) — headline-এ match করে district বের করা হয় ----
DISTRICTS = [
    "ঢাকা", "গাজীপুর", "নারায়ণগঞ্জ", "নরসিংদী", "মানিকগঞ্জ", "মুন্সিগঞ্জ",
    "টাঙ্গাইল", "কিশোরগঞ্জ", "ফরিদপুর", "গোপালগঞ্জ", "মাদারীপুর", "রাজবাড়ী",
    "শরীয়তপুর", "চট্টগ্রাম", "কক্সবাজার", "কুমিল্লা", "ফেনী", "নোয়াখালী",
    "লক্ষ্মীপুর", "চাঁদপুর", "ব্রাহ্মণবাড়িয়া", "খাগড়াছড়ি", "রাঙামাটি", "বান্দরবান",
    "রাজশাহী", "চাঁপাইনবাবগঞ্জ", "নাটোর", "নওগাঁ", "পাবনা", "সিরাজগঞ্জ",
    "বগুড়া", "জয়পুরহাট", "খুলনা", "যশোর", "সাতক্ষীরা", "বাগেরহাট", "নড়াইল",
    "ঝিনাইদহ", "মাগুরা", "কুষ্টিয়া", "চুয়াডাঙ্গা", "মেহেরপুর", "বরিশাল",
    "পটুয়াখালী", "ভোলা", "পিরোজপুর", "ঝালকাঠি", "বরগুনা", "সিলেট",
    "মৌলভীবাজার", "হবিগঞ্জ", "সুনামগঞ্জ", "রংপুর", "দিনাজপুর", "গাইবান্ধা",
    "কুড়িগ্রাম", "লালমনিরহাট", "নীলফামারী", "পঞ্চগড়", "ঠাকুরগাঁও", "ময়মনসিংহ",
    "জামালপুর", "নেত্রকোণা", "শেরপুর",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BNPMonitorBot/1.0)"}


def fetch_rss(query: str):
    """Google News RSS থেকে একটা query-র জন্য news item list আনে।"""
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=bn&gl=BD&ceid=BD:bn"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
    except Exception as e:
        print(f"[warn] fetch failed for '{query}': {e}")
        return []

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print(f"[warn] parse failed for '{query}': {e}")
        return []

    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else "Google News"
        if not title or not link:
            continue
        items.append({"title": title, "link": link, "pub_date": pub_date, "source": source})
    return items


def parse_pubdate(pub_date: str) -> str:
    """RSS pubDate কে YYYY-MM-DD ফরম্যাটে আনে; ব্যর্থ হলে আজকের তারিখ দেয়।"""
    try:
        dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return datetime.now(timezone(timedelta(hours=6))).strftime("%Y-%m-%d")


def detect_categories(text: str):
    found = []
    for cat, keywords in CATEGORY_RULES.items():
        if any(kw in text for kw in keywords):
            found.append(cat)
    return found or ["অশ্রেণীবদ্ধ"]


def detect_district(text: str):
    for d in DISTRICTS:
        if d in text:
            return d
    return "অজ্ঞাত"


def make_id(link: str) -> str:
    return "n" + hashlib.md5(link.encode("utf-8")).hexdigest()[:10]


def load_existing():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated": "", "queries": QUERIES, "items": []}


def save(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    data = load_existing()
    existing_ids = {item["id"] for item in data["items"]}
    new_count = 0

    for q in QUERIES:
        for raw in fetch_rss(q):
            item_id = make_id(raw["link"])
            if item_id in existing_ids:
                continue
            text = raw["title"]
            entry = {
                "id": item_id,
                "date": parse_pubdate(raw["pub_date"]),
                "district": detect_district(text),
                "leader": "",  # ম্যানুয়ালি যাচাই করে পরে বসানো যাবে
                "position": "",
                "category": detect_categories(text),
                "status": "অভিযোগ (যাচাই বাকি)",
                "headline": text,
                "source": raw["source"],
                "url": raw["link"],
            }
            data["items"].append(entry)
            existing_ids.add(item_id)
            new_count += 1

    data["last_updated"] = datetime.now(timezone(timedelta(hours=6))).isoformat()
    data["queries"] = QUERIES
    # সবচেয়ে নতুন আগে
    data["items"].sort(key=lambda x: x["date"], reverse=True)
    save(data)
    print(f"[done] {new_count} টি নতুন news যোগ হয়েছে। মোট: {len(data['items'])}")


if __name__ == "__main__":
    main()
