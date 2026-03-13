from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import date
import re
import os

rows = []
seen = set()

ALLOWED_AIRLINES = {"American", "Delta", "JetBlue", "Spirit", "United"}

destination = input("Enter destination (MIA / MCO / TPA / FLL): ").strip().upper()
departure_date = input("Enter departure date (YYYY-MM-DD): ").strip()

if destination not in {"MIA", "MCO", "TPA", "FLL"}:
    raise ValueError("Destination must be one of: MIA, MCO, TPA, FLL")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page()

    page.goto("https://skiplagged.com", wait_until="domcontentloaded")

    print(f"Search BOS -> {destination} manually in the browser.")
    input("After results appear press ENTER here...")

    page.wait_for_timeout(3000)

    for _ in range(15):
        cards = page.locator(".trip")
        count = cards.count()
        print("Trips visible:", count)

        for i in range(count):
            card = cards.nth(i)
            class_name = card.get_attribute("class") or ""

            if "clear-filters" in class_name or "highlight-flex-container" in class_name:
                continue

            airline = None
            price = None
            stops = None

            try:
                airline_locator = card.locator("span.airlines")
                if airline_locator.count() > 0:
                    airline_text = airline_locator.first.text_content()
                    airline_text = airline_text.strip() if airline_text else None

                    if airline_text and airline_text != "Multiple":
                        airline = airline_text
                    else:
                        raw_html = card.inner_html()
                        for name in ALLOWED_AIRLINES:
                            if name in raw_html:
                                airline = name
                                break
            except:
                pass

            try:
                price_locator = card.locator(".trip-cost span")
                if price_locator.count() > 0:
                    price_text = price_locator.first.text_content()
                    if price_text:
                        price_text = (
                            price_text.replace("US$", "")
                            .replace("$", "")
                            .replace(",", "")
                            .strip()
                        )
                        price = int(price_text)
            except:
                pass

            try:
                stops_locator = card.locator("span.trip-stops")
                if stops_locator.count() > 0:
                    stops_text = stops_locator.first.text_content()
                    stops_text = stops_text.lower().strip()

                    if "nonstop" in stops_text:
                        stops = 0
                    else:
                        match = re.search(r"(\d+)", stops_text)
                        if match:
                            stops = int(match.group(1))
            except:
                pass

            key = (destination, airline, price, stops)

            if airline and price and stops is not None and key not in seen:
                seen.add(key)
                rows.append({
                    "search_date": str(date.today()),
                    "origin": "BOS",
                    "destination": destination,
                    "airline": airline,
                    "price": price,
                    "stops": stops,
                    "departure_date": departure_date,
                    "route": f"BOS-{destination}"
                })

        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(1500)

    browser.close()

df = pd.DataFrame(rows)
print(df.head(20))
print("Rows collected this run:", len(df))

raw_path = "data/raw/flights_scraped.csv"

if os.path.exists(raw_path):
    old_df = pd.read_csv(raw_path)
    df = pd.concat([old_df, df], ignore_index=True).drop_duplicates()

df.to_csv(raw_path, index=False)
print(f"Saved/updated {raw_path}")