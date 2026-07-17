import sys
import json
import os
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

def parse_date_string(date_str: str) -> str:
    if not date_str: return None
    date_str = date_str.strip().replace("'", "")
    try:
        from datetime import datetime, timezone
        dt = datetime.strptime(date_str, "%d %b %y")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        pass
    return None

def parse_relative_date(text: str) -> str:
    text = text.lower().strip()
    now = datetime.now(timezone.utc)
    try:
        if "just now" in text or "today" in text:
            return now.isoformat()
        elif "yesterday" in text:
            return (now - timedelta(days=1)).isoformat()
        elif "week" in text:
            num = int(''.join(filter(str.isdigit, text)) or 1)
            return (now - timedelta(weeks=num)).isoformat()
        elif "month" in text:
            num = int(''.join(filter(str.isdigit, text)) or 1)
            return (now - timedelta(days=num*30)).isoformat()
        elif "day" in text:
            num = int(''.join(filter(str.isdigit, text)) or 1)
            return (now - timedelta(days=num)).isoformat()
    except Exception:
        pass
    return now.isoformat()

def log_step(msg):
    print(f"\n[Step 1 Scraper] {msg}", file=sys.stderr, flush=True)

def scrape(search_query: str, strict_prefs: list, soft_prefs: list):
    log_step(f"Starting Internshala scrape for query: '{search_query}' with strict prefs: {strict_prefs} | soft prefs: {soft_prefs}")
    import re
    # 1. Fix the Search Query Split
    roles = [role.strip() for role in search_query.split(',') if role.strip()]
    base_query = roles[0].lower() if roles else "developer"
    url_query = re.sub(r'[^a-z0-9 ]', '', base_query).strip().replace(" ", "-")
    log_step(f"Sanitized URL Search Query: {url_query}")
    
    # 2. Utilize Native URL Structures
    is_internship = False
    for p in strict_prefs:
        if isinstance(p, dict) and p.get("category") == "Employment Type" and p.get("value", "").lower() == "internship":
            is_internship = True
            break
            
    if is_internship:
        target_url = f"https://internshala.com/internships/keywords-{url_query}/"
    else:
        target_url = f"https://internshala.com/jobs/keywords-{url_query}/"
        
    jobs = []
    user_data_dir = os.path.join(os.getenv('APPDATA', ''), 'KairosBrowserContext')

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,  # Run invisibly as requested
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled", # Bypass Google's "This browser is not secure" block
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        page = browser.new_page()
        
        try:
            collected_basics = []
            current_page = 1
            max_pages = 5
            processed_urls = set()
            
            while current_page <= max_pages and len(collected_basics) < 10:
                if current_page == 1:
                    page_url = target_url
                else:
                    if is_internship:
                        page_url = f"https://internshala.com/internships/page-{current_page}/keywords-{url_query}/"
                    else:
                        page_url = f"https://internshala.com/jobs/page-{current_page}/keywords-{url_query}/"
                        
                log_step(f"Scanning search results (Page {current_page}): {page_url}")
                try:
                    page.goto(page_url, timeout=60000, wait_until="domcontentloaded")
                    page.wait_for_selector('.individual_internship', timeout=15000)
                except Exception:
                    if page.locator('.zero_results').count() > 0 or page.locator('.empty_state').count() > 0 or page.locator('#error').count() > 0:
                        log_step("No more jobs available (Empty state).")
                    else:
                        log_step("No job cards found on this page.")
                    break
                    
                job_cards = page.query_selector_all('.individual_internship')
                
                for card in job_cards:
                    if len(collected_basics) >= 10:
                        break
                        
                    title_elem = card.query_selector('.job-internship-name')
                    company_elem = card.query_selector('.company-name')
                    
                    title = title_elem.inner_text() if title_elem else "Unknown Title"
                    company = company_elem.inner_text() if company_elem else "Unknown Company"
                    
                    link_elem = card.query_selector('.job-internship-name a') or card.query_selector('a.job-title-href')
                    href = link_elem.get_attribute('href') if link_elem else None
                    if not href:
                        href = card.get_attribute('data-href')
                        
                    job_url = f"https://internshala.com{href}" if href else ""
                    if not job_url or job_url in processed_urls:
                        continue
                        
                    processed_urls.add(job_url)
                        
                    stipend_elem = card.query_selector('.stipend') or card.query_selector('.salary')
                    stipend = stipend_elem.inner_text().strip() if stipend_elem else "Not Disclosed"
                    
                    posted_elem = card.query_selector('.status-small') or card.query_selector('.status') or card.query_selector('.posted_by')
                    posted_text = posted_elem.inner_text().strip() if posted_elem else "Just now"
                    posted_iso = parse_relative_date(posted_text)
                    
                    # 3. Deterministic DOM Badge Filtering
                    location_elem = card.query_selector('.location_link') or card.query_selector('#location_names')
                    location = location_elem.inner_text().strip() if location_elem else ""

                    passed_badges = True
                    for pref in strict_prefs:
                        if not isinstance(pref, dict): continue
                        cat = pref.get("category")
                        val = pref.get("value").lower()
                        
                        if cat == "Location":
                            if location and val not in location.lower():
                                log_step(f"-> REJECTED BY BADGE: Location '{val}' not in '{location}' for {title}")
                                passed_badges = False
                                break
                        elif cat == "Min Salary":
                            try:
                                import re
                                val_num = int(val)
                                stipend_str = stipend.replace(',', '')
                                nums = [int(n) for n in re.findall(r'\d+', stipend_str)]
                                if nums:
                                    max_offered = max(nums)
                                    if max_offered < val_num:
                                        log_step(f"-> REJECTED BY BADGE: Max salary ({max_offered}) < target ({val_num}) for {title}")
                                        passed_badges = False
                                        break
                            except Exception:
                                pass
                                
                    if not passed_badges:
                        continue
                    
                    job_url = f"https://internshala.com{href}" if href else ""
                    
                    # 4. Title Relevancy Check
                    if job_url:
                        title_lower = title.lower()
                        
                        target_roles = [r.strip().lower() for r in search_query.split(',') if r.strip()]
                        relevant = False
                        
                        for role in target_roles:
                            # Direct substring match
                            if role in title_lower:
                                relevant = True
                                break
                            # Compound word match (e.g. "AI" AND "Developer")
                            role_words = [w for w in role.split() if w]
                            if role_words and all(w in title_lower for w in role_words):
                                relevant = True
                                break
                                
                        if not relevant and target_roles:
                            log_step(f"-> REJECTED BY TITLE: '{title}' missing target roles {target_roles}")
                            continue
                            
                        collected_basics.append({
                            "title": title,
                            "company": company,
                            "url": job_url,
                            "stipend": stipend,
                            "posted_date": posted_iso
                        })
                        
                if len(collected_basics) >= 10:
                    break
                    
                current_page += 1
                
            for basic in collected_basics:
                if len(jobs) >= 10:
                    break # Reached our batch limit
                    
                title = basic["title"]
                company = basic["company"]
                job_url = basic["url"]
                stipend = basic["stipend"]
                posted_date = basic["posted_date"]
                
                log_step(f"Found Job: {title} | Company: {company}")
                log_step(f"Package: {stipend}")
                log_step(f"URL: {job_url}")
                
                # Visit the page immediately to check description against strict preferences
                log_step("Visiting job page to extract structured details and check preferences...")
                try:
                    page.goto(job_url, timeout=30000)
                    page.wait_for_selector('.detail_view', timeout=10000)
                    
                    description = ""
                    job_details = {}
                    
                    try:
                        # Attempt surgical DOM extraction using robust Text-based locators
                        def extract_section(heading_keywords):
                            for kw in heading_keywords:
                                loc = page.locator(f"h3:has-text('{kw}')")
                                if loc.count() > 0:
                                    sibling = loc.first.locator("~ div").first
                                    if sibling.count() > 0:
                                        return sibling.inner_text().strip()
                            return ""

                        req_text = extract_section(["Skill(s) required", "Who can apply"])
                        resp_text = extract_section([
                            "About the internship", 
                            "About the job", 
                            "Key responsibilities", 
                            "About the work from home job/internship",
                            "Day-to-day responsibilities",
                            "About the part time job/internship"
                        ])
                        
                        if not resp_text:
                            fallback_elem = page.query_selector('.text-container.responsibilities') or page.query_selector('.job-description') or page.query_selector('.text-container')
                            if fallback_elem:
                                resp_text = fallback_elem.inner_text().strip()
                                
                        perks_text = extract_section(["Perks", "Additional Information"])
                        
                        def extract_meta(keyword):
                            loc = page.locator(f".item_heading:has-text('{keyword}')")
                            if loc.count() > 0:
                                sibling = loc.first.locator("~ .item_body").first
                                if sibling.count() > 0:
                                    return sibling.inner_text().strip()
                                sibling2 = loc.first.evaluate("el => el.nextElementSibling ? el.nextElementSibling.innerText : ''")
                                if sibling2:
                                    return sibling2.strip()
                            return ""
                            
                        location = extract_meta("Location")
                        if not location:
                            loc_elem = page.query_selector('#location_names')
                            location = loc_elem.inner_text().strip() if loc_elem else "Not Disclosed"
                            
                        duration = extract_meta("Duration")
                        apply_by_str = extract_meta("Apply By")
                        apply_by_iso = parse_date_string(apply_by_str) if apply_by_str else None
                        
                        if req_text or resp_text or perks_text:
                            job_details = {
                                "requirements": req_text,
                                "responsibilities": resp_text,
                                "perks": perks_text
                            }
                            description = f"{req_text}\n{resp_text}\n{perks_text}"
                        else:
                            raise Exception("Specific structural sections not found")
                    except Exception as e:
                        log_step(f"DOM surgical extraction failed ({e}), falling back to bulk .detail_view extraction.")
                        desc_elem = page.query_selector('.detail_view')
                        description = desc_elem.inner_text() if desc_elem else ""
                        job_details = {"raw_description": description}
                    
                    if not description:
                        log_step("Warning: Could not extract description via fallback. Skipping.")
                        continue
                        
                    log_step(f"Details extracted. Filtering strict preferences...")
                    desc_lower = description.lower()
                    passed = True
                    for pref in strict_prefs:
                        if isinstance(pref, dict) and pref.get("category") == "Tech Stack":
                            if pref.get("value").lower() not in desc_lower:
                                log_step(f"-> REJECTED BY DESCRIPTION: Missing Tech Stack '{pref.get('value')}'")
                                passed = False
                                break
                            
                    if passed:
                        # Evaluate Soft Preferences
                        matched_prefs = []
                        unmatched_prefs = []
                        for sp in soft_prefs:
                            if not isinstance(sp, dict): continue
                            val = sp.get("value").lower()
                            if val in desc_lower:
                                matched_prefs.append(sp.get("value"))
                            else:
                                unmatched_prefs.append(sp.get("value"))
                                
                        log_step(f"-> ACCEPTED: Matched soft prefs: {matched_prefs}")
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "url": job_url,
                            "job_details": job_details,
                            "package": stipend,
                            "location": location,
                            "duration": duration,
                            "apply_by": apply_by_iso,
                            "posted_date": posted_date,
                            "matched_prefs": matched_prefs,
                            "unmatched_prefs": unmatched_prefs
                        })
                except Exception as e:
                    log_step(f"Error visiting job page: {e}. Skipping.")
                    continue
                    
                log_step(f"Moving to next job... ({len(jobs)}/10 collected)")
                        
        except Exception as e:
            # We output JSON even on error
            pass
        finally:
            browser.close()
            
    print(json.dumps(jobs))

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Python Developer"
    try:
        strict_prefs = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
    except:
        strict_prefs = []
        
    try:
        soft_prefs = json.loads(sys.argv[3]) if len(sys.argv) > 3 else []
    except:
        soft_prefs = []
        
    scrape(query, strict_prefs, soft_prefs)
