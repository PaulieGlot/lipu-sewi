import csv
import os
import re
import aiohttp

import bookaliases
import discord
import nimi

from discord import app_commands
from dotenv import load_dotenv


class Engine:
    def __init__(self, repo):
        self.rawurl = f"https://raw.githubusercontent.com/{repo}"
        self.verse_pattern = re.compile(r"(.*)\s+(\d+):(\d+)$")
        self.range_pattern = re.compile(r"(.*)\s+(\d+):(\d+)\-(\d+)$")
        self.nimifier = nimi.Nimifier()
        self.aliases = bookaliases.BOOK_ALIASES

    async def async_init(self):
        await self.nimifier.update()

    async def get_stats(self) -> str:
        url = self.rawurl + "stats/completion.csv"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return "error fetching stats."
                text = await resp.text()
                for line in text.splitlines():
                    pass
                line = "as of " + line
                line = line.replace(',', ':', 1)
                line = line.replace(',', ' verses complete - ', 1)
                line = line.replace(',', ' sealed, ', 1)
                line += " cobwebs"
                return line

    def normalize_book_name(self, name: str) -> str:
        name = name.strip().lower().replace(".", "")
        name_no_space = name.replace(" ", "")
        return self.aliases.get(name_no_space, name)

    async def cite(self, citation: str, euphemise: bool) -> str:
        verse_citation = self.verse_pattern.match(citation)
        range_citation = self.range_pattern.match(citation)

        if verse_citation:
            raw_book = verse_citation[1]
            chapter = int(verse_citation[2])
            start_verse = int(verse_citation[3])
            end_verse = start_verse
        elif range_citation:
            raw_book = range_citation[1]
            chapter = int(range_citation[2])
            start_verse = int(range_citation[3])
            end_verse = int(range_citation[4])
        else:
            return f"hmm... `{citation}` doesn't quite look like a biblical citation to me."

        book = self.normalize_book_name(raw_book)

        try:
            section = self.get_section_name(book)
        except FileNotFoundError:
            return "oh fuck! serious problem! book listing file is missing. get jan Poli immediately!"
        except ValueError:
            return f"hmm... `{citation}` doesn't seem to be on the master list of books. check for typos!"

        url = self.rawurl + f"bible/{section}/{book}/{chapter:04}.txt"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as file:
                if file.status != 200:
                    return "oh fuck! serious problem! chapter file is missing. get jan Poli immediately!"
                text = ""
                contents = await file.text()
                for line in contents.splitlines():
                    prefix = int(line.split(":")[0])
                    if prefix > end_verse:
                        break
                    if prefix >= start_verse:
                        line = line.split(' | ', 1)[0]
                        if not line.endswith('\n'):
                            line += '\n'
                        text += line

        if not text:
            return f"hmm... `{citation}` doesn't seem to contain any verses - not yet, anyway."

        text = self.nimifier.replace_names(text)

        if euphemise:
            text = text.replace("Jawe", "**Nimi**")

        return text

    def get_section_name(self, book: str) -> str:
        with open('bible/chapters.csv', 'r', encoding="utf-8") as file:
            csvreader = csv.reader(file)
            next(csvreader)
            for row in csvreader:
                if row[1] == book:
                    return row[0]
        raise ValueError


class Bot:
    TOC_FILE = "toc.csv"

    def __init__(self):
        load_dotenv()
        self.repo = "PaulieGlot/lipu-sewi/master/"
        self.engine = Engine(self.repo)

        self.toc = self.load_toc()
        self.normalize_existing_bookmarks()

        self.TOKEN = os.getenv('DISCORD_TOKEN')
        self.GUILD_ID = os.getenv('GUILD_ID')

        intents = discord.Intents.default()
        intents.messages = True
        self.client = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.client)

        self.setup_commands()
        self.client.event(self.on_ready)

    def load_toc(self):
        toc = {}
        if os.path.exists(self.TOC_FILE):
            with open(self.TOC_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 4:
                        book, chapter, verse, url = row
                        toc[(book, int(chapter), int(verse))] = url
        return toc

    def save_toc(self):
        with open(self.TOC_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for (book, chapter, verse), url in self.toc.items():
                writer.writerow([book, chapter, verse, url])

    def normalize_existing_bookmarks(self):
        updated_toc = {}
        for (book, chapter, verse), url in self.toc.items():
            normalized_book = self.engine.normalize_book_name(book)
            updated_toc[(normalized_book, chapter, verse)] = url
        self.toc = updated_toc
        self.save_toc()

    def setup_commands(self):
        # [All your commands remain unchanged; omitted here for brevity]

        # ✅ They already use await self.engine.cite(...) and self.engine.get_stats()

        pass  # replace with your full set of commands

    async def respond(self, ctx, text, post: bool):
        if len(text) > 2000:
            text = text[:1996] + " ..."
        await ctx.response.send_message(text, ephemeral=not post)

    async def on_ready(self):
        await self.engine.async_init()  # ✅ load name lists async
        await self.tree.sync(guild=discord.Object(id=self.GUILD_ID))
        print("ready!")

    def run(self):
        self.client.run(self.TOKEN)


if __name__ == "__main__":
    bot = Bot()
    bot.run()
