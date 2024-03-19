import requests

next_url = "https://hub.docker.com/api/content/v1/products/search?image_filter=official&page=1&page_size=100&q=&type=image"
headers = {"Accept": "application/json", "Search-Version": "v3"}

images_list = []

while next_url:
    res = requests.get(next_url, headers=headers).json()
    next_url = res["next"]
    images = [i["name"] for i in res["summaries"]]
    images_list += images

with open("official_images", "w") as f:
    f.write("\n".join(images_list))
