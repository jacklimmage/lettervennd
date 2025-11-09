import sys
import requests
from bs4 import BeautifulSoup
import time
import random

# --- Anti-Throttling Configuration ---
"""
[ChatGPT did this] Global configuration for anti-throttling and polite scraping.

These constants are used to randomize request behavior, mimicking human
interaction speed and identity to avoid detection and rate limiting (HTTP 429).
This is achieved by ensuring that:
1.  Requests do not happen in fixed, predictable time intervals.
2.  The client's identity (User-Agent) appears to change between requests.

USER_AGENTS (list[str]): A pool of legitimate browser User-Agent strings.
                         One is chosen randomly for each HTTP request to obscure
                         the scraper's true identity.
"""
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15'
]
MIN_DELAY = 0.001  # Minimum delay between pages
MAX_DELAY = 0.005 # Maximum delay between pages

def get_wishlist(username):
    titles = []
    slugs = []
    page = 1

    while True:
        url = f"https://letterboxd.com/{username}/watchlist/page/{page}"

        headers = {'User-Agent': random.choice(USER_AGENTS)}

        resp = requests.get(url, headers=headers)
        match resp.status_code:
            case 200:
                soup = BeautifulSoup(resp.text, "html.parser")
            case 404:
                raise Exception(f"User '{username}' not found.")
            case 429:
                raise Exception("Rate limited by Letterboxd. Please try again later.")
            case _:
                raise Exception(f"Failed to fetch page: {resp.status_code}")
            

        soup = BeautifulSoup(resp.text, "html.parser")
        page_titles = [div["data-item-name"].strip()
                       for div in soup.select("div.react-component[data-item-name]")]
        page_slugs = [div["data-item-slug"].strip()
                      for div in soup.select("div.react-component[data-item-slug]")]
        if not page_titles:
            break  # no more pages
        titles.extend(page_titles)
        slugs.extend(page_slugs)
        page += 1
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    return titles, slugs

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python letterboxd_movie_night.py [username1 username2 ... ]")
        sys.exit(1)
    elif len(sys.argv) == 2:
        print("Please provide at least two usernames to compare watchlists.")
        sys.exit(1)

    # creating a dictionary to count movie occurrences
    movies = {}  # {(title, slug): [user1, user2, ...]}
    for user in sys.argv[1:]:
        try:
            titles, slugs = get_wishlist(user)
            print(f"Found {len(titles)} movies in {user}'s watchlist.")
            for i in range(len(titles)):
                movies[(titles[i], slugs[i])] = movies.get((titles[i], slugs[i]), []) + [user]
        except Exception as e:
            print(f"Error fetching user {user}:", e)
            

    # find movies in common watchlists
    overlap = set()  # movies in all watchlists
    all_but_one = set()  # movies in all but one watchlist

    for (title, slug), users in movies.items():

        if len(users) == len(sys.argv) - 1:
            overlap.add(title)

        elif len(users) == len(sys.argv) - 2:
            # find user missing this movie
            missing_user = [user for user in sys.argv[1:] if user not in users][0]
            all_but_one.add((title, missing_user))

    if not overlap:
        print("\nNo common movies found in every watchlist.")
    else:
        print("\nCommon movies in all watchlists:")
        for title in sorted(overlap):
            print("-", title)
    
    if not all_but_one:
        print("\nNo movies found in all but one watchlist.")
    else:
        print("\nMovies in all but one watchlist:")
        for title, missing_user in sorted(all_but_one):
            print(f"- {title} (missing from {missing_user})")
