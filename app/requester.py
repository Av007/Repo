import asyncio
import json
import aiofiles
from httpx import AsyncClient
import logging
from os import path, scandir, listdir
from .config import config

logger = logging.getLogger('uvicorn.error')


async def get_request(url, params):
    """
    Request Github API handler
    :param url: github api url
    :param params: github params
    :return: dict
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {config.token}",
    }

    logger.debug(f"Params {params}")

    async with AsyncClient() as client:
        logger.debug(f"Requesting to GitHub API: {url} with params: {params}")
        response = await client.get(url, params=params, headers=headers)
        logger.debug("requesting to github api")
        response.raise_for_status()
    return response.json()

async def get_repos_io(count: int, page: int | None):
    """
    Fetch top GitHub repositories by stars, up to the specified count

    :see https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-repositories
    :param count: number of repositories to fetch
    :param page: current page
    :return: A list of repositories
    """
    url = "https://api.github.com/search/repositories"
    limit = count if not page else 100
    logger.debug(f"Requesting repos with limit:{limit} and count:{count} and page:{page}")
    params = {
        "q": "stars:>1000",
        "sort": "stars",
        "order": "desc",
        "page": page,
        "per_page": limit
    }
    data = await fetch_data(url, params)
    logger.info("complete fetching data")

    tags_tasks = [write_file(item) for item in data]
    await asyncio.gather(*tags_tasks, return_exceptions=True)
    logger.info("complete writing file")

async def get_tags(url):
    logger.debug(f"Requesting {url}...")
    return await get_request(url, {})

async def fetch_data(url, params):
    """
    Fetch data asynchronously

    :param url: github url API endpint
    :param params: github API params
    :return: github API response
    """
    result = []

    response = await get_request(url, params)

    if response['total_count'] > 0:
        tags_tasks = [get_tags(item['tags_url']) for item in response['items']]
        tags_results = await asyncio.gather(*tags_tasks, return_exceptions=True)

        for item, tags in zip(response['items'], tags_results):
            if isinstance(tags, Exception):
                logger.error(f"Error fetching tags for {item['tags_url']}: {tags}")
                item['tags'] = []
            else:
                item['tags'] = tags
            result.append(item)

    return result

async def write_file(data):
    """
    Writing json file to fs
    :param data: repo dto
    """
    file_name = path.join(f"assets/{data["name"]}_{data["id"]}.json")
    logger.info(f"Writing file: {file_name}")
    async with aiofiles.open(f"{file_name}", mode="w") as file:
        await file.write(json.dumps(data, indent=4))

async def read_dir(prefix=None):
    """
    Reading directory
    :param prefix: for matching files by names
    :return: array of files names
    """
    directory = path.join(f"assets/")
    loop = asyncio.get_event_loop()
    with scandir(directory) as dir_fd:
        if prefix:
            logger.info(f"Scanning directory with prefix={prefix}")
            return await loop.run_in_executor(None, lambda: [entry.name for entry in dir_fd if entry.is_file() and entry.name.startswith(prefix)])
        else:
            logger.info(f"Scanning directory")
            return await loop.run_in_executor(None, listdir, directory)

async def read_files(file_path: str, single_file="") -> object:
    """
    Asynchronously read the contents of a file.

    :param file_path: Path to the file.
    :param single_file: Path to the file.
    :return: The content of the file as a string.
    """
    file_name = path.join(f"assets/{file_path}")
    logger.info(f"Reading file: {file_name}")
    async with aiofiles.open(file_name, mode="r") as file:
        content = await file.read()
        data = json.loads(content) if content else None

        if single_file:
            return {
                "name": data['name'],
                "url": data['html_url'],
                "stars": data['stargazers_count'],
                "tags": data['tags'],
            } if data else None
        else:
            return data['name'] if data else None
