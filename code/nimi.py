import requests

class Nimifier:
    def __init__(self):
        self.name_file_paths = ["names/place-names.csv", "names/people-names.csv"]
        self.update()

    def update(self):
        self.name_lines = []
        for file_path in self.name_file_paths:
            name_file = requests.get("https://raw.githubusercontent.com/PaulieGlot/lipu-sewi/master/%s" % file_path, "r")
            self.name_lines += name_file.text.splitlines()

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
            if text[i] == "&":
                name = ""
                while i+1 < len(text) and text[i+1].isalpha():
                    name += text[i+1]
                    i += 1
                res += self.get_nimi(name)
            else:
                res += text[i]
            i += 1
        return res