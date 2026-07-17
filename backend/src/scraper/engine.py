from enum import Enum
from typing import Optional, List
import sys
import os
import asyncio
import subprocess
import json

class Platform(str, Enum):
    INTERNSHALA = "internshala"
    NAUKRI = "naukri"
    INDEED = "indeed"
    CUSTOM_URL = "custom"

class MNCCareerAgent(str, Enum):
    GOOGLE = "google"
    ADOBE = "adobe"
    DELOITTE = "deloitte"

class ScraperEngine:
    def __init__(self):
        # We define the persistent context path
        self.user_data_dir = os.path.join(os.getenv('APPDATA', ''), 'KairosBrowserContext')

    async def verify_authentication(self, platform: Platform) -> bool:
        """
        Since Kairos acts on behalf of the user, we must verify 
        that the user is actually logged into the target platform.
        """
        print(f"[Scraper] Verifying authentication for {platform.value}...")
        
        if platform == Platform.CUSTOM_URL:
            return True # Custom URLs usually don't require auth

        # TODO: Playwright check for auth cookies specifically for Internshala/Naukri
        return True

    async def fetch_jobs(self, platform: Platform, search_query: str, strict_prefs: List[str] = [], soft_prefs: List[str] = []) -> List[dict]:
        """
        Routes the fetch request to the correct platform scraper.
        """
        print(f"[Scraper] Fetching jobs for '{search_query}' from {platform.value}...")
        
        if platform == Platform.INTERNSHALA:
            return await self._scrape_internshala(search_query, strict_prefs, soft_prefs)
        elif platform == Platform.NAUKRI:
            return await self._scrape_naukri(search_query)
        
        return []

    async def _scrape_internshala(self, search_query: str, strict_prefs: List[str], soft_prefs: List[str]) -> List[dict]:
        # We run the synchronous subprocess in a background thread to prevent blocking FastAPI
        def run_worker():
            worker_path = os.path.join(os.path.dirname(__file__), "internshala_worker.py")
            # Run the isolated playwright worker using the current virtual environment python
            # Pass strict_prefs and soft_prefs as a JSON string
            result = subprocess.check_output(
                [sys.executable, worker_path, search_query, json.dumps(strict_prefs), json.dumps(soft_prefs)], 
                text=True
            )
            return json.loads(result)
            
        try:
            print(f"[Internshala] Delegating scrape task to isolated Playwright worker...")
            jobs = await asyncio.to_thread(run_worker)
            return jobs
        except Exception as e:
            print(f"[Internshala] Scrape Error: {e}")
            return []

    async def _scrape_naukri(self, search_query: str) -> List[dict]:
        # TODO: Implement Naukri scraper
        print("[Naukri] Scraper not yet implemented.")
        return []
