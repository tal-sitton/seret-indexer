MOVIE_MAPPING = {
    "properties": {
        "url": {
            "type": "text",
        },
        "priority": {
            "type": "float"
        },

        "name": {
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
        "description": {
            "type": "text",
            "analyzer": "sefaria-naive-lemmatizer",
        },
        "year": {
            "type": "long"
        },
        "premiere": {
            "type": "date"
        },
        "scrape_date": {
            "type": "date"
        },
        "image_url": {
            "type": "text"
        }
    }
}
