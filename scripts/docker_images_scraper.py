import requests

next_url = "https://hub.docker.com/api/search/v4?badges=official&size=100&query=&type=image"
headers = {"Accept": "application/json"}

ses = requests.Session()
images_list = []
deprecated = []
res = ses.get(next_url, headers=headers).json()
total = res["total"]
current = 0

while current < total:
    for elem in res["results"]:
        if "deprecate" in elem["short_description"].lower():
            deprecated.append(elem["name"])
        else:   
            images_list.append(elem["name"])
    current += len(res["results"])
    if current < total:
        res = ses.get(next_url + f"&from={current}", headers=headers).json()

with open("official_docker_images", "w") as f:
    images_list.sort()
    f.write("\n".join(images_list))

with open("deprecated_official_docker_images", "w") as f:
    deprecated.sort()
    f.write("\n".join(deprecated))

