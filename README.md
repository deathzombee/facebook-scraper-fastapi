# 📘 Facebook Friends Scraper

A standalone Python script that scrapes a user's Facebook friend list and their friends' lists using valid session cookies (`c_user`, `xs`) via Selenium.

⚠️ **Disclaimer**: This project is for educational purposes only. Scraping Facebook may violate their [Terms of Service](https://www.facebook.com/legal/terms).

---

## 🚀 Features

- Login using Facebook cookies (no username/password needed)
- Fetch logged-in user's friends
- For each friend, get their friends
- Built with Selenium and Firefox WebDriver
- Standalone script - no web server needed

---

## 📦 Requirements

- Python 3.8+
- Mozilla Firefox
- GeckoDriver (compatible with your Firefox version)

---

## 🔧 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/deathzombee/facebook-scraper-fastapi.git
   cd facebook-scraper-fastapi
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download GeckoDriver:**
   - Visit https://github.com/mozilla/geckodriver/releases
   - Download the appropriate version for your system
   - Add it to your system PATH

---

## ⚙️ Configuration

1. **Set up your cookies:**
   - Edit `src/cookies.txt` and replace the placeholder values with your actual Facebook cookies
   - To get your cookies:
     1. Log in to Facebook in Firefox
     2. Open Developer Tools (F12)
     3. Go to the Storage tab
     4. Find the `c_user` and `xs` cookies under Cookies → https://www.facebook.com
     5. Copy their values into `src/cookies.txt`

   Example `src/cookies.txt`:
   ```
   c_user=1234567890
   xs=your_xs_cookie_value_here
   ```

---

## 🎯 Usage

Run the scraper:
```bash
python main.py
```

The script will:
1. Load cookies from `src/cookies.txt`
2. Open Firefox and log in to Facebook
3. Navigate to your friends list
4. For each friend, collect their friend count and friends list
5. Display results in the console

---

## 📝 Output

The scraper will display results in the console:
```
Facebook Friends Scraper
==================================================
Loading cookies from src/cookies.txt...
✓ Cookies loaded successfully

Starting scraper...

Scraping 1/10: John Doe
Scraping 2/10: Jane Smith
...

==================================================
Scraping completed! Found 10 friends.
==================================================

1. John Doe
   Friend count: 523
   Friends of friend: 45 people
...
```