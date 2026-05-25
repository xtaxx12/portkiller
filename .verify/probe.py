"""Probe the PortKiller UI: light theme, kill modal, empty-state filter."""

import time
import pathlib

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

OUT = pathlib.Path(r"C:\Users\USER\Downloads\projects\portkiller\.verify")
OUT.mkdir(parents=True, exist_ok=True)

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
opts.add_argument("--hide-scrollbars")
opts.add_argument("--window-size=1920,1200")

driver = webdriver.Chrome(options=opts)
driver.set_window_size(1920, 1200)

try:
    # 1) Dark + kill modal
    driver.get("http://127.0.0.1:8787/")
    time.sleep(2.5)
    # click the first enabled kill button
    clicked = driver.execute_script(
        "var b=Array.from(document.querySelectorAll('.btn-kill')).find(x=>!x.disabled);"
        "if(b){b.click();return true} return false;"
    )
    if clicked:
        time.sleep(0.5)
        driver.save_screenshot(str(OUT / "portkiller-modal.png"))
        print("modal screenshot saved")
        driver.execute_script("document.getElementById('cancelKill').click();")
    else:
        print("no enabled kill button found")

    time.sleep(0.4)

    # 2) Logs drawer
    driver.execute_script("document.getElementById('logsToggle').click();")
    time.sleep(0.6)
    driver.save_screenshot(str(OUT / "portkiller-drawer.png"))
    driver.execute_script("document.getElementById('closeDrawer').click();")
    print("drawer screenshot saved")
    time.sleep(0.4)

    # 3) Light theme
    driver.execute_script("document.getElementById('themeToggle').click();")
    time.sleep(0.5)
    driver.save_screenshot(str(OUT / "portkiller-light.png"))
    print("light theme screenshot saved")

    # 4) Critical filter
    driver.execute_script(
        "document.querySelector('.filter-chip[data-filter=critical]').click();"
    )
    time.sleep(0.5)
    driver.save_screenshot(str(OUT / "portkiller-critical.png"))
    print("critical-filter screenshot saved")

    # 5) Force a 'no results' state via search
    driver.execute_script(
        "var i=document.getElementById('searchInput');"
        "i.value='zzz-no-match-xxx';"
        "i.dispatchEvent(new Event('input', {bubbles:true}));"
    )
    time.sleep(0.4)
    driver.save_screenshot(str(OUT / "portkiller-empty.png"))
    print("empty-state screenshot saved")

finally:
    driver.quit()
