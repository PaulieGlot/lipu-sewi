import os, sys, re
import discord
import requests
import csv
from discord import app_commands
from dotenv import load_dotenv
import nimi



def get_stats():
    url = 'https://raw.githubusercontent.com/PaulieGlot/lipu-sewi/master/stats/completion.csv'
    file = requests.get(url)
    for line in file.text.splitlines():
        pass

    line = "as of " + line
    line = line.replace(',', ':', 1)
    line = line.replace(',', ' verses complete - ', 1)
    line = line.replace(',', ' sealed, ', 1)
    line += " cobwebs"
    

    return line

# pull a verse from a chapter file
def get_verse(section: str, book: str, chapter: int, verse: int):
    filename = f"bible/{section}/{book}/{chapter:04}.txt"
    url = 'https://raw.githubusercontent.com/PaulieGlot/lipu-sewi/master/%s' % filename
    file = requests.get(url)
    if file.status_code != requests.codes.ok:
        return "error fetching verse: chapter file `%s` does not exist.\n\n*jan Poli says: check chapters.txt to see if it should!*\n" % filename
    
    for line in file.text.splitlines():
        prefix = "%i: " % verse
        if line.startswith(prefix):
            line = line.split(' | ', 1)[0]
            if not line.endswith('\n'):
                line += '\n'
            return line
    return "error fetching verse: chapter file `%s` contains no verse numbered %i.\n\n*jan Poli says: be sure you are using the same numbering system as this version, and that a translation has been supplied for the requested verse.*\n" % (filename, verse)


# quickly pull all completed verses within a chapter
def get_chapter(section: str, book: str, chapter: int): 
    filename = f"bible/{section}/{book}/{chapter:04}.txt"
    try: file = open(filename)
    except FileNotFoundError: return "error fetching chapter: chapter file `%s` does not exist.\n\n*jan Poli says: check chapters.txt to see if it should!*\n" % filename
    text = ""
    for line in file:
        line = line.split(' | ', 1)[0]
        if not line.endswith('\n'):
            line += '\n'
        text += line
    return text


# quickly pull all completed verses within a range
def get_verse_range(section: str, book: str, chapter: int, start_verse: int, end_verse: int):
    filename = f"bible/{section}/{book}/{chapter:04}.txt"
    url = 'https://raw.githubusercontent.com/PaulieGlot/lipu-sewi/master/%s' % filename
    file = requests.get(url)
    if file.status_code != requests.codes.ok:
        return "error fetching verse: chapter file `%s` does not exist.\n\n*jan Poli says: check chapters.txt to see if it should!*\n" % filename
    
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
        return "error fetching verse range: chapter file `%s` contains no verses within the range %i - %i.\n\n*jan Poli says: be sure you are using the same numbering system as this version, and that translations have been supplied for verses in the requested range.*\n" % (filename, start_verse, end_verse)
    return text


# pull all completed verses and errors when requested verses aren't found (somewhat slower)
def check_verse_range(section: str, book: str, chapter: int, start_verse: int, end_verse: int):
    text = ""
    errors = []
    for verse in range(start_verse, end_verse+1):
        checkverse = get_verse(section, book, chapter, verse)
        if checkverse.startswith("error"):
            errors.append(verse)
            continue
        text += checkverse
    error = ""
    if len(errors) > 0:
        error = "error fetching verses: translations could not be found for verses "
        for verse in errors:
            error += "%i " % verse
    text += error + "\n"
    return text


# get section name for a book
def get_section_name(book: str):

    try: file = open('bible/chapters.csv', 'r')
    except FileNotFoundError: return "error finding section name: chapters.csv file does not exist.\n\n*jan Poli says: make sure that it is properly named and located!*\n" % filename
    csvreader = csv.reader(file)
    next(csvreader)
    for row in csvreader:
        if row[1] == book:
            return row[0]
    return "error finding section name: book `%s` is not listed in chapters.txt.\n\n*jan Poli says: make sure you're using the same book names as this version, and that you have all planned books listed along with their chapter lengths!*" % book
    '''
    section = ""
    for line in file:
        if line.startswith("#"):
            section = line.removeprefix("#")
        if line.startswith("%s," % book):
            return section.removesuffix("\n")
    return "error finding section name: book `%s` is not listed in chapters.txt.\n\n*jan Poli says: make sure you're using the same book names as this version, and that you have all planned books listed along with their chapter lengths!*" % book
    '''


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
nimifier = nimi.Nimifier()

def respond(ctx, text, post: bool, euphemise: bool = True):
    nimifier.update()
    text = nimifier.replace_names(text)
    if euphemise:
        text = re.sub(r"\bJawe\b", "**Nimi**", text)
    if len(text) > 2000:
        text = text[:1996] + " ..."
    return ctx.response.send_message(text, ephemeral=not post)


@tree.command(name="verse", description="pull a verse from the translated text", guild=discord.Object(id=GUILD_ID))
async def verse(ctx, book: str, chapter: int, verse: int, euphemise: bool=True, post: bool=False):
    book = book.lower()
    section = get_section_name(book)
    if section.startswith("error"):
        await respond(ctx, section, post)
        return
    text = get_verse(section, book, chapter, verse)
    await respond(ctx, text, post, euphemise)


@tree.command(name="range", description="pull a range of verses from the translated text", guild=discord.Object(id=GUILD_ID))
async def range(ctx, book: str, chapter: int, start_verse: int, end_verse: int, euphemise: bool=True, post: bool=False):
    book = book.lower()
    section = get_section_name(book)
    if section.startswith("error"):
        await respond(ctx, section, post)
        return
    text = get_verse_range(section, book, chapter, start_verse, end_verse)
    await respond(ctx, text, post, euphemise)

@tree.command(name="cite", description="cite a passage from the translated text", guild=discord.Object(id=GUILD_ID))
async def cite(ctx, citation: str, euphemise: bool=True, post: bool=False):
    verse_pattern = re.compile(r"(.*)\s+(\d+):(\d+)$")
    range_pattern = re.compile(r"(.*)\s+(\d+):(\d+)\-(\d+)$")
    verse_citation = verse_pattern.match(citation)
    range_citation = range_pattern.match(citation)

    if verse_citation is not None:
        book = verse_citation[1].lower()
        section = get_section_name(book)
        if section.startswith("error"):
            await respond(ctx, section, post, euphemise=False)
            return
        text = get_verse(section, book, int(verse_citation[2]), int(verse_citation[3]))
    elif range_citation is not None:
        book = range_citation[1].lower()
        section = get_section_name(book)
        if section.startswith("error"):
            await respond(ctx, section, post, euphemise)
            return
        text = get_verse_range(section, book, int(range_citation[2]), int(range_citation[3]), int(range_citation[4]))
    else:
        text = "error parsing citation: `%s` does not seem to be formatted as a proper citation." % citation
    await respond(ctx, text, post, euphemise)

@tree.command(name="help", description="stop it. get some help", guild=discord.Object(id=GUILD_ID))
async def help(ctx, command: str=None, post: bool=False):
    if command is None:
        await respond(ctx, "/help - display this help text\n/verse - fetch a specified verse\n/range - fetch a specified range of verses\ncite - use a biblical citation\n/repo - get a link to the repo\n/stats - get some quick stats", post)
    elif command == "help":
        await respond(ctx, "what... what more do you need?", post)
    elif command == "verse":
        await respond(ctx, "specify a verse using the command parameters. make sure you're using the same book names as this version!", post)
    elif command == "range":
        await respond(ctx, "specify a range of verses using the command parameters. make sure you're using the same book names as this version!", post)
    elif command == "cite":
        await respond(ctx, "specify a verse or range using the traditional biblical citation format. make sure you're using the same book names as this version!", post)
    elif command == "repo":
        await respond(ctx, "get a link to the repo from which this bot is pulling verses.", post)
    elif command == "stats":
        await respond(ctx, "get the recorded stats from the last time buildbook was run.", post)


@tree.command(name="repo", description="get a link to the repo from which this bot is pulling verses", guild=discord.Object(id=GUILD_ID))
async def repo(ctx, post: bool=False):
    await respond(ctx, "https://github.com/PaulieGlot/lipu-sewi/tree/master", post)

@tree.command(name="stats", description="get the latest count of completion", guild=discord.Object(id=GUILD_ID))
async def stats(ctx, post: bool=False):
    await respond(ctx, get_stats(), post)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("ready!")

client.run(TOKEN)
