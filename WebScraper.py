import re
import time
import os
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed


CHUNK_SIZE = 50
SAVE_EVERY = 20
song_cards = []

options = webdriver.ChromeOptions()
# options.add_argument("--headless")
# options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

song_links = []
song_meta = []   

try:
    driver.get("https://genius.com/search?q=Nepali")
    wait = WebDriverWait(driver, 10)

    modal_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "/html/body/routable-page/ng-outlet/search-results-page/div/div[2]/div[1]/div[2]/search-result-section/div/a")
    ))
    modal_button.click()
    time.sleep(2)

    consecutive_no_change = 0
    last_count = 0

    while consecutive_no_change < 3:
        try:
            modal_window = driver.find_element(By.XPATH, "/html/body/div[4]")
            driver.execute_script("arguments[0].scrollBy(0, 800);", modal_window)
            time.sleep(2)
        except:
            break

        song_cards = driver.find_elements(By.XPATH,
            "/html/body/div[4]/div[1]/ng-transclude/search-result-paginated-section/scrollable-data/div[1]/transclude-injecting-local-scope/search-result-item/div/mini-song-card"
        )

        if len(song_cards) == last_count:
            consecutive_no_change += 1
        else:
            last_count = len(song_cards)
            consecutive_no_change = 0

    for card in song_cards:
        try:
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            title = card.find_element(By.CLASS_NAME, "mini_card-title").text.strip()
            artist = card.find_element(By.CLASS_NAME, "mini_card-subtitle").text.strip()
        except:
            title, artist = "Def_title", "Def_Artist"
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

        song_links.append(link)
        song_meta.append((link, title, artist))

finally:
    driver.quit()



def save_to_csv(rows, filename="lyrics_output.csv"):
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Category", "Title", "Artist", "Lyrics"])
        writer.writerows(rows)
    print(" CSV Auto-Saved")



def scrape_song(meta):
    link, title, artist = meta
    try:
        local_driver = webdriver.Chrome(options=options)
        local_driver.get(link)
        wait = WebDriverWait(local_driver, 10)
        time.sleep(2)

        lyrics_div = wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="lyrics-root"]/div[1]'))
        )
        lyrics_text = lyrics_div.text.strip()

        if "Lyrics for this song have yet to be transcribed" in lyrics_text:
            return None

        
        if re.search(r'[\u0900-\u097F]', lyrics_text):
            category = "nepali"
        else:
            category = "romanized"

        return (category, title, artist, lyrics_text)

    except:
        return None
    finally:
        local_driver.quit()



processed_total = 0
all_rows = []

for chunk_start in range(0, len(song_meta), CHUNK_SIZE):
    chunk = song_meta[chunk_start:chunk_start + CHUNK_SIZE]
    chunk_results = []
    saved_in_chunk = 0

    print(f"\n Processing chunk {chunk_start // CHUNK_SIZE + 1} ({len(chunk)} songs)")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(scrape_song, meta) for meta in chunk]

        for future in as_completed(futures):
            processed_total += 1
            res = future.result()

            if res:
                chunk_results.append(res)
                saved_in_chunk += 1

            print(f"Progress: {processed_total}/{len(song_links)} | Chunk saved: {saved_in_chunk}")

            if saved_in_chunk % SAVE_EVERY == 0 and saved_in_chunk > 0:
                all_rows.extend(chunk_results)
                save_to_csv(all_rows)
                chunk_results = []

    all_rows.extend(chunk_results)
    save_to_csv(all_rows)

print(f"Total detected: {len(song_links)}")
print(f"Collected rows: {len(all_rows)}")
