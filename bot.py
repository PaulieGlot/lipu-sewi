import os, sys, discord
from discord import app_commands
from dotenv import load_dotenv

# pull a verse from a chapter file
def get_verse(section, book, chapter, verse):
    filename = "Bible/%s/%s/%s.txt" % (section, book, f"{chapter:04}")
    try: file = open(filename)
    except FileNotFoundError: return "error fetching verse: chapter file `%s` does not exist.\n\n*jan Poli says: check chapters.txt to see if it should!*\n" % filename
    for line in file:
        prefix = "%i: " % verse
        if line.startswith(prefix):
            return line
    return "error fetching verse: chapter file `%s` contains no verse numbered %i.\n\n*jan Poli says: be sure you are using the same numbering system as this version, and that a translation has been supplied for the requested verse.*\n" % (filename, verse)


# quickly pull all completed verses within a chapter
def get_chapter(section, book, chapter):
    filename = "Bible/%s/%s/%s.txt" % (section, book, f"{chapter:04}")
    try: file = open(filename)
    except FileNotFoundError: return "error fetching chapter: chapter file `%s` does not exist.\n\n*jan Poli says: check chapters.txt to see if it should!*\n" % filename
    text = ""
    for line in file:
        text += line
    return text


# quickly pull all completed verses within a range
def get_verse_range(section: str, book: str, chapter: int, start_verse: int, end_verse: int):
    filename = "Bible/%s/%s/%s.txt" % (section, book, f"{chapter:04}")
    try: file = open(filename)
    except FileNotFoundError: return "error fetching verse range: chapter file `%s` does not exist.\n\n*jan Poli says: check chapters.txt to see if it should!*\n" % filename
    text = ""
    current_verse = start_verse
    for line in file:
        prefix = int(line.split(":")[0])
        if prefix >= start_verse:
            text += line
        if prefix > end_verse:
            break
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
def get_section_name(book):
    try: file = open("Bible/chapters.txt")
    except FileNotFoundError: return "error finding section name: chapters.txt file does not exist.\n\n*jan Poli says: make sure that it is properly named and located!*\n" % filename
    section = ""
    for line in file:
        if line.startswith("#"):
            section = line.removeprefix("#")
        if line.startswith("%s," % book):
            return section.removesuffix("\n")
    return "error finding section name: book `%s` is not listed in chapters.txt.\n\n*jan Poli says: make sure you're using the same book names as this version, and that you have all planned books listed along with their chapter lengths!*" % book


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="verse", description="pull a verse from the translated text", guild=discord.Object(id=GUILD_ID))
async def verse(ctx, book: str, chapter: int, verse: int):
    section = get_section_name(book)
    if section.startswith("error"):
        await ctx.response.send_message(section)
        return
    text = get_verse(section, book, chapter, verse)
    if len(text) > 2000:
        text = "error crafting message: requested range contains too many characters.\n\n*jan Poli says: wow, this is a pickle. i really didn't think we'd have a verse this long.*\n"
    await ctx.response.send_message(text)


@tree.command(name="range", description="pull a range of verses from the translated text", guild=discord.Object(id=GUILD_ID))
async def range(ctx, book: str, chapter: int, start_verse: int, end_verse: int):
    section = get_section_name(book)
    if section.startswith("error"):
        await ctx.response.send_message(section)
        return
    text = get_verse_range(section, book, chapter, start_verse, end_verse)
    if len(text) > 2000:
        text = "error crafting message: requested range contains too many characters.\n\n*jan Poli says: try narrowing your range a bit. surely you don't need every one of those verses all at once, right?*\n"
    await ctx.response.send_message(text)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("ready!")

client.run(TOKEN)
