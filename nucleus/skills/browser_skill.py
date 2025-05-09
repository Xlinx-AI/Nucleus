from nucleus.skill_manager import Skill

class BrowserSkill(Skill):
    """
    This skill is a web browser, but not the fun kind.
    It can open a site, grab the HTML, take a screenshot, or just dump the text.
    All powered by playwright, so expect some flakiness if the internet is in a bad mood.
    """
    def __init__(self, event_bus=None):
        super().__init__(
            name="browser",
            description="Open websites, screenshot them, or get their text. That's it.",
            capability=None  # We'll use get_capabilities for matching
        )
        self.event_bus = event_bus

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        """
        Returns a list of capabilities for this skill, because sometimes the router just needs a hint.
        """
        return [
            {
                "intent": "Open website",
                "desc": "Opens a website and returns its HTML.",
                "input_type": "url",
                "output_type": "html",
                "tags": ["browser", "open", "web"]
            },
            {
                "intent": "Take screenshot",
                "desc": "Takes a screenshot of the given web page.",
                "input_type": "url",
                "output_type": "image",
                "tags": ["browser", "screenshot", "png"]
            },
            {
                "intent": "Get page text",
                "desc": "Extracts all visible text from a page.",
                "input_type": "url",
                "output_type": "text",
                "tags": ["browser", "text", "web"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        You give it a step (dict with intent, url, etc).
        It'll try to do what you want, unless playwright throws a fit.
        """
        from playwright.async_api import async_playwright
        intent = step.get("intent", "").lower()
        url = step.get("url") or step.get("input") or step.get("desc", "")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                if "open" in intent:
                    if not url.startswith("http"):
                        url = "https://" + url
                    await page.goto(url, timeout=30000)
                    title = await page.title()
                    content = await page.content()
                    await browser.close()
                    return {"type": "html", "title": title, "content": content[:2000]}
                elif "screenshot" in intent:
                    if not url.startswith("http"):
                        url = "https://" + url
                    await page.goto(url, timeout=30000)
                    fname = f"screenshot_{context.get('task_id', 'site')}.png" if context else "screenshot_site.png"
                    await page.screenshot(path=fname)
                    await browser.close()
                    return {"type": "image", "file": fname}
                elif "text" in intent:
                    if not url.startswith("http"):
                        url = "https://" + url
                    await page.goto(url, timeout=30000)
                    text = await page.inner_text("body")
                    await browser.close()
                    return {"type": "text", "text": text[:3000]}
                else:
                    await browser.close()
                    return {"type": "error", "msg": "No idea what browser action you wanted, sorry."}
        except Exception as e:
            return {"type": "error", "msg": f"Browser crashed: {e}"}