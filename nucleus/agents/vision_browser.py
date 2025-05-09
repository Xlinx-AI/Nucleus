"""
Веб-браузерный инструмент nucleus.agents: управление браузером через Selenium/Helium, поиск, скриншоты, интеграция с агентом.
"""

import time
from io import BytesIO
from typing import Optional, List

class BrowserController:
    """
    Управление браузером (Selenium + Helium): навигация, поиск, снятие скриншотов.
    """
    def __init__(self, driver=None):
        self.driver = driver or self._start_driver()

    def _start_driver(self):
        import helium
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1200,900")
        return helium.start_chrome(headless=False, options=options)

    def go_to(self, url: str):
        import helium
        helium.go_to(url)

    def search_text(self, text: str, nth: int = 1) -> str:
        from selenium.webdriver.common.by import By
        elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
        if not elements or nth > len(elements):
            return f"Не найдено совпадений для '{text}'"
        elem = elements[nth - 1]
        self.driver.execute_script("arguments[0].scrollIntoView(true);", elem)
        return f"Фокус на элементе {nth}/{len(elements)} для '{text}'"

    def screenshot(self) -> bytes:
        png = self.driver.get_screenshot_as_png()
        return png

    def close(self):
        self.driver.quit()

# Пример интеграции с агентом nucleus:
def agent_with_browser(model, tools: Optional[List] = None):
    """
    Пример создания агента с браузерным инструментом.
    """
    browser = BrowserController()
    # tools инициализируются, включая browser.search_text и browser.screenshot
    # Дальнейшая интеграция — по аналогии с остальными агентами nucleus
    return browser