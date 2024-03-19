import requests
from bs4 import BeautifulSoup

URL = "https://docstore.mik.ua/orelly/unix3/unixnut/appb_02.htm"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")
table = soup.find("table", cellpadding="5", border="1")
tds = table.find_all("td", valign="top")
obsolete = [td.text for td in tds if len(td) == 1]

with open("obsolete_commands", "w") as f:
    f.write("\n".join(obsolete))
