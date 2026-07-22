import sys
import json
import os
import httpx
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

def generate_filter_dictionary(target_roles: list, is_strict: bool = True) -> dict:
    prompt = f"Target Roles: {target_roles}\\nStrict Mode Active: {is_strict}\\nGenerate the JSON object now. Return ONLY the JSON object. Do not include conversational filler."
    
    sys_msg = (
        "You are the core Rules Engine for Kairos, an enterprise automated job application pipeline. "
        "Your task is to generate a strict classification dictionary in JSON format based on the user's target roles.\\n\\n"
        "The output MUST be a JSON object containing exactly three keys:\\n"
        "1. \\\"domain_anchors\\\": An array of lowercase strings representing the core domain (e.g. \\\"machine learning\\\", \\\"ai\\\", \\\"artificial intelligence\\\", \\\"data science\\\").\\n"
        "2. \\\"role_indicators\\\": An array of lowercase strings representing the seniority or functional role (e.g. \\\"engineer\\\", \\\"developer\\\", \\\"analyst\\\", \\\"scientist\\\"). ALWAYS include morphological variations (e.g. if \\\"developer\\\" is included, also include \\\"development\\\"; for \\\"analyst\\\", include \\\"analytics\\\").\\n"
        "3. \\\"banned_words\\\": An array of standalone lowercase words that indicate a completely unrelated career domain. CRITICAL: If the target roles are Software/IT/Cloud/DevOps, you MUST explicitly generate base word roots and continuous activity forms for non-technical fields (e.g., \\\"writer\\\", \\\"writing\\\", \\\"blog\\\", \\\"content\\\", \\\"marketing\\\", \\\"sales\\\"), AND explicitly ban physical construction terms (e.g., \\\"civil\\\", \\\"hvac\\\", \\\"construction\\\", \\\"interior design\\\", \\\"autocad\\\", \\\"electrical site\\\", \\\"mechanical site\\\", \\\"billing engineer\\\"). Note: only ban \\\"site\\\" if it is NOT part of a target like \\\"site reliability\\\".\\n\\n"
        "### FEW-SHOT EXAMPLES:\\n\\n"
        "Example 1: Target = [\\\"Machine Learning Engineer\\\"]\\n"
        "Output:\\n"
        "{\\n"
        "  \\\"domain_anchors\\\": [\\\"machine learning\\\", \\\"ml\\\", \\\"artificial intelligence\\\", \\\"ai\\\", \\\"deep learning\\\", \\\"computer vision\\\", \\\"nlp\\\"],\\n"
        "  \\\"role_indicators\\\": [\\\"engineer\\\", \\\"engineering\\\", \\\"developer\\\", \\\"development\\\", \\\"scientist\\\", \\\"researcher\\\"],\\n"
        "  \\\"banned_words\\\": [\\\"sales\\\", \\\"marketing\\\", \\\"hr\\\", \\\"writer\\\", \\\"graphic\\\", \\\"seo\\\", \\\"content\\\", \\\"recruiter\\\"]\\n"
        "}\\n"
    )
    
    payload = {
        "model": "llama3.1",
        "prompt": prompt,
        "system": sys_msg,
        "format": "json",
        "stream": False
    }
    
    try:
        with httpx.Client(timeout=120.0) as client:
            res = client.post("http://localhost:11434/api/generate", json=payload)
            res.raise_for_status()
            data = res.json()
            result_dict = json.loads(data.get("response", "{}"))
    except Exception as e:
        sys.stderr.write(f"[Step 1 Scraper] LLM Classification Error: {e}\\n")
        result_dict = {"domain_anchors": [], "role_indicators": [], "banned_words": []}
        
    if "domain_anchors" not in result_dict:
        result_dict["domain_anchors"] = []
        
    for role in target_roles:
        r_lower = role.lower()
        if r_lower not in result_dict["domain_anchors"]:
            result_dict["domain_anchors"].append(r_lower)
            
        if "react" in r_lower:
            for syn in ["react", "reactjs", "react.js"]:
                if syn not in result_dict["domain_anchors"]: result_dict["domain_anchors"].append(syn)
        if "node" in r_lower:
            for syn in ["node", "nodejs", "node.js"]:
                if syn not in result_dict["domain_anchors"]: result_dict["domain_anchors"].append(syn)
        if "vue" in r_lower:
            for syn in ["vue", "vuejs", "vue.js"]:
                if syn not in result_dict["domain_anchors"]: result_dict["domain_anchors"].append(syn)
                
        for w in r_lower.split():
            if w not in ["developer", "engineer", "analyst", "scientist", "manager", "intern", "assistant", "site"]:
                if w not in result_dict["domain_anchors"]:
                    result_dict["domain_anchors"].append(w)
                    
        if "site reliability" in r_lower:
            for syn in ["site reliability", "sre"]:
                if syn not in result_dict["domain_anchors"]:
                    result_dict["domain_anchors"].append(syn)
    return result_dict

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

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def log_step(msg):
    print(f"\n[Step 1 Scraper] {msg}", file=sys.stderr, flush=True)

def scrape(search_query: str, strict_prefs: list, soft_prefs: list):
    log_step(f"Starting Internshala scrape for query: '{search_query}' with strict prefs: {strict_prefs} | soft prefs: {soft_prefs}")
    import re
    # 1. Fix the Search Query Split
    roles = [role.strip(" .,") for role in search_query.split(',') if role.strip(" .,")]
    
    log_step(f"Generating Dynamic LLM Dictionary for roles: {roles}")
    is_strict_mode = False  # Toggle for broad vs strict domain matching
    filter_dict = generate_filter_dictionary(roles, is_strict=is_strict_mode)
    domain_anchors = filter_dict.get("domain_anchors", [])
    role_indicators = filter_dict.get("role_indicators", [])
    banned_words = filter_dict.get("banned_words", [])
    log_step(f"Dictionary ready.\nAnchors: {domain_anchors}\nRoles: {role_indicators}\nBanned: {banned_words}")
    
    # 2. Utilize Native URL Structures
    is_internship = False
    for p in strict_prefs:
        if isinstance(p, dict) and p.get("category") == "Employment Type" and p.get("value", "").lower() == "internship":
            is_internship = True
            break
            
        
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
            processed_urls = set()
            
            for role_str in roles:
                if len(collected_basics) >= 10:
                    break
                
                url_query = re.sub(r"[^a-z0-9 ]", "", role_str.lower()).strip().replace(" ", "-")
                log_step(f"Searching for role: '{role_str}' | Sanitized URL: {url_query}")
                
                if is_internship:
                    target_url = f"https://internshala.com/internships/keywords-{url_query}/"
                else:
                    target_url = f"https://internshala.com/jobs/keywords-{url_query}/"
                
                current_page = 1
                max_pages = 15
            
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
                        title = title_elem.inner_text() if title_elem else "Unknown Title"
                        
                        if title == "Unknown Title":
                            log_step("-> [REJECTED] 'Unknown Title'. Template empty state reached. Stopping pagination.")
                            current_page = max_pages + 1
                            break
                            
                        title_lower = title.lower()
                        
                        # Dynamic Dictionary Filter
                        is_rejected_by_banned = False
                        for bw in banned_words:
                            if re.search(rf'\b{re.escape(bw)}\b', title_lower):
                                log_step(f"-> [REJECTED BY BANNED WORD: '{bw}'] '{title}'")
                                is_rejected_by_banned = True
                                break
                                
                        if is_rejected_by_banned:
                            continue
                            
                        has_domain = any(re.search(rf'\b{re.escape(anchor)}\b', title_lower) for anchor in domain_anchors)
                        has_role = any(re.search(rf'\b{re.escape(role)}\b', title_lower) for role in role_indicators)
                        
                        is_valid_phrase = False
                        if is_strict_mode:
                            if has_domain and has_role:
                                is_valid_phrase = True
                        else:
                            if has_domain:
                                is_valid_phrase = True
                                
                        if not is_valid_phrase:
                            log_step(f"-> [REJECTED BY VALID PHRASE MISS] '{title}'")
                            continue
                            
                        log_step(f"-> [ACCEPTED] '{title}'")
                        
                        company_elem = card.query_selector('.company-name')
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
                        
                        if job_url:
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
