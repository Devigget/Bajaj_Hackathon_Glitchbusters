import requests

def download(url: str, dest_path: str) -> str:
    r = requests.get(url)
    r.raise_for_status()
    with open(dest_path, 'wb') as f:
        f.write(r.content)
    return dest_path
