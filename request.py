import requests


url = 'https://raw.githubusercontent.com/PaulieGlot/lipu-sewi/master/Bible/chapters.txt'
page = requests.get(url)
if page.status_code == requests.codes.ok:
    for line in page.text.splitlines():
        print(line)
else:
    print('Content was not found.')
