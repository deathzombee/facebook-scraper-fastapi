from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MinimalCookieModel(BaseModel):
    c_user: str  # Facebook c_user cookie
    xs: str      # Facebook xs cookie

def scrape_facebook(c_user: str, xs: str):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.facebook.com/")
        time.sleep(3)

        driver.add_cookie({
            "name": "c_user",
            "value": c_user,  
            "domain": ".facebook.com",
            "path": "/",
            "secure": True,
            "httpOnly": False,
            "sameSite": "Lax"
        })

        driver.add_cookie({
            "name": "xs",
            "value": xs,  
            "domain": ".facebook.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Lax"
        })

        driver.get("https://www.facebook.com/friends")
        time.sleep(5)

        if "login" in driver.current_url:
            raise HTTPException(status_code=401, detail="Login failed via cookies.")

        wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="navigation"]')))
        time.sleep(5)

        all_friends_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//span[text()="All friends"]/ancestor::a[1]'))
        )
        all_friends_btn.click()
        time.sleep(5)

        friend_elements = driver.find_elements(By.XPATH, '//span[contains(@class, "x193iq5w") and text()]')
        friend_names = list({el.text.strip() for el in friend_elements if el.text.strip()})

        all_data = []

        def scroll_to_bottom():
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

        for index, name in enumerate(friend_names):
            print(f"\nScraping {index + 1}/{len(friend_names)}: {name}")
            try:
                friend_link = wait.until(EC.element_to_be_clickable((By.XPATH, f'//a[.//span[text()="{name}"]]')))
                driver.execute_script("arguments[0].scrollIntoView(true);", friend_link)
                time.sleep(1)
                friend_link.click()
            except:
                continue

            try:
                temp_count = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//a[contains(@href,"sk=friends")]//strong'))).text.strip()
            except:
                temp_count = "N/A"

            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(),"friends")]'))).click()
            except:
                pass

            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="main"]')))
            scroll_to_bottom()

            friends_of_friend = list({
                el.text.strip() for el in driver.find_elements(
                    By.XPATH, '//a[contains(@href,"facebook.com") and @role="link"]//span')
                if len(el.text.split()) >= 2
            })

            all_data.append({
                "name": name,
                "friend_count": temp_count,
                "friends_of_friend": friends_of_friend
            })

            driver.back()
            time.sleep(3)
            driver.get("https://www.facebook.com/friends")
            wait.until(EC.presence_of_element_located((By.XPATH, '//span[text()="All friends"]/ancestor::a[1]'))).click()

        return all_data

    finally:
        driver.quit()

@app.post("/scrape_facebook/")
async def start_scraping(payload: MinimalCookieModel):
    try:
        result = scrape_facebook(payload.c_user, payload.xs)
        return {"status": "success", "data": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
