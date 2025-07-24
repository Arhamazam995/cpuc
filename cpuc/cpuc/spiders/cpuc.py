import urllib.parse

import scrapy
from scrapy.http import FormRequest
from datetime import datetime
from itertools import zip_longest

class CpucSpider(scrapy.Spider):
    name = "cpuc"
    start_urls = ["https://docs.cpuc.ca.gov/advancedsearchform.aspx"]

    def __init__(self, datefrom=None, dateto=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index1 = 0
        self.docket = None
        self.datefrom = datefrom
        self.dateto = dateto
        self.ids = set()
        self.proceedings = None
        self.index = 0
        self.state_id = None
        self.proceed = None
        self.fillings = None
        self.document = None

    def parse(self, response):
        __viewstate = response.xpath('//input[@id="__VIEWSTATE"]/@value').get()
        __eventvalidation = response.xpath('//input[@id="__EVENTVALIDATION"]/@value').get()
        __viewstategenerator = response.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').get()

        yield FormRequest(
            url=response.url,
            formdata={
                '__VIEWSTATE': __viewstate,
                '__EVENTVALIDATION': __eventvalidation,
                '__VIEWSTATEGENERATOR': __viewstategenerator,
                'PubDateFrom': self.datefrom,
                'PubDateTo': self.dateto,
                'SearchButton': 'Search'
            },
            callback=self.parse_result
        )

    def parse_result(self, response):
        self.parse_data(response)

        next_link = response.xpath("//a[contains(@href, 'lnkNext')]/@href").get()
        if next_link:
            event_target = next_link.split("'")[1]

            __viewstate = response.xpath('//input[@id="__VIEWSTATE"]/@value').get()
            __eventvalidation = response.xpath('//input[@id="__EVENTVALIDATION"]/@value').get()
            __viewstategenerator = response.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').get()

            return FormRequest(
                url="https://docs.cpuc.ca.gov/SearchRes.aspx",
                formdata={
                    '__EVENTTARGET': event_target,
                    '__VIEWSTATE': __viewstate,
                    '__VIEWSTATEGENERATOR': __viewstategenerator,
                    '__EVENTVALIDATION': __eventvalidation
                },
                callback=self.parse_result
            )
        else:
            return self.parse_output()

    def parse_data(self, response):
        proceeding1 = [x for x in response.xpath("//td[@class='ResultTitleTD']/text()").getall() if 'Proceeding:' in x]
        proceedings2 = [p.split(':')[-1].strip() for p in proceeding1]
        for data in proceedings2:
            split_items = [p for p in data.split(";")]
            for p in split_items:
                p1 = p.strip()
                if p1 in self.ids:
                    continue
                else:
                    self.ids.add(p1)

    def parse_output(self):
        self.proceedings = list(self.ids)
        if self.index < len(self.proceedings):
            self.proceed = self.proceedings[self.index]
            params = {
                "p": f"401:56:6056676397617::NO:RP,57,RIR:P5_PROCEEDING_SELECT:{self.proceed}"
            }
            full_url = f"https://apps.cpuc.ca.gov/apex/f?{urllib.parse.urlencode(params)}"
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_result_data,
                dont_filter=True
            )
    def parse_result_data(self, response):
        staff = response.xpath("//span[@id='P56_STAFF']/text()").getall()
        filled_on = response.xpath("//span[@id='P56_FILING_DATE']/text()").get()
        industry = response.xpath("//span[@id='P56_INDUSTRY']/text()").get()
        category = response.xpath("//span[@id='P56_CATEGORY']/text()").get()
        status = response.xpath("//span[@id='P56_STATUS']/text()").get()
        description = response.xpath("//span[@id='P56_DESCRIPTION']/text()").get()
        filled_by = response.xpath("//span[@id='P56_FILED_BY']/text()").getall()
        url = response.url
        url1 = url.split("P5_PROCEEDING_SELECT%3A")[-1]
        self.docket = {
                "assignees" : staff,
                "filled on" : filled_on,
                "crawled at" : datetime.now().isoformat(),
                "fillings" : [],
                "industries" : industry,
                "major parties" : filled_by,
                "proceeding type" : category,
                "slug" : f"ca-{url1}",
                "source_assignees": [],
                "source_major_parties": [],
                "source title": description,
                "source url" : response.url,
                "spider name" : "on_demand",
                "start_time" : None,
                "state" : "CA",
                "state id" : url1,
                "status" : status,
                "title" : description,
            }
        links = response.xpath("//ul//a/@href")[1].get()
        yield scrapy.Request(
            url=f"https://apps.cpuc.ca.gov/apex/{links}",
            callback=self.parse_filing_date,
            dont_filter=True
            )

    def parse_filing_date(self, response):
        filing_dates = response.xpath("//td[@headers='FILING_DATE']/text()").getall()
        descriptions = response.xpath("//td[@headers='DESCRIPTION']/text()").getall()
        filed_by_parties = response.xpath("//td[@headers='FILED_BY']/text()").getall()
        document_types = response.xpath("//td[@headers='DOCUMENT_TYPE']//span//u/text()").getall()
        self.state_id = response.xpath("//td[@headers='DOCUMENT_TYPE']//a/@href").getall()
        self.fillings = []
        for date, desc, party, doc_type, sat_id in zip_longest(filing_dates, descriptions, filed_by_parties, document_types, self.state_id):
            data = {
                "filed_on": date.strip(),
                "description": desc.strip(),
                "document": [],
                "filing_parties": party,
                "source_filing_parties": party,
                "state_id" : sat_id.split("=")[-1],
                "type": doc_type,
            }
            self.fillings.append(data)
        self.docket["fillings"] = self.fillings

        if self.index1 < len(self.state_id):
            doc_id = self.state_id[self.index1].split("ID=")[-1]
            params = {
                "DocFormat": "ALL",
                "DocID": doc_id
            }
            yield scrapy.Request(
                url=f"https://docs.cpuc.ca.gov/SearchRes.aspx?{urllib.parse.urlencode(params)}",
                meta={'cookiejar': doc_id},
                callback=self.parse_ducoment,
                dont_filter=True
            )
    def parse_ducoment(self, response):
        self.document = []
        for row in response.xpath('//*[@id="ResultTable"]//tbody/tr[not(@style)]'):
            title = row.css(".ResultTitleTD ::text").get()
            exten = row.css(".ResultLinkTD a::text").get()
            source_url = row.css(".ResultLinkTD a::attr(href)").get()
            name = source_url.split("/")[-1] if source_url else None
            data =  {
                "blob_name": f"CA_{self.proceed}_{name}",
                "extension": exten,
                "name" : name,
                "source_url": f"https://docs.cpuc.ca.gov{source_url}",
                "title" : title,
            }
            self.document.append(data)
        self.fillings[self.index1]["document"] = self.document
        self.index1 += 1
        if self.index1 < len(self.state_id):
            doc_id = self.state_id[self.index1].split("ID=")[-1]
            params = {
                "DocFormat" : "ALL",
                "DocID" : doc_id
            }
            yield scrapy.Request(
                url=f"https://docs.cpuc.ca.gov/SearchRes.aspx?{urllib.parse.urlencode(params)}",
                meta={'cookiejar': doc_id},
                callback=self.parse_ducoment,
                dont_filter=True
            )

        else:
            self.index += 1
            self.index1 = 0
            self.docket["fillings"] = self.fillings
            yield {
                "Docket" : self.docket,
                "state" : "CA"
            }
            if self.index < len(self.proceedings):
                self.proceed = self.proceedings[self.index]
                params = {
                    "p": f"401:56:6056676397617::NO:RP,57,RIR:P5_PROCEEDING_SELECT:{self.proceed}"
                }
                next_url = f"https://apps.cpuc.ca.gov/apex/f?{urllib.parse.urlencode(params)}"
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse_result_data,
                    meta={"proceed": self.proceed},
                    dont_filter=True
                )
