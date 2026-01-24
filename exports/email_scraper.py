"""
New Orleans Restaurant Email Scraper
Scrapes websites to find contact emails for restaurants missing email addresses.
"""

import pandas as pd
import requests
import re
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Configuration
INPUT_FILE = '/app/exports/nola_needs_scraping.csv'
OUTPUT_FILE = '/app/exports/nola_scraped_emails.csv'
PROGRESS_FILE = '/app/exports/scrape_progress.json'
DELAY_SECONDS = 1.5  # Be polite to servers

# Email regex pattern
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Common email patterns to exclude (generic/spam)
EXCLUDE_PATTERNS = [
    'example.com', 'test.com', 'domain.com', 'email.com',
    'wixpress.com', 'sentry.io', 'googleapis.com', 'gstatic.com',
    'wordpress.com', 'w3.org', 'schema.org', 'facebook.com',
    'twitter.com', 'instagram.com', 'youtube.com', 'linkedin.com',
    '.png', '.jpg', '.gif', '.css', '.js'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; OnTheCheapBot/1.0; +https://www.onthecheapapp.com)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def is_valid_email(email):
    """Check if email is valid and not a generic/excluded pattern"""
    email = email.lower().strip()
    
    # Check against exclusion patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern in email:
            return False
    
    # Must have reasonable length
    if len(email) < 6 or len(email) > 100:
        return False
    
    return True

def extract_emails_from_text(text):
    """Extract unique valid emails from text"""
    emails = re.findall(EMAIL_PATTERN, text, re.IGNORECASE)
    valid_emails = []
    
    for email in emails:
        email = email.lower().strip()
        if is_valid_email(email) and email not in valid_emails:
            valid_emails.append(email)
    
    return valid_emails

def fetch_page(url, timeout=10):
    """Fetch a webpage with error handling"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        pass
    return None

def find_contact_pages(base_url, html):
    """Find potential contact page URLs from the homepage"""
    contact_paths = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # Common contact page patterns
    contact_keywords = ['contact', 'about', 'team', 'info', 'reach', 'connect', 'email']
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').lower()
        text = link.get_text().lower()
        
        for keyword in contact_keywords:
            if keyword in href or keyword in text:
                full_url = urljoin(base_url, link['href'])
                if full_url not in contact_paths and urlparse(full_url).netloc == urlparse(base_url).netloc:
                    contact_paths.append(full_url)
                break
    
    return contact_paths[:5]  # Limit to 5 pages

def scrape_restaurant(name, website, contact_page=None):
    """Scrape a restaurant's website for email addresses"""
    result = {
        'restaurant_name': name,
        'website': website,
        'emails_found': [],
        'source_page': None,
        'status': 'pending'
    }
    
    if not website or not isinstance(website, str) or not website.startswith('http'):
        result['status'] = 'invalid_url'
        return result
    
    all_emails = []
    pages_to_check = [website]
    
    # Add contact page if provided
    if contact_page and isinstance(contact_page, str) and contact_page.startswith('http'):
        pages_to_check.append(contact_page)
    
    # Fetch homepage and find more contact pages
    homepage_html = fetch_page(website)
    if homepage_html:
        all_emails.extend(extract_emails_from_text(homepage_html))
        
        # Find additional contact pages
        additional_pages = find_contact_pages(website, homepage_html)
        pages_to_check.extend(additional_pages)
    
    # Check each page for emails
    for page_url in pages_to_check[1:]:  # Skip homepage (already checked)
        time.sleep(0.5)  # Small delay between pages on same site
        html = fetch_page(page_url)
        if html:
            emails = extract_emails_from_text(html)
            for email in emails:
                if email not in all_emails:
                    all_emails.append(email)
                    if not result['source_page']:
                        result['source_page'] = page_url
    
    if all_emails:
        result['emails_found'] = all_emails
        result['status'] = 'found'
        if not result['source_page']:
            result['source_page'] = website
    else:
        result['status'] = 'not_found'
    
    return result

def load_progress():
    """Load progress from previous run"""
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'completed': [], 'results': []}

def save_progress(progress):
    """Save progress for resume capability"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def main():
    print(f"=== Restaurant Email Scraper ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} restaurants to scrape\n")
    
    # Load previous progress
    progress = load_progress()
    completed_names = set(progress['completed'])
    results = progress['results']
    
    # Filter to only unprocessed
    df_todo = df[~df['restaurant_name'].isin(completed_names)]
    print(f"Already completed: {len(completed_names)}")
    print(f"Remaining: {len(df_todo)}\n")
    
    # Process each restaurant
    for idx, row in df_todo.iterrows():
        name = row['restaurant_name']
        website = row['website']
        contact_page = row.get('contact_page', None)
        
        print(f"[{len(completed_names)+1}/{len(df)}] Scraping: {name[:50]}...", end=" ")
        
        result = scrape_restaurant(name, website, contact_page)
        
        if result['status'] == 'found':
            print(f"✅ Found: {', '.join(result['emails_found'][:2])}")
        elif result['status'] == 'not_found':
            print("❌ No email found")
        else:
            print(f"⚠️ {result['status']}")
        
        results.append(result)
        completed_names.add(name)
        
        # Save progress every 10 restaurants
        if len(completed_names) % 10 == 0:
            progress = {'completed': list(completed_names), 'results': results}
            save_progress(progress)
        
        time.sleep(DELAY_SECONDS)
    
    # Save final results
    progress = {'completed': list(completed_names), 'results': results}
    save_progress(progress)
    
    # Create output CSV
    output_data = []
    for r in results:
        output_data.append({
            'restaurant_name': r['restaurant_name'],
            'website': r['website'],
            'email_1': r['emails_found'][0] if r['emails_found'] else '',
            'email_2': r['emails_found'][1] if len(r['emails_found']) > 1 else '',
            'all_emails': '; '.join(r['emails_found']),
            'source_page': r['source_page'] or '',
            'status': r['status']
        })
    
    output_df = pd.DataFrame(output_data)
    output_df.to_csv(OUTPUT_FILE, index=False)
    
    # Summary
    found = sum(1 for r in results if r['status'] == 'found')
    not_found = sum(1 for r in results if r['status'] == 'not_found')
    errors = sum(1 for r in results if r['status'] not in ['found', 'not_found'])
    
    print(f"\n=== SCRAPING COMPLETE ===")
    print(f"Total processed: {len(results)}")
    print(f"Emails found: {found}")
    print(f"No email found: {not_found}")
    print(f"Errors/Invalid: {errors}")
    print(f"\nResults saved to: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
