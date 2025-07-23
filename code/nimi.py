import aiohttp

class Nimifier:
    def __init__(self):
        self.name_file_paths = [
            "names/place-names.csv",
            "names/people-names.csv"
        ]
        self.name_lines = []

    async def update(self):
        self.name_lines = []
        async with aiohttp.ClientSession() as session:
            for file_path in self.name_file_paths:
                url = f"https://raw.githubusercontent.com/PaulieGlot/lipu-sewi/master/{file_path}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        self.name_lines += text.splitlines()
                    else:
                        print(f"Warning: Failed to fetch {file_path}")

    def get_nimi(self, name):
        pattern = f",{name}"
        for name_line in self.name_lines:
            if name_line.endswith(pattern):
                return name_line.split(",")[1]
        return name

    def replace_names(self, text):
        res = ""
        i = 0
        while i < len(text):
            if text[i] == "&":
                name = ""
                while i + 1 < len(text) and text[i + 1].isalpha():
                    name += text[i + 1]
                    i += 1
                res += self.get_nimi(name)
            else:
                res += text[i]
            i += 1
        return res
