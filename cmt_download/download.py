"""
Download tensor moments from CMT
"""

from typing import Optional
import datetime
import requests
from bs4 import BeautifulSoup
from io import StringIO

import pandas as pd

BASE_URL = "https://www.globalcmt.org/cgi-bin/globalcmt-cgi-bin/CMT5/"
FORM = (
    "form?"
    "itype=ymd&yr={start_year}&mo={start_month}&day={start_day}"
    "&otype=ymd&oyr={end_year}&omo={end_month}&oday={end_day}"
    "&jyr=1976&jday=1&ojyr=1976&ojday=1&nday=1"
    "&lmw={mw_min}&umw={mw_max}&lms={ms_min}&ums={ms_max}&lmb={mb_min}&umb={mb_max}"
    "&llat={south}&ulat={north}&llon={west}&ulon={east}&lhd={min_depth}&uhd={max_depth}"
    "&lts=-9999&uts=9999&lpe1=0&upe1=90&lpe2=0&upe2=90&list=6"
)
COLUMNS = "lon lat depth mrr mtt mpp mrt mrp mtp iexp COORD_X COORD_Y name".split()


def download(
    min_date: datetime.datetime,
    max_date: datetime.datetime,
    mw_min: Optional[float] = 0,
    mw_max: Optional[float] = 10,
    ms_min: Optional[float] = 0,
    ms_max: Optional[float] = 10,
    mb_min: Optional[float] = 0,
    mb_max: Optional[float] = 10,
    south: Optional[float] = -90,
    north: Optional[float] = 90,
    west: Optional[float] = -180,
    east: Optional[float] = 180,
    min_depth: Optional[float] = 0,
    max_depth: Optional[float] = 1000,
) -> (str, pd.DataFrame):
    url = BASE_URL + FORM.format(
        start_year=min_date.year,
        start_month=min_date.month,
        start_day=min_date.day,
        end_year=max_date.year,
        end_month=max_date.month,
        end_day=max_date.day,
        mw_min=mw_min,
        mw_max=mw_max,
        ms_min=ms_min,
        ms_max=ms_max,
        mb_min=mb_min,
        mb_max=mb_max,
        south=south,
        north=north,
        west=west,
        east=east,
        min_depth=min_depth,
        max_depth=max_depth,
    )
    header, df = None, None
    page = 1
    while True:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Parse website
        print(f"Processing page {page}")
        header_i, df_i = _parse_page(soup)
        if header is None:
            header = header_i
        df = df_i if df is None else pd.concat((df, df_i), ignore_index=True)
        page += 1

        # Check if there are more pages
        links = [a for a in soup.find_all("a") if a.get_text() == "More solutions"]
        if not links:
            break
        (link,) = links
        url = link.get("href")

    return header, df


def _parse_page(soup: BeautifulSoup):
    pres = soup.find_all("pre")
    header = [s for s in pres[0].get_text().split("\n") if s]
    table = pres[1].get_text()
    df = pd.read_table(StringIO(table), sep=r"\s+", names=COLUMNS, index_col=None)
    return header, df
