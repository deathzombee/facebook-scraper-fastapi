# 📘 Facebook Friends Scraper API

This project is a FastAPI-based web service that scrapes a user's Facebook friend list and their friends' list using valid session cookies (`c_user`, `xs`) via Selenium.

⚠️ **Disclaimer**: This project is for educational purposes only. Scraping Facebook may violate their [Terms of Service](https://www.facebook.com/legal/terms).

---

## 🚀 Features

- Login using Facebook cookies (no username/password needed)
- Fetch logged-in user's friends
- For each friend, get their friends
- Built with FastAPI + Selenium

---

## 📦 Requirements

- Python 3.8+
- Google Chrome
- ChromeDriver (compatible with your Chrome version)

---

## 🔧 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ahmedrana603/facebook-scraper-fastapi.git
   cd facebook-scraper-api
   

## 🧪 API Usage

- Endpoint info (/scrape_facebook/)
- Payload description (cookies in JSON)
- Example request & response JSON
- Error handling info