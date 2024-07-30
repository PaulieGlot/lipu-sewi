import requests

class nimifier:
    def __init__(self):
        self.name_file_url = "https://raw.githubusercontent.com/PaulieGlot/lipu-sewi/master/names/people-names.csv"
        name_file = requests.get(self.name_file_url, "r")
        self.name_lines = name_file.text.splitlines()

    def update(self):
        name_file = requests.get(self.name_file_url, "r")
        self.name_lines = name_file.text.splitlines()

    def get_nimi(self, name):
        pattern = ",%s" % name
        for name_line in self.name_lines:
            if name_line.endswith(pattern):
                return name_line.split(",")[1]
        return name

    def replace_names(self, text):
        res=""
        i = 0
        while i < len(text):
            if text[i] == "#":
                name = ""
                while i+1 < len(text) and text[i+1].isalpha():
                    name += text[i+1]
                    i += 1
                res += self.get_nimi(name)
            else:
                res += text[i]
            i += 1
        return res