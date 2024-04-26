#!/usr/bin/env python3

import sys
import os
import logging
import requests


logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', os.path.join(SCRIPT_DIR, 'downloads'))


def main():
    csv = sys.argv[1]
    with open(csv, 'rt') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            name, url = line.split(',')
            if url:
                filename = url.split('/')[-1]
                target_file = os.path.join(DOWNLOAD_DIR, f'{name}-{filename}.csv')

                if not os.path.exists(target_file):
                    # TODO: fix this
                    url = f'https://data.egov.bg/resource/download/{filename}/csv'
                    logger.info('Downloading %s to %s', url, target_file)

                    with requests.get(f'{url}', stream=True) as r:
                        r.raise_for_status()
                        with open(target_file, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                else:
                    logger.info('URL %s is already downloaed to %s', url, target_file)


if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
