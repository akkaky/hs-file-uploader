import argparse
import asyncio
import json
import os
import time
from typing import Iterable, Iterator, Tuple

import httpx
from httpx import Response
from tqdm import tqdm

EXCLUDED_FILES = (
    '.DS_Store',
)
EXCLUDED_DIRS = (
    '.git',
    '.idea',
    'node_modules',
)
HS_TOKEN = ''  # put here your access token
HEADERS = {
    'Authorization': 'Bearer {}',
}
UPLOAD_FILES_URL = 'https://api.hubapi.com/files/v3'
WORKERS_COUNT = 5
ERRORS = []


async def upload_file(
        file_path: str,
        destination_file_path: str,
        http_client: httpx.AsyncClient,
) -> Response:
    with open(file_path, 'rb') as f:
        file_name = os.path.basename(file_path)
        data = {
            'fileName': file_name,
            'file': f,
            'folderPath': destination_file_path,
            'options': json.dumps(
                {
                    'access': "PUBLIC_INDEXABLE",
                    'overwrite': True,
                }
            )
        }
        res = await http_client.post('/files', files=data)

    return res


def is_excluded(file, root):
    return file in EXCLUDED_FILES or any(d in root for d in EXCLUDED_DIRS)


def get_files(
        source_path: str,
        destination_path: str,
) -> Iterator[Tuple[str, str]]:
    if os.path.isdir(source_path):
        for root, dirs, files in os.walk(os.path.abspath(source_path)):
            for file in files:
                if not is_excluded(file, root):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.dirname(
                        os.path.relpath(file_path, source_path)
                    )
                    destination_file_path = os.path.join(
                        destination_path, relative_path
                    )

                    yield file_path, destination_file_path
    else:
        yield os.path.abspath(source_path), destination_path


async def producer(
        queue: asyncio.Queue,
        files: Iterable[Tuple[str, str]],
) -> None:
    for file in files:
        await queue.put(file)


async def consumer(
        queue: asyncio.Queue,
        http_client: httpx.AsyncClient,
        pbar,
) -> None:
    while True:
        file_path, destination_file_path = await queue.get()

        start = time.monotonic()
        res = await upload_file(file_path, destination_file_path, http_client)
        diff = time.monotonic() - start

        if diff < 1:
            await asyncio.sleep(1 - diff)

        match res.status_code:
            case 200 | 201:
                pbar.write(
                    f'Uploaded {file_path} to {destination_file_path}'
                )
                pbar.update()
            case 429:
                pbar.write(f'Too many requests')
                await queue.put((file_path, destination_file_path))
            case _:
                pbar.write(
                    f'Error upload {file_path} to {destination_file_path}'
                )
                ERRORS.append((file_path, res.status_code))
                pbar.update()

        queue.task_done()


async def main(source: str, dest_folder: str):
    queue = asyncio.Queue(WORKERS_COUNT)
    files = tuple(get_files(source, dest_folder))

    with tqdm(
            desc='Files upload',
            total=len(files),
            dynamic_ncols=True,
    ) as pbar:
        async with httpx.AsyncClient(
                base_url=UPLOAD_FILES_URL,
                headers=HEADERS,
                timeout=60.0 * 1,
        ) as http_client:

            for _ in range(WORKERS_COUNT):
                asyncio.create_task(consumer(queue, http_client, pbar))

            await asyncio.create_task(producer(queue, files))
            await queue.join()

    if ERRORS:
        print(f"\n!!!ERROR!!!\n{len(ERRORS)} files weren't uploaded:")
        for file, status_code in ERRORS:
            print(f'Status code {status_code} ==> {file}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Simple script for uploading files to Hubspot'
    )
    parser.add_argument(
        '-s', '--source',
        type=str,
        required=True,
        help='Path to the folder or file to upload'
    )
    parser.add_argument(
        '-d', '--destination',
        type=str,
        default='/',
        help='Destination folder on Hubspot file manager. Default path "/"',
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    token = os.environ.get('HS_TOKEN') or HS_TOKEN

    if token:
        HEADERS['Authorization'] = HEADERS['Authorization'].format(token)
        asyncio.run(main(args.source, args.destination))
    else:
        print('No Hubspot API access token')
