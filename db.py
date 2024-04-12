import logging
import os

import dotenv
from elasticsearch import Elasticsearch
from retry import retry

from mappings import MOVIE_MAPPING
from movie_model import MovieModel
from site_info_model import SiteInfoModel

if not os.environ.get('ELASTIC_HOST'):
    dotenv.load_dotenv()

CACHE_INDEX = "seret_cache"
MOVIES_INDEX = "seret_movies"
ELASTIC_HOST = os.environ.get('ELASTIC_HOST')


def thread(func):
    def wrapper(*args, **kwargs):
        import threading
        threading.Thread(target=func, args=args, kwargs=kwargs).start()

    return wrapper


class DB:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.client = Elasticsearch(hosts=[ELASTIC_HOST])
        logging.getLogger('elastic_transport.transport').setLevel(logging.WARNING)

    @retry(Exception, tries=3, delay=10)
    def create_index(self):
        if not self.client.indices.exists(index=CACHE_INDEX):
            self.client.indices.create(index=CACHE_INDEX)
            self.logger.info(f"Created index {CACHE_INDEX}")

        if not self.client.indices.exists(index=MOVIES_INDEX):
            self.client.indices.create(index=MOVIES_INDEX, mappings=MOVIE_MAPPING)
            self.logger.info(f"Created index {MOVIES_INDEX} with mapping")

    def get_cached(self, sites: list[SiteInfoModel]) -> list[SiteInfoModel]:
        try:
            res = self.client.mget(index=CACHE_INDEX, body={"ids": [site.mid for site in sites]})
            self.logger.info(f"Got {len(res['docs'])} cached sites")
            raw_sites: list[dict] = []
            for hit in res['docs']:
                if hit['found']:
                    raw_site = hit['_source']
                    raw_site['mid'] = hit['_id']
                    raw_sites.append(raw_site)
            self.logger.info(f"Parsed {len(raw_sites)} cached sites")
            return [SiteInfoModel(**raw_site) for raw_site in raw_sites]
        except Exception as e:
            self.logger.warning(f"Failed to get cached sites: {e}")
            return []

    @thread
    def add_to_cache(self, site: SiteInfoModel):
        raw_site = site.dict()
        del raw_site['mid']
        self.client.index(index=CACHE_INDEX, body=raw_site, id=str(site.mid))
        logging.info(f"Added {site} to cache")

    @thread
    def submit_movie(self, movie: MovieModel, movie_index: int, all_movies_len: int, site: SiteInfoModel):
        """
        add movie to cache file without reading the whole file
        """
        raw_movie = movie.dict()
        raw_movie['_script'] = {
            "source": "Math.exp(-(doc['premiere'].date.millis - params.now) / params.scale)",
            "params": {
                "now": "now",
                "scale": 2592000000
            }}
        del raw_movie['id']
        self.client.index(index=MOVIES_INDEX, body=raw_movie, id=str(movie.id))
        logging.info(f"Added {movie.name} to DB: {movie_index}/{all_movies_len}")
        self.add_to_cache(site)
