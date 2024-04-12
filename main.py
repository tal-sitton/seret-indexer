import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from db import DB
from movie_model import MovieModel
from site_info_model import SiteInfoModel

SITEMAP_URL = 'https://www.seret.co.il/Sitemapsite.xml'

db = DB(logging.root)


def setup_logger():
    # log to file
    file_handler = logging.FileHandler('log.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    # log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[file_handler, console_handler], encoding='utf-8')


def get_sitemap(sitemap_url: str, session: requests.Session) -> bytes:
    res = session.get(sitemap_url)
    return res.content


def get_sites(sitemap_url: str, session: requests.Session) -> list[SiteInfoModel]:
    sitemap = get_sitemap(sitemap_url, session)
    soup = BeautifulSoup(sitemap, "lxml")
    logging.info(sitemap)
    sites: list[SiteInfoModel] = []
    for site in soup.find_all("url"):
        url = site.find_next('loc').text
        if not url.startswith('https://www.seret.co.il/movies/s_movies.asp?MID='):
            continue
        mid = int(url.split('MID=')[-1])
        priority = float(site.find_next('priority').text)
        sites.append(SiteInfoModel(mid=mid, url=url, priority=priority))
    logging.info(f"Found {len(sites)} sites")
    return sites


def filter_cached_sites(sites: list[SiteInfoModel]) -> list[SiteInfoModel]:
    cached = db.get_cached(sites)
    cached = {cache.id: cache.priority for cache in cached}
    if cached:
        return [site for site in sites if
                site.mid not in cached.keys() or (site.mid in cached.keys() and site.priority > 0.8)
                or (site.mid in cached and site.priority != cached[site.mid])]
    else:
        return sites


def handle_site(site: SiteInfoModel, session: requests.Session, movie_index: int, all_movies_len: int):
    res = session.get(site.url)
    soup = BeautifulSoup(res.content, "html.parser")

    if soup.find("link", {"rel": "canonical"})['href'] != site.url:
        logging.warning(f"{site.url} is not canonical, skipping AND adding to cache")
        db.add_to_cache(site)
        return

    name = soup.find("meta", {"property": "og:title"})['content']
    english_name = soup.find("span", {"itemprop": "alternatename"}).text
    keywords = soup.find("meta", {"name": "keywords"})['content'].split(',')
    description = soup.find("span", {"itemprop": "description"})
    image_url = soup.find("meta", {"property": "og:image"})['content']

    raw_year = soup.find("span", {"itemprop": "dateCreated"})
    if raw_year and raw_year.text.isdigit():
        year = int(raw_year.text)
    else:
        logging.warning(f"Failed to get year for {site}")
        year = None
    raw_premiere = soup.find("span", {"itemprop": "datePublished"}).text.split(" ")[0]
    premiere = datetime.strptime(raw_premiere, "%d/%m/%Y")
    movie = MovieModel(id=site.mid, url=site.url, priority=site.priority, name=name, english_name=english_name,
                       keywords=keywords, description=description.text, image_url=image_url, year=year,
                       premiere=premiere, scrape_date=datetime.now())
    db.submit_movie(movie, movie_index, all_movies_len, site)


def main():
    setup_logger()
    db.create_index()
    session = requests.Session()
    sites = get_sites(SITEMAP_URL, session)
    sites = filter_cached_sites(sites)
    sites.sort(key=lambda x: x.mid)

    all_movies_len = len(sites)
    logging.info(f"Found {all_movies_len} new sites")
    for i, site in enumerate(sites):
        try:
            handle_site(site, session, i + 1, all_movies_len)
        except Exception as e:
            logging.error(f"Failed to handle site {site}", exc_info=e)


if __name__ == '__main__':
    main()
