import os, re, csv, requests
import nimi
import discord
from discord import app_commands
from dotenv import load_dotenv


class Engine:
    def __init__(self, repo):
        self.rawurl = "https://raw.githubusercontent.com/%s" % repo
        self.verse_pattern = re.compile(r"(.*)\s+(\d+):(\d+)$")
        self.range_pattern = re.compile(r"(.*)\s+(\d+):(\d+)\-(\d+)$")
        self.nimifier = nimi.Nimifier()

    def get_stats(self) -> str:
        url = self.rawurl + "stats/completion.csv"
        file = requests.get(url)
        for line in file.text.splitlines():
            pass
        line = "as of " + line
        line = line.replace(',', ':', 1)
        line = line.replace(',', ' verses complete - ', 1)
        line = line.replace(',', ' sealed, ', 1)
        line += " cobwebs"
        return line

    def cite(self, citation: str, euphemise: bool) -> str:
        verse_citation = self.verse_pattern.match(citation)
        range_citation = self.range_pattern.match(citation)
        if verse_citation:
            book, chapter, start_verse = verse_citation[1].lower(), int(verse_citation[2]), int(verse_citation[3])
            end_verse = start_verse
        elif range_citation:
            book, chapter = range_citation[1].lower(), int(range_citation[2])
            start_verse, end_verse = int(range_citation[3]), int(range_citation[4])
        else:
            return f"hmm... `{citation}` doesn't quite look like a biblical citation to me."

        try:
            section = self.get_section_name(book)
        except FileNotFoundError:
            return "oh fuck! serious problem! book listing file is missing. get jan Poli immediately!"
        except ValueError:
            return f"hmm... `{citation}` doesn't seem to be on the master list of books. check for typos!"

        url = self.rawurl + f"bible/{section}/{book}/{chapter:04}.txt"
        file = requests.get(url)

        if file.status_code != requests.codes.ok:
            return "oh fuck! serious problem! chapter file is missing. get jan Poli immediately!"

        text = ""
        for line in file.text.splitlines():
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

        if euphemise:
            text = text.replace("&YHWH", "**Nimi**")
        self.nimifier.update()
        return self.nimifier.replace_names(text)

    def get_section_name(self, book: str) -> str:
        with open('bible/chapters.csv', 'r') as file:
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

        self.toc: [(str, int, int), str]= self.load_toc()

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



    def setup_commands(self):
        @self.tree.command(name="cite", description="cite a passage of the translated text", guild=discord.Object(id=self.GUILD_ID))
        async def cite(ctx, citation: str, euphemise: bool = True, post: bool = False):
            text = self.engine.cite(citation, euphemise)
            await self.respond(ctx, text, post)

        @self.tree.command(name="help", description="stop it. get some help", guild=discord.Object(id=self.GUILD_ID))
        async def help(ctx, command: str = None, post: bool = False):
            help_text = {
                None: "/help - display this help text\n/cite - use a biblical citation\n/repo - get a link to the repo\n/stats - get some quick stats",
                "help": "what... what more do you need?",
                "cite": "specify a verse or range using the traditional biblical citation format. make sure you're using the same book names as this version!",
                "repo": "get a link to the repo from which this bot is pulling verses.",
                "stats": "get the recorded stats from the last time buildbook was run."
            }
            await self.respond(ctx, help_text.get(command, "no help available for that command."), post)

        @self.tree.command(name="repo", description="get a link to the repo", guild=discord.Object(id=self.GUILD_ID))
        async def repo(ctx, post: bool = False):
            await self.respond(ctx, "https://github.com/" + self.repo, post)

        @self.tree.command(name="stats", description="get the latest count of completion", guild=discord.Object(id=self.GUILD_ID))
        async def stats(ctx, post: bool = False):
            await self.respond(ctx, self.engine.get_stats(), post)

        @self.tree.command(name="flag", description="updates the ToC link for the specified verse", guild=discord.Object(id=self.GUILD_ID))
        async def flag(ctx, citation: str):
            verse_citation = self.engine.verse_pattern.match(citation)
            if not verse_citation:
                await self.respond(ctx, f"`{citation}` doesn't look like a single-verse citation.", post=False)
                return

            book, chapter, verse = verse_citation[1].lower(), int(verse_citation[2]), int(verse_citation[3])

            await ctx.response.defer()
            msg = await ctx.followup.send(f"🏁\n# {citation}")
            bookmark_url = f"https://discord.com/channels/{ctx.guild.id}/{msg.channel.id}/{msg.id}"
            self.toc[(book, chapter, verse)] = bookmark_url
            self.save_toc()

        @self.tree.command(name="goto", description="fetches the ToC link for the specified verse", guild=discord.Object(id=self.GUILD_ID))
        async def goto(ctx, citation: str, post: bool = False):
            verse_citation = self.engine.verse_pattern.match(citation)
            if not verse_citation:
                await self.respond(ctx, f"`{citation}` doesn't look like a single-verse citation.", post=False)
                return

            book, chapter, verse = verse_citation[1].lower(), int(verse_citation[2]), int(verse_citation[3])
            try:
                await self.respond(ctx, f"{book} {chapter}:{verse} was last bookmarked at: {self.toc[(book, chapter, verse)]}", post)
            except KeyError:
                await self.respond(ctx, f"{book} {chapter}:{verse} has no recorded bookmark.", post)



    async def respond(self, ctx, text, post: bool):
        if len(text) > 2000:
            text = text[:1996] + " ..."
        await ctx.response.send_message(text, ephemeral=not post)

    async def on_ready(self):
        await self.tree.sync(guild=discord.Object(id=self.GUILD_ID))
        print("ready!")

    def run(self):
        self.client.run(self.TOKEN)


if __name__ == "__main__":
    bot = Bot()
    bot.run()