import json

import scrapy
from furl import furl
from pydantic import BaseModel, ValidationError


# Pydantic schemas
class Image(BaseModel):
    title: str
    url: str

class SoundItem(BaseModel):
    id: str
    title: str
    type: str
    text: str
    image: Image
    link: dict | str
    download: str | None = None
    playerData: str | None = None
    pianoDownloads : str | None = None
    

NORD_KEYBOARDS_URL = "https://www.nordkeyboards.com"

def get_url(sound_type, selected_product, page_index = 1):
    base_url = f"{NORD_KEYBOARDS_URL}/_next/data/qVf153K5N41sKV1bsZjOg/en"
    fmt_url = "/sounds/{0}.json?selected_product={1}&page={2}&sort=alphabetic&path=sounds&path={0}"
    return base_url + fmt_url.format(sound_type, selected_product, page_index)



class ClaviaSoundBankSpider(scrapy.Spider):
    name = 'clavia_sound_bank_spider'
    sound_types = [
        "piano-library",
        "sample-library",
        "sound-collections",
        "signature-sound-banks"
    ]

    def __init__(self, selected_product=54, *args, **kwargs):
        super(ClaviaSoundBankSpider, self).__init__(*args, **kwargs)
        self.start_urls = [
            get_url(sound_type, selected_product=selected_product, page_index=1)
            for sound_type in self.sound_types
        ]

    def parse(self, response):
        data = json.loads(response.text)
        url = furl(response.url)

        props = data["pageProps"]["componentProps"]
        num_pages = int(props["pagination"]["totalPages"])
        current_page = int(props["pagination"]["currentPage"])
        
        # Follow the next page
        if current_page < num_pages:
            url.args['page'] = current_page + 1
            yield response.follow(url.url, self.parse)

        items = props["items"]
        for item in items:
            try:
                sound_item = SoundItem(**item)
                sound_item.link = f'{NORD_KEYBOARDS_URL}{sound_item.link["href"]}'

                # Nord Piano Library / Direct download
                # Nord Sample Library / Follow API urls
                # Sound Collections / Direct download
                # Signature Sound Banks / Direct download

                if sound_item.download:
                    sound_item.pianoDownloads = f'{NORD_KEYBOARDS_URL}{sound_item.pianoDownloads}'

                yield sound_item.dict()
            except ValidationError as e:
                self.logger.warning(str(e))



