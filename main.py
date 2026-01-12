from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
import time

# Configuration constants
COOKIES_FILE_PATH = Path(__file__).parent / "src" / "cookies.txt"
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


def load_cookies_from_file() -> Tuple[str, str]:
    """
    Load Facebook cookies from src/cookies.txt file.
    
    Returns:
        Tuple of (c_user, xs) cookie values
        
    Raises:
        FileNotFoundError: If cookies file is not found
        ValueError: If cookies file is improperly formatted
    """
    if not COOKIES_FILE_PATH.exists():
        raise FileNotFoundError(
            f"Cookies file not found at {COOKIES_FILE_PATH}. Please create it with c_user and xs values."
        )
    
    cookies = {}
    try:
        with open(COOKIES_FILE_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse key=value format
                if '=' in line:
                    key, value = line.split('=', 1)
                    cookies[key.strip()] = value.strip()
    except Exception as e:
        raise ValueError(f"Error reading cookies file: {str(e)}")
    
    # Validate required cookies are present
    if 'c_user' not in cookies or 'xs' not in cookies:
        raise ValueError("Cookies file must contain both 'c_user' and 'xs' values")
    
    # Validate cookies have actual values (not placeholder text)
    if cookies['c_user'].startswith('your_') or cookies['xs'].startswith('your_'):
        raise ValueError(
            "Please replace placeholder values in cookies.txt with your actual Facebook cookie values"
        )
    
    return cookies['c_user'], cookies['xs']


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
        raise RuntimeError("Login failed via cookies. Please check your cookie values in src/cookies.txt")


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


def escape_xpath_string(value: str) -> str:
    """
    Escape a string for use in XPath expressions to prevent injection attacks.
    
    Args:
        value: The string to escape
    
    Returns:
        Escaped string safe for XPath
    """
    # If the string contains no single quotes, wrap it in single quotes
    if "'" not in value:
        return f"'{value}'"
    # If it contains no double quotes, wrap it in double quotes
    elif '"' not in value:
        return f'"{value}"'
    # Otherwise, use concat to handle both quote types
    else:
        parts = value.split("'")
        # Build concat: concat('part1', "'", 'part2', "'", 'part3')
        # Keep empty parts to preserve consecutive single quotes
        concat_parts = []
        for i, part in enumerate(parts):
            concat_parts.append(f"'{part}'")
            if i < len(parts) - 1:  # Add single quote between parts
                concat_parts.append("\"'\"")
        return f"concat({', '.join(concat_parts)})"


def get_friend_data(driver: WebDriver, wait: WebDriverWait, name: str) -> Optional[Dict[str, Any]]:
    """Get detailed data for a specific friend."""
    try:
        # Click on friend's profile - use escaped XPath string
        escaped_name = escape_xpath_string(name)
        friend_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//a[.//span[text()={escaped_name}]]'))
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


def navigate_to_all_friends_page(driver: WebDriver, wait: WebDriverWait, check_navigation: bool = False) -> None:
    """
    Navigate to the 'All friends' page.
    
    Args:
        driver: WebDriver instance
        wait: WebDriverWait instance
        check_navigation: If True, wait for navigation element to load first
    """
    driver.get(FACEBOOK_FRIENDS_URL)
    if check_navigation:
        wait.until(EC.presence_of_element_located((By.XPATH, XPATH_NAVIGATION)))
        time.sleep(FRIENDS_PAGE_DELAY)
    
    all_friends_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, XPATH_ALL_FRIENDS_BUTTON))
    )
    all_friends_button.click()
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
    driver = None
    try:
        driver = create_firefox_driver()
        wait = WebDriverWait(driver, WAIT_TIMEOUT)

        # Initial page load and cookie setup
        driver.get(FACEBOOK_BASE_URL)
        time.sleep(INITIAL_LOAD_DELAY)
        
        add_facebook_cookies(driver, c_user, xs)
        
        # Navigate to friends page and verify login
        driver.get(FACEBOOK_FRIENDS_URL)
        time.sleep(FRIENDS_PAGE_DELAY)
        verify_login(driver)
        
        # Navigate to "All friends" page
        navigate_to_all_friends_page(driver, wait, check_navigation=True)
        
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
        if driver is not None:
            driver.quit()


def main():
    """Main function to run the Facebook scraper."""
    print("Facebook Friends Scraper")
    print("=" * 50)
    
    try:
        # Load cookies from file
        print(f"Loading cookies from {COOKIES_FILE_PATH}...")
        c_user, xs = load_cookies_from_file()
        print("✓ Cookies loaded successfully")
        
        # Run the scraper
        print("\nStarting scraper...")
        result = scrape_facebook(c_user, xs)
        
        # Display results
        print("\n" + "=" * 50)
        print(f"Scraping completed! Found {len(result)} friends.")
        print("=" * 50)
        
        for idx, friend in enumerate(result, 1):
            print(f"\n{idx}. {friend['name']}")
            print(f"   Friend count: {friend['friend_count']}")
            print(f"   Friends of friend: {len(friend['friends_of_friend'])} people")
        
        return result
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print(f"\nPlease create the file at {COOKIES_FILE_PATH} with your Facebook cookies.")
        return None
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        return None
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
