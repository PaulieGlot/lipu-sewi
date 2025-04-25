import os, sys, re
import requests
import csv
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
        if verse_citation is not None:
            book        = verse_citation[1].lower()
            chapter     = int(verse_citation[2])
            start_verse = int(verse_citation[3])
            end_verse   = int(verse_citation[3])
        elif range_citation is not None:
            book        = range_citation[1].lower()
            chapter     = int(range_citation[2])
            start_verse = int(range_citation[3])
            end_verse   = int(range_citation[4])
        else:
            raise ValueError("Incorrect citation format")

        try:
            section = self.get_section_name(book)
        except FileNotFoundError:
            pass

        url = self.rawurl + f"bible/{section}/{book}/{chapter:04}.txt"
        file = requests.get(url)

        if file.status_code != requests.codes.ok:
            raise FileNotFoundError
 
        text = ""
        current_verse = start_verse
        for line in file.text.splitlines():
            prefix = int(line.split(":")[0])
            if prefix > end_verse:
                break
            if prefix >= start_verse:
                line = line.split(' | ', 1)[0]
                if not line.endswith('\n'):
                    line += '\n'
                text += line
        if text == "":
            raise ValueError("No verses in range")


        if euphemise:
            text = text.replace("&YHWH", "**Nimi**")

        return self.nimifier.replace_names(text)

    
    def get_section_name(self, book: str) -> str:
        try:
            file = open('bible/chapters.csv', 'r')
        except FileNotFoundError:
            pass
        csvreader = csv.reader(file)
        next(csvreader)
        for row in csvreader:
            if row[1] == book:
                return row[0]
        raise ValueError("Book not listed")







load_dotenv()
repo = "PaulieGlot/lipu-sewi/master/"
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
engine = Engine(repo)
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def respond(ctx, text, post: bool):
    if len(text) > 2000:
        text = text[:1996] + " ..."
    return ctx.response.send_message(text, ephemeral=not post)

@tree.command(name="cite", description="cite a passage of the translated text", guild=discord.Object(id=GUILD_ID))
async def cite(ctx, citation:str, euphemise: bool=True, post: bool=False):
    try:
        text = engine.cite(citation, euphemise)
    except FileNotFoundError:
        text = "oh fuck! serious problem! book listing file is missing. get jan Poli immediately!"
    except ValueError as error:
        if {error} == "Incorrect citation format":
            text = "hmm... `%s` doesn't quite look like a biblical citation to me." % (citation)
        elif {error} == "Book not listed":
            text = "hmm... `%s` doesn't quite look like a biblical citation to me." % (citation)
        elif {error} == "No verses in range":
            text = "hmm... `%s` doesn't seem to be on the master list of books. check for typos!" % (citation)
    await respond(ctx, text, post)

@tree.command(name="help", description="stop it. get some help", guild=discord.Object(id=GUILD_ID))
async def help(ctx, command: str=None, post: bool=False):
    if command is None:
        await respond(ctx, "/help - display this help text\ncite - use a biblical citation\n/repo - get a link to the repo\n/stats - get some quick stats", post)
    elif command == "help":
        await respond(ctx, "what... what more do you need?", post)
    elif command == "cite":
        await respond(ctx, "specify a verse or range using the traditional biblical citation format. make sure you're using the same book names as this version!", post)
    elif command == "repo":
        await respond(ctx, "get a link to the repo from which this bot is pulling verses.", post)
    elif command == "stats":
        await respond(ctx, "get the recorded stats from the last time buildbook was run.", post)

@tree.command(name="repo", description="get a link to the repo from which this bot is pulling verses", guild=discord.Object(id=GUILD_ID))
async def repo(ctx, post: bool=False):
    await respond(ctx, "https://github.com/" + repo, post)

@tree.command(name="stats", description="get the latest count of completion", guild=discord.Object(id=GUILD_ID))
async def stats(ctx, post: bool=False):
    await respond(ctx, engine.get_stats(), post)

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("ready!")



client.run(TOKEN)