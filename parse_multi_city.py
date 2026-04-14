import datetime
import time
import json
import logging
import os
from tqdm import tqdm

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Please install playwright: pip install playwright && playwright install")
    exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

SUBSCRIPTION_ID = "erg"

def build_multi_city_url(origin, dest1, dest2, dep_date, ret_date, sub_id):
    """
    Format: https://www.aviasales.ru/search/MOW0308OSA-TYO15081
    Where: MOW -> OSA on 03.08 (dep_date)
           TYO -> (MOW implicitly) on 15.08 (ret_date)
           1 -> One adult
    """
    ddmm1 = f"{dep_date.day:02d}{dep_date.month:02d}"
    ddmm2 = f"{ret_date.day:02d}{ret_date.month:02d}"
    
    url = (
        f"https://www.aviasales.ru/search/"
        f"{origin}{ddmm1}{dest1}-{dest2}{ddmm2}1"
        f"?subscription_id={sub_id}"
    )
    return url

# Search parameters
origin = "MOW"
destinations = ["TYO", "OSA"]  # Tokyo, Nagoya, Osaka (IATA codes) , "NGO"
min_duration = 10
max_duration = 12

# The window that must overlap with the trip (at least 2 days)
window_start = datetime.date(2026, 7, 29)
window_end = datetime.date(2026, 8, 5)
window_end_plus = window_end + datetime.timedelta(days=1)  # for inclusive overlap

# Range of possible departure dates 
start_departure = datetime.date(2026, 7, 27)
end_departure = datetime.date(2026, 8, 13)
days_range = (end_departure - start_departure).days + 1

all_queries = []
for dest1 in destinations:
    for dest2 in destinations:
        for duration in range(min_duration, max_duration + 1):
            for offset in range(days_range):
                dep_date = start_departure + datetime.timedelta(days=offset)
                ret_date = dep_date + datetime.timedelta(days=duration)
                
                # Check overlap
                overlap_start = max(dep_date, window_start)
                overlap_end = min(ret_date, window_end_plus)
                overlap_days = (overlap_end - overlap_start).days
                if overlap_days >= 2:
                    url = build_multi_city_url(origin, dest1, dest2, dep_date, ret_date, SUBSCRIPTION_ID)
                    all_queries.append({
                        "url": url,
                        "origin": origin,
                        "dest1": dest1,
                        "dest2": dest2,
                        "departure": str(dep_date),
                        "return": str(ret_date)
                    })

logging.info(f"Generated {len(all_queries)} queries.")

def find_cheapest_ticket(page):
    """Finds all tickets on the page and returns the minimum price and the corresponding locator."""
    tickets = page.locator('[data-test-id="ticket"], [data-test-id="ticket-desktop"], .s-ticket-desktop, div[data-test-id*="ticket"]')
    min_parsed_price = None
    best_ticket = None
    
    for i in range(tickets.count()):
        t = tickets.nth(i)
        price_el = t.locator('[data-test-id="price"], .price').first
        if price_el.is_visible():
            txt = price_el.inner_text().replace('\u200a', '').replace('\xa0', '').replace(' ', '')
            num = ''.join(filter(str.isdigit, txt))
            if num: 
                pval = int(num)
                if min_parsed_price is None or pval < min_parsed_price:
                    min_parsed_price = pval
                    best_ticket = t
                    
    return min_parsed_price, best_ticket

def count_transfers(best_ticket):
    """Extracts the number of transfers from a ticket locator."""
    import re
    total_transfers = "Unknown"
    
    transfer_spans = best_ticket.locator('span[data-test-id="text"]:has-text("пересад"), span[data-test-id="text"]:has-text("layover")')
    if transfer_spans.count() > 0:
        sum_transfers = 0
        for i in range(transfer_spans.count()):
            text_lower = transfer_spans.nth(i).inner_text().lower()
            match = re.search(r'(\d+)\s*(?:layover|пересад)', text_lower)
            if match:
                sum_transfers += int(match.group(1))
        if sum_transfers > 0:
            total_transfers = sum_transfers
            
    # Check direct
    direct_spans = best_ticket.locator('span[data-test-id="text"]:has-text("без пересадок"), span[data-test-id="text"]:has-text("direct")')
    if direct_spans.count() > 0 and total_transfers == "Unknown":
        total_transfers = 0
        
    return total_transfers

def extract_ticket_link(page, best_ticket, default_link):
    """Attempt to click the share button inside the ticket to get a short link."""
    short_link = default_link
    share_btn = best_ticket.locator('button:has(svg path[d^="m4.22 4.22"])').first
    if share_btn.is_visible():
        share_btn.click(timeout=3000)
        page.wait_for_timeout(1000) # Give UI time to copy or popup
        
        # Read Native OS Clipboard since we permitted 'clipboard-read'
        copied = page.evaluate('navigator.clipboard.readText()')
        if copied and 'avs.io' in copied:
            short_link = copied
        else:
            input_link = page.locator('input[value*="avs.io"]').first
            if input_link.is_visible():
                short_link = input_link.input_value()
    return short_link

def process_single_query(page, query):
    """Processes a single search query, waits for load, and extracts ticket details."""
    page.goto(query["url"], wait_until="domcontentloaded", timeout=60000)
    
    # Give the page a short moment to initialize search and display the progress loader
    page.wait_for_timeout(2000)
    
    # Wait for the search progress bar to disappear instead of fixed 35s timeout
    try:
        progress_bar = page.locator('div.s__A3pQob2DMKcguvoF.s__Ml7ohwAMUQvukoCB')
        progress_bar.wait_for(state='hidden', timeout=33000)
    except Exception:
        pass # Progress bar wait timeout or selector changed
        
    # Explicit check just in case elements are delayed
    try:
        page.wait_for_selector('[data-test-id="price"], .price, .ticket-price', timeout=15000)
    except Exception:
        pass # Might not find any if no tickets exist

    min_parsed_price = None
    total_transfers = "Unknown"
    short_link = query["url"]
    
    try:
        min_parsed_price, best_ticket = find_cheapest_ticket(page)
        query['min_price'] = min_parsed_price
        
        if best_ticket is not None:
            total_transfers = count_transfers(best_ticket)
            query['transfers'] = total_transfers
            short_link = extract_ticket_link(page, best_ticket, short_link)
            
        query['ticket_link'] = short_link
    except Exception as parse_e:
        logging.warning(f"Failed deep parsing of ticket: {parse_e}")
        query['min_price'] = min_parsed_price
        query['transfers'] = total_transfers
        query['ticket_link'] = short_link
        
    return query

def parse_tickets():
    results = []
    
    with sync_playwright() as p:
        # Launching Chromium in non-headless mode is often required to avoid anti-bot detection
        # If running inside WSL/container, you might need headed=False or xvfb-run   
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(permissions=['clipboard-read', 'clipboard-write'])
        page = context.new_page()

        try:
            for query in tqdm(all_queries, desc="Parsing URLs"):
                try:
                    updated_query = process_single_query(page, query)
                    results.append(updated_query)
                    
                    # Incremental save! If script freezes or Ctrl+C, nothing is lost.
                    with open("multi_city_results.json", "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=4)
                    
                except Exception as e:
                    logging.error(f"Error parsing {query['url']}: {e}")
                    query['error'] = str(e)
                    results.append(query)
                    
        except KeyboardInterrupt:
            logging.info(f"\nParsing manually interrupted! Saved {len(results)} accumulated results.")
            os._exit(0) # Force exit immediately without letting Playwright hang
        finally:
            # Wrap close in another block to avoid exceptions propagating during KeyboardInterrupt
            try:
                browser.close()
            except:
                pass
        
    return results

if __name__ == "__main__":
    extracted = parse_tickets()
    logging.info("Run finished successfully!")
