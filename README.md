# নজরদারি — স্বয়ংক্রিয় নিউজ মনিটরিং ড্যাশবোর্ড

Google News থেকে প্রতিদিন স্বয়ংক্রিয়ভাবে নির্দিষ্ট keyword-এর news সংগ্রহ করে, ক্যাটাগরি/জেলা অনুযায়ী শ্রেণীবদ্ধ করে একটা live dashboard-এ দেখায়। সম্পূর্ণ ফ্রি (GitHub Actions + GitHub Pages)।

## সেটআপ (একবারের কাজ, ৫-১০ মিনিট)

### ধাপ ১ — GitHub-এ Repository বানান
1. https://github.com এ গিয়ে অ্যাকাউন্ট বানান (না থাকলে)
2. উপরে ডান দিকে **"+"** → **"New repository"**
3. নাম দিন (যেমন `bnp-monitor`), **Public** বা **Private** যেকোনোটা বাছাই করুন
4. "Create repository" চাপুন

### ধাপ ২ — ফাইলগুলো আপলোড করুন
1. নতুন repo পেজে **"uploading an existing file"** লিংকে ক্লিক করুন
2. এই zip-এর ভেতরের **সব ফাইল ও ফোল্ডার** (index.html, collector.py, data/, .github/) ঠিক একই ফোল্ডার-কাঠামো বজায় রেখে drag-drop করুন
   - খেয়াল রাখুন: `.github/workflows/update.yml` ফাইলটা `.github/workflows/` ফোল্ডারের ভেতরেই থাকতে হবে
   - সহজ উপায়: GitHub Desktop অ্যাপ ব্যবহার করলে পুরো ফোল্ডার একসাথে push করা যায়
3. "Commit changes" চাপুন

### ধাপ ৩ — GitHub Pages চালু করুন
1. Repo-র **Settings** ট্যাবে যান
2. বাম পাশে **Pages** এ ক্লিক করুন
3. "Source" এ **"Deploy from a branch"** বাছাই করুন, branch = **main**, folder = **/ (root)**
4. Save করুন — কিছুক্ষণ পর একটা লিংক পাবেন (যেমন `https://<username>.github.io/bnp-monitor/`)

### ধাপ ৪ — Actions চালু আছে কিনা দেখুন
1. Repo-র **Actions** ট্যাবে যান
2. "Daily News Update" workflow দেখতে পাবেন
3. প্রথমবার নিজে থেকে test করতে চাইলে workflow-এর ভেতরে গিয়ে **"Run workflow"** বাটনে ক্লিক করুন
4. এরপর থেকে এটা প্রতিদিন বাংলাদেশ সময় সকাল ৮টায় নিজে থেকে চলবে

ব্যাস — এখন থেকে প্রতিদিন data নিজে থেকে আপডেট হবে, আপনাকে কিছু করতে হবে না। শুধু লিংকে ঢুকে দেখবেন।

## কীভাবে কাজ করে
- `collector.py` — Google News RSS থেকে keyword সার্চ করে, নতুন news পেলে `data/data.json`-এ যোগ করে (পুরনো data মুছে না, শুধু নতুন যোগ হয়)
- `.github/workflows/update.yml` — GitHub-এর নিজস্ব সার্ভারে প্রতিদিন `collector.py` চালায় এবং updated `data.json` repo-তে commit করে
- `index.html` — সেই `data.json` পড়ে dashboard আকারে দেখায় (charts, trend, warnings, recommendations)

## নিজের মতো বদলাতে চাইলে
- **Keyword বদলানো/যোগ করা:** `collector.py`-তে উপরের দিকে `QUERIES` লিস্ট এডিট করুন
- **ক্যাটাগরি রুল বদলানো:** `CATEGORY_RULES` ডিকশনারি এডিট করুন
- **Schedule সময় বদলানো:** `.github/workflows/update.yml`-এ `cron` লাইনটা বদলান (UTC সময়ে লিখতে হয়)
- **নেতার নাম/পদবি সঠিক করে বসানো:** প্রতিটা news auto-collect হওয়ার পর `leader` ও `position` ফিল্ড খালি থাকে (auto-detect অনির্ভরযোগ্য বলে ইচ্ছাকৃতভাবে ফাঁকা রাখা হয়েছে) — চাইলে সরাসরি GitHub-এ `data/data.json` এডিট করে ম্যানুয়ালি বসিয়ে দিতে পারেন

## সীমাবদ্ধতা (honestly বলে রাখছি)
- Google News RSS নির্ভরযোগ্য কিন্তু সব খবর কভার করবে না; নির্দিষ্ট কিছু ওয়েবসাইট RSS-এ কম আসে
- জেলা-শনাক্তকরণ rule-based — মাঝে মাঝে ভুল/miss হতে পারে
- সিস্টেম চালু হওয়ার আগের কোনো তারিখের data automatically পাওয়া যাবে না (Google News পুরনো history দেয় না) — শুধু আজ থেকে সামনের দিকে data জমবে
- YouTube বা অন্য source যোগ করতে চাইলে collector.py-তে নতুন fetch function লিখে যোগ করতে হবে
