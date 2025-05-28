import csv
import os
import re

import bookaliases
import discord
import nimi
import requests
from discord import app_commands
from dotenv import load_dotenv


class Engine:
    def __init__(self, repo):
        self.rawurl = f"https://raw.githubusercontent.com/{repo}"
        self.verse_pattern = re.compile(r"(.*)\s+(\d+):(\d+)$")
        self.range_pattern = re.compile(r"(.*)\s+(\d+):(\d+)\-(\d+)$")
        self.nimifier = nimi.Nimifier()
        self.aliases = bookaliases.BOOK_ALIASES

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

    def normalize_book_name(self, name: str) -> str:
        name = name.strip().lower().replace(".", "")
        name_no_space = name.replace(" ", "")
        return self.aliases.get(name_no_space, name)

    def cite(self, citation: str, euphemise: bool) -> str:
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

        self.toc: [(str, int, int), str] = self.load_toc()
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
            # Normalize the book name
            normalized_book = self.engine.normalize_book_name(book)
            updated_toc[(normalized_book, chapter, verse)] = url

        # Replace the old toc with the updated one
        self.toc = updated_toc
        self.save_toc()  # Save the updated ToC with normalized keys

    def setup_commands(self):

        @self.tree.command(name="cite",
                           description="cite a passage of the translated text",
                           guild=discord.Object(id=self.GUILD_ID))
        async def cite(ctx,
                       citation: str,
                       euphemise: bool = True,
                       post: bool = False):
            text = self.engine.cite(citation, euphemise)
            await self.respond(ctx, text, post)

        @self.tree.command(name="help",
                           description="stop it. get some help",
                           guild=discord.Object(id=self.GUILD_ID))
        async def help(ctx, command: str = None, post: bool = False):
            help_text = {
                None:
                "/help - display this help text\n/cite - use a biblical citation\n/repo - get a link to the repo\n/stats - get some quick stats",
                "help":
                "what... what more do you need?",
                "cite":
                "specify a verse or range using the traditional biblical citation format. make sure you're using the same book names as this version!",
                "repo":
                "get a link to the repo from which this bot is pulling verses.",
                "stats":
                "get the recorded stats from the last time buildbook was run."
            }
            await self.respond(
                ctx,
                help_text.get(command, "no help available for that command."),
                post)

        @self.tree.command(name="repo",
                           description="get a link to the repo",
                           guild=discord.Object(id=self.GUILD_ID))
        async def repo(ctx, post: bool = False):
            await self.respond(ctx, "https://github.com/" + self.repo, post)

        @self.tree.command(name="stats",
                           description="get the latest count of completion",
                           guild=discord.Object(id=self.GUILD_ID))
        async def stats(ctx, post: bool = False):
            await self.respond(ctx, self.engine.get_stats(), post)

        @self.tree.command(
            name="flag",
            description="updates the ToC link for the specified verse",
            guild=discord.Object(id=self.GUILD_ID))
        async def flag(ctx, citation: str, confirm: bool = False):
            if not isinstance(ctx.channel, discord.Thread):
                await self.respond(ctx,
                                   "This command must be run inside a thread.",
                                   post=False)
                return

            verse_citation = self.engine.verse_pattern.match(citation)
            if not verse_citation:
                await self.respond(
                    ctx,
                    f"`{citation}` doesn't look like a single-verse citation.",
                    post=False)
                return

            book, chapter, verse = verse_citation[1].lower(), int(
                verse_citation[2]), int(verse_citation[3])
            normalized_book = self.engine.normalize_book_name(book)
            thread_url = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.parent_id}/{ctx.channel.id}"

            # check for conflicts
            existing_url = self.toc.get((normalized_book, chapter, verse))
            thread_is_used = None
            for (b, c, v), url in self.toc.items():
                if url == thread_url and (b, c, v) != (normalized_book,
                                                       chapter, verse):
                    thread_is_used = (b, c, v)
                    break

            if existing_url and existing_url != thread_url:
                if not confirm:
                    await self.respond(
                        ctx,
                        f"⚠️ `{normalized_book} {chapter}:{verse}` is already flagged in another thread:\n{existing_url}\n\nif this is intentional, please re-run the command with `confirm: true`.",
                        post=False)
                    return

            if thread_is_used:
                if not confirm:
                    b, c, v = thread_is_used
                    await self.respond(
                        ctx,
                        f"⚠️ this thread is already linked to another verse: `{b} {c}:{v}`\n\nif this is intentional, please re-run the command with `confirm: true`.",
                        post=False)
                    return

            # prevent unnecessary confirmations - lazy humans!
            if confirm and not existing_url and not thread_is_used:
                await self.respond(
                    ctx,
                    "⚠️ there's no conflict here - you don't need to confirm anything.\n\nplease re-run without `confirm: True`.",
                    post=False)
                return

            # passed all checks. safe to flag
            await ctx.response.defer()
            await ctx.followup.send(
                f"🏁 flagged verse: **{normalized_book} {chapter}:{verse}** is at {thread_url}"
            )
            self.toc[(normalized_book, chapter, verse)] = thread_url
            self.save_toc()

        @self.tree.command(
            name="goto",
            description="fetches the ToC link for the specified verse",
            guild=discord.Object(id=self.GUILD_ID))
        async def goto(ctx, citation: str, post: bool = False):
            verse_citation = self.engine.verse_pattern.match(citation)
            if not verse_citation:
                await self.respond(
                    ctx,
                    f"`{citation}` doesn't look like a single-verse citation.",
                    post=False)
                return

            book, chapter, verse = verse_citation[1].lower(), int(
                verse_citation[2]), int(verse_citation[3])
            normalized_book = self.engine.normalize_book_name(book)
            try:
                await self.respond(
                    ctx,
                    f"{normalized_book} {chapter}:{verse} was last bookmarked at: {self.toc[(normalized_book, chapter, verse)]}",
                    post)
            except KeyError:
                await self.respond(
                    ctx,
                    f"{normalized_book} {chapter}:{verse} has no recorded bookmark.",
                    post)

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
