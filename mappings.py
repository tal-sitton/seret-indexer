MOVIE_MAPPING = {
    "properties": {
        "description": {
            "type": "text",
            "analyzer": "sefaria-naive-lemmatizer",
        },
        "english_name": {
            "type": "text",
            "analyzer": "english",
        },
        "keywords": {
            "type": "text",
        },
        "name": {
            "type": "text",
            "analyzer": "sefaria-naive-lemmatizer",
        },
        "premiere": {
            "type": "date"
        },
        "priority": {
            "type": "float"
        },
        "scrape_date": {
            "type": "date"
        },
        "url": {
            "type": "text",
        },
        "year": {
            "type": "long"
        }
    }
}
