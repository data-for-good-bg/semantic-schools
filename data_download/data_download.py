"""
This script can be used to download the csv/json/xml files for all NVO and DZI data.

It uses as starting point the following links:
* for DZI https://data.egov.bg/data/view/066b4b04-d81d-444e-a61c-8ca0516079e4
  This web page can contains list of resources (ресурси) for different DZI sessions.
  The page could have pagination.

  The title of each resource contains the following attributes:
  * session (сесия) - possible values are "май-юни" or "август-септември"
    we use only the second month (june for юни and september for септември)
  * year (година) - values usually are expressed like 2025/2026, but we use
    only the second year -> 2026
  * type of examination - z (задължителни) or i (по избор)
  * the link itself contains a UUID which is the ID of the resource
  * the link to the resource points to another web page which contains also
    attributes of interest:
    * last date of change labeled with "Последна промяна"
    * at the bottom there's a section with links, where we can find the
      link to the different types - csv, json, xml, ...

  When files are downloaded, we use these attributes to name the downloaded files:
  * dzi-<year>-<session month>-<type of examination>-<id>-<last-date-of-change>.<extension for the desired type>

  For NVO the files are named:
  * nvo-<grade>-<year>-<id>-<last-date-of-change>.<extension for the desired type>

* NVO
  * 4th grade - https://data.egov.bg/organisation/dataset/5613e75f-2b1b-4244-9f54-b27580a91dfb
  * 7th grade - https://data.egov.bg/organisation/dataset/b56288b6-25aa-4049-9aa6-de2cd4cdabf8
  * 10th grade - https://data.egov.bg/data/view/2f801b2f-d4cb-4ddb-a23d-3e372339c80f

  All of these web pages also contains list of resources (ресурси), but their
  titles contain less attributes of interest, here they are:
  * the grade - it can be taken from the title in roman digits or it from the starting page URL
  * the year - it usually expressed as 2025/2026, but we use only the second one -> 2026
  * the id which can be extracted from the link to the resource
  * similarly to the DZI resource pages, from there we can extract the last date of change
    and the links to the desired type for downloading

The downloader uses a .cache directory where it downloads the starting
or resource pages. This can reduce significantly the performance during
development, but one should clean the cache if they want to get the most
recent data.

"""

import argparse
import hashlib
import logging
import os
import re
import shutil
from dataclasses import dataclass
from html import unescape
from typing import Optional
from urllib.parse import urlparse

import requests


logger = logging.getLogger(__name__)

DZI_START_URL = 'https://data.egov.bg/data/view/066b4b04-d81d-444e-a61c-8ca0516079e4'
NVO_START_URLS = {
    4: 'https://data.egov.bg/organisation/dataset/5613e75f-2b1b-4244-9f54-b27580a91dfb',
    7: 'https://data.egov.bg/organisation/dataset/b56288b6-25aa-4049-9aa6-de2cd4cdabf8',
    10: 'https://data.egov.bg/data/view/2f801b2f-d4cb-4ddb-a23d-3e372339c80f',
}

SUPPORTED_EXTENSIONS = ['csv', 'json', 'xml']
DEFAULT_DOWNLOAD_DIR = './downloads'
DEFAULT_EXTENSION = 'json'
CACHE_DIR = '.cache'

SESSION_MONTH_PATTERNS = [
    ('септември', 'september'),
    ('август', 'september'),
    ('юни', 'june'),
    ('юнска', 'june'),
    ('май', 'june'),
]

RESOURCE_LINK_RE = re.compile(
    r'href="(https://data\.egov\.bg/(?:data|organisation/datasets)/resourceView/([0-9a-f-]+))(?:\?[^"]*)?"[^>]*>(.*?)</a>',
    re.S,
)
RPAGE_LINK_RE = re.compile(r'href="([^"]*[?&]rpage=\d+[^"]*)"')
LAST_CHANGE_RE = re.compile(r'Последна промяна:\s*(\d{4}-\d{2}-\d{2})')
YEAR_RANGE_RE = re.compile(r'(\d{4})/(\d{4})')
SINGLE_YEAR_RE = re.compile(r'(\d{4})\s*(?:г\.|оценки)')


@dataclass
class Resource:
    id: str
    url: str
    title: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Downloads the csv/json/xml files for all NVO and DZI data from data.egov.bg.'
    )
    parser.add_argument(
        '--download-dir', type=str, default=DEFAULT_DOWNLOAD_DIR,
        help=f'Target directory for the downloaded files. By default: {DEFAULT_DOWNLOAD_DIR}.'
    )
    parser.add_argument(
        '--extension', type=str, choices=SUPPORTED_EXTENSIONS, default=DEFAULT_EXTENSION,
        help=f'File type to download. By default: {DEFAULT_EXTENSION}.'
    )
    parser.add_argument(
        '--clean-cache', action='store_true',
        help=f'Removes the {CACHE_DIR} directory before downloading, so all pages are fetched fresh.'
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Overwrite already downloaded files. By default existing files are never overwritten.'
    )
    return parser.parse_args()


def fetch_page(url: str, cache_dir: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, hashlib.sha256(url.encode('utf-8')).hexdigest() + '.html')
    if os.path.exists(cache_file):
        logger.debug('Using cached page %s', url)
        with open(cache_file, 'rt', encoding='utf-8') as f:
            return f.read()

    logger.info('Fetching %s', url)
    r = requests.get(url)
    r.raise_for_status()
    with open(cache_file, 'wt', encoding='utf-8') as f:
        f.write(r.text)
    return r.text


def collect_resources(start_url: str, cache_dir: str) -> list[Resource]:
    start_path = urlparse(start_url).path
    resources = []
    seen_ids = set()
    seen_pages = set()
    queue = [start_url]
    while queue:
        url = queue.pop(0)
        if url in seen_pages:
            continue
        seen_pages.add(url)
        page = fetch_page(url, cache_dir)
        for m in RESOURCE_LINK_RE.finditer(page):
            resource_id, raw_title = m.group(2), m.group(3)
            if resource_id in seen_ids:
                continue
            seen_ids.add(resource_id)
            resource_url = m.group(1)
            title = unescape(re.sub(r'<[^>]+>', ' ', raw_title))
            title = ' '.join(title.split())
            resources.append(Resource(id=resource_id, url=resource_url, title=title))
        for link in RPAGE_LINK_RE.findall(page):
            next_url = unescape(link)
            parsed = urlparse(next_url)
            if parsed.path == start_path and 'rpage=' in parsed.query and next_url not in seen_pages:
                queue.append(next_url)
    return resources


def parse_last_change_date(resource_page: str) -> Optional[str]:
    m = LAST_CHANGE_RE.search(resource_page)
    return m.group(1) if m else None


def parse_download_link(resource_page: str, extension: str) -> Optional[str]:
    m = re.search(r'id="link_%s"[^>]*value="([^"]+)"' % extension, resource_page)
    return unescape(m.group(1)) if m else None


def parse_year(title: str) -> str:
    year_m = YEAR_RANGE_RE.search(title)
    if year_m:
        return year_m.group(2)
    year_m = SINGLE_YEAR_RE.search(title)
    if year_m:
        return year_m.group(1)
    raise ValueError(f'No year found in title: {title}')


def parse_dzi_attributes(title: str) -> tuple[str, str, str]:
    year = parse_year(title)

    month = None
    for pattern, session_month in SESSION_MONTH_PATTERNS:
        if pattern in title:
            month = session_month
            break
    if month is None:
        raise ValueError(f'No session found in DZI title: {title}')

    if 'по желание' in title:
        exam_type = 'i'
    elif 'задължителн' in title:
        exam_type = 'z'
    else:
        raise ValueError(f'No examination type found in DZI title: {title}')

    return year, month, exam_type


def download_file(url: str, target_path: str, force: bool) -> bool:
    if os.path.exists(target_path) and not force:
        logger.info('Already downloaded, skipping: %s', target_path)
        return False

    logger.info('Downloading %s to %s', url, target_path)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return True


def process_resource(resource: Resource, filename: str, extension: str, args: argparse.Namespace) -> None:
    page = fetch_page(resource.url, CACHE_DIR)

    last_change = parse_last_change_date(page)
    if last_change is None:
        logger.warning('No "Последна промяна" found on %s, skipping', resource.url)
        return

    download_url = parse_download_link(page, extension)
    if download_url is None:
        logger.warning('No %s download link found on %s, skipping', extension, resource.url)
        return

    target_path = os.path.join(args.download_dir, filename.format(last_change=last_change, extension=extension))
    download_file(download_url, target_path, args.force)


def download_dzi(args: argparse.Namespace) -> None:
    for resource in collect_resources(DZI_START_URL, CACHE_DIR):
        try:
            year, month, exam_type = parse_dzi_attributes(resource.title)
        except ValueError as e:
            logger.warning('%s, skipping %s', e, resource.url)
            continue
        filename = f'dzi-{year}-{month}-{exam_type}-{resource.id}-{{last_change}}.{{extension}}'
        process_resource(resource, filename, args.extension, args)


def download_nvo(args: argparse.Namespace) -> None:
    for grade, start_url in NVO_START_URLS.items():
        for resource in collect_resources(start_url, CACHE_DIR):
            try:
                year = parse_year(resource.title)
            except ValueError as e:
                logger.warning('%s, skipping %s', e, resource.url)
                continue
            filename = f'nvo-{grade}-{year}-{resource.id}-{{last_change}}.{{extension}}'
            process_resource(resource, filename, args.extension, args)


def main() -> None:
    args = parse_args()
    if args.clean_cache and os.path.isdir(CACHE_DIR):
        logger.info('Cleaning cache directory %s', CACHE_DIR)
        shutil.rmtree(CACHE_DIR)

    os.makedirs(args.download_dir, exist_ok=True)
    download_dzi(args)
    download_nvo(args)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()