from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration constants
FACEBOOK_BASE_URL = "https://www.facebook.com/"
FACEBOOK_FRIENDS_URL = "https://www.facebook.com/friends"
WAIT_TIMEOUT = 20
INITIAL_LOAD_DELAY = 3
FRIENDS_PAGE_DELAY = 5
CLICK_DELAY = 1
SCROLL_DELAY = 2
NAVIGATION_DELAY = 3

# XPath selectors
XPATH_NAVIGATION = '//div[@role="navigation"]'
XPATH_ALL_FRIENDS_BUTTON = '//span[text()="All friends"]/ancestor::a[1]'
XPATH_FRIEND_NAMES = '//span[contains(@class, "x193iq5w") and text()]'
XPATH_FRIEND_COUNT = '//a[contains(@href,"sk=friends")]//strong'
XPATH_FRIENDS_LINK = '//a[contains(text(),"friends")]'
XPATH_MAIN_CONTENT = '//div[@role="main"]'
XPATH_PROFILE_LINKS = '//a[contains(@href,"facebook.com") and @role="link"]//span'


class MinimalCookieModel(BaseModel):
    c_user: str  # Facebook c_user cookie
    xs: str      # Facebook xs cookie


def create_firefox_driver() -> WebDriver:
    """Create and configure a Firefox WebDriver instance."""
    options = Options()
    options.add_argument("--start-maximized")
    options.set_preference("dom.webnotifications.enabled", False)
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    
    driver = webdriver.Firefox(options=options)
    return driver


def add_facebook_cookies(driver: WebDriver, c_user: str, xs: str) -> None:
    """Add Facebook authentication cookies to the driver."""
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


def verify_login(driver: WebDriver) -> None:
    """Verify that the user is logged in to Facebook."""
    if "login" in driver.current_url:
        raise HTTPException(status_code=401, detail="Login failed via cookies.")


def scroll_to_bottom(driver: WebDriver) -> None:
    """Scroll to the bottom of the page to load all content."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_DELAY)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def extract_friend_names(driver: WebDriver) -> List[str]:
    """Extract unique friend names from the friends page."""
    friend_elements = driver.find_elements(By.XPATH, XPATH_FRIEND_NAMES)
    friend_names = list({el.text.strip() for el in friend_elements if el.text.strip()})
    return friend_names


def get_friend_data(driver: WebDriver, wait: WebDriverWait, name: str) -> Dict[str, Any]:
    """Get detailed data for a specific friend."""
    try:
        # Click on friend's profile
        friend_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//a[.//span[text()="{name}"]]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", friend_link)
        time.sleep(CLICK_DELAY)
        friend_link.click()
    except Exception:
        return None
    
    # Get friend count
    try:
        friend_count = wait.until(
            EC.presence_of_element_located((By.XPATH, XPATH_FRIEND_COUNT))
        ).text.strip()
    except Exception:
        friend_count = "N/A"
    
    # Navigate to friends list
    try:
        wait.until(
            EC.element_to_be_clickable((By.XPATH, XPATH_FRIENDS_LINK))
        ).click()
    except Exception:
        pass
    
    # Wait for page to load and scroll to load all friends
    wait.until(EC.presence_of_element_located((By.XPATH, XPATH_MAIN_CONTENT)))
    scroll_to_bottom(driver)
    
    # Extract friends of friend
    friends_of_friend = list({
        el.text.strip() 
        for el in driver.find_elements(By.XPATH, XPATH_PROFILE_LINKS)
        if len(el.text.split()) >= 2
    })
    
    return {
        "name": name,
        "friend_count": friend_count,
        "friends_of_friend": friends_of_friend
    }


def navigate_to_all_friends_page(driver: WebDriver, wait: WebDriverWait) -> None:
    """Navigate to the 'All friends' page."""
    driver.get(FACEBOOK_FRIENDS_URL)
    wait.until(EC.presence_of_element_located((By.XPATH, XPATH_ALL_FRIENDS_BUTTON))).click()
    time.sleep(FRIENDS_PAGE_DELAY)


def scrape_facebook(c_user: str, xs: str) -> List[Dict[str, Any]]:
    """
    Scrape Facebook friends data using authentication cookies.
    
    Args:
        c_user: Facebook c_user cookie value
        xs: Facebook xs cookie value
    
    Returns:
        List of dictionaries containing friend data
    """
    driver = create_firefox_driver()
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    try:
        # Initial page load and cookie setup
        driver.get(FACEBOOK_BASE_URL)
        time.sleep(INITIAL_LOAD_DELAY)
        
        add_facebook_cookies(driver, c_user, xs)
        
        # Navigate to friends page and verify login
        driver.get(FACEBOOK_FRIENDS_URL)
        time.sleep(FRIENDS_PAGE_DELAY)
        verify_login(driver)
        
        # Wait for navigation to load and click "All friends"
        wait.until(EC.presence_of_element_located((By.XPATH, XPATH_NAVIGATION)))
        time.sleep(FRIENDS_PAGE_DELAY)
        
        all_friends_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, XPATH_ALL_FRIENDS_BUTTON))
        )
        all_friends_btn.click()
        time.sleep(FRIENDS_PAGE_DELAY)
        
        # Extract all friend names
        friend_names = extract_friend_names(driver)
        all_data = []

        # Iterate through each friend and collect their data
        for index, name in enumerate(friend_names):
            print(f"\nScraping {index + 1}/{len(friend_names)}: {name}")
            
            friend_data = get_friend_data(driver, wait, name)
            if friend_data:
                all_data.append(friend_data)
            
            # Navigate back to the all friends page
            driver.back()
            time.sleep(NAVIGATION_DELAY)
            navigate_to_all_friends_page(driver, wait)

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
