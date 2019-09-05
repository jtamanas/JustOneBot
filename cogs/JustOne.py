import random
import asyncio
import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context, command, Cog
import cogs.insulter as insulter

import logging
log = logging.getLogger(__name__)


class JustOne(commands.Cog):
    """
    A selection of commands for running the cooperative party game Just One
    """
    def __init__(self, bot: Bot):
        self.bot = bot

        # round data
        self.players = []
        self.hints = []
        self.cmd_prefix = "!"
        self.default_answer = "jsdhf"
        self.answer = self.default_answer
        self.guess_msg = "sfhiouwehf"
        self.gave_hint = []

        # Game settings
        self.round_delay = 25
        self.game_channel_id = 618957002554736652
        self.voice_channel_id = 618922677838544910
        self.num_rounds = 13

        # Game flags
        self.game_started = False
        self.registration = False
        self.hint_round = False
        self.guess_round = False
        self.round_count = 0
        self.points = 0
        # generate random word list
        rand_words = random.choices(list(open('word_list.txt')), k=self.num_rounds)
        self.all_secret_words = [word.rstrip().title() for word in rand_words]

    def reset_hint_data(self):
        self.hints = []
        self.cmd_prefix = "!"
        self.default_answer = "jsdhf"
        self.answer = self.default_answer
        self.guess_msg = "sfhiouwehf"
        self.gave_hint = []

    def reset_game(self):
        self.reset_hint_data()
        self.players = []
        # Game flags
        self.game_started = False
        self.registration = False
        self.hint_round = False
        self.guess_round = False
        self.round_count = 0
        self.points = 0
        # generate random word list
        rand_words = random.choices(list(open('word_list.txt')), k=self.num_rounds)
        self.all_secret_words = [word.rstrip().title() for word in rand_words]

    def get_secret_word(self):
        return self.all_secret_words[self.round_count]

    async def post_secret_word(self):
        await self.channel.send('The secret word is "{}". '.format(self.secret_word))

    def generate_turn_order(self):
        n_players = len(self.players)
        random_start = random.choice([i for i in range(n_players)])
        guess_order = [(i+random_start) % n_players for i in range(self.num_rounds)]
        self.guess_order = guess_order

    async def set_player_roles(self, players):
        g_ind = self.guess_order[self.round_count]
        guesser = players[g_ind]
        hinters = players[:g_ind] + players[(g_ind + 1):]
        self.guesser = guesser
        self.hinters = hinters

    async def assign_players(self):
        for hinter in self.players:
            role = self.player_role
            await hinter.add_roles(role)

    async def assign_quiets(self):
        for hinter in self.players:
            role = self.quiet_role
            await hinter.add_roles(role)

    async def assign_blinds(self):
        role = self.blind_role
        await self.guesser.add_roles(role)

    async def assign_amnesias(self):
        role = self.amnesia_role
        await self.guesser.add_roles(role)

    async def remove_players(self):
        for hinter in self.players:
            role = self.player_role
            await hinter.remove_roles(role)

    async def remove_quiets(self):
        for hinter in self.players:
            role = self.quiet_role
            await hinter.remove_roles(role)

    async def remove_blinds(self):
        role = self.blind_role
        await self.guesser.remove_roles(role)

    async def remove_amnesias(self):
        role = self.amnesia_role
        await self.guesser.remove_roles(role)

    def play_guess_tone(self):
        self.vc.play(discord.FFmpegPCMAudio('cogs/sounds/guess_tone.mp3'))

    async def hints_post(self):
        title = "Secret Word"
        if self.hint_round:
            title = self.secret_word
        embed = Embed(title=title, color=0xeee657)
        # add hints
        if not self.hints:
            self.hints = ["No hints given!"]
        hints = self.hints
        hints.sort()
        hints = [str(i+1) + ". " + hint for i, hint in enumerate(hints)]
        hint_msg_content = "\n".join(hints)

        # bot commands here
        embed.add_field(name="Hints", value=hint_msg_content)

        hint_msg = await self.channel.send('', embed=embed)
        if self.hint_round:  # not needed during guess phase
            emoji_nums = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
            for i, hint in enumerate(hints):
                await hint_msg.add_reaction(emoji_nums[i])
        return hint_msg

    async def del_bad_hints(self, hint_msg):
        hint_msg =  discord.utils.get(self.bot.cached_messages, id=hint_msg.id)
        reacts = hint_msg.reactions
        dels = []
        for i, react in enumerate(reacts):
            if react.count > 1:
                dels.append(i)
        # delete all of the clues with non-zero votes
        # reverse dels so we don't mess up indices of other elements
        dels.reverse()

        hints = self.hints
        for del_ind in dels:
            hints.pop(del_ind)
        self.hints = hints

    async def start_vote_on_guess(self):
        thumbs_up = '👍'
        thumbs_down = '👎'
        await self.guess_msg.add_reaction(thumbs_up)
        await self.guess_msg.add_reaction(thumbs_down)
        await self.channel.send("React with {} if this is correct, "
                            "react with {} if it's not".format(thumbs_up, thumbs_down))

    async def update_score(self):
        ess = "s"
        if type(self.guess_msg) != str:
            reacts = self.guess_msg.reactions
            if len(reacts) > 0:
                react_counts = [react.count for react in reacts]
                if react_counts[0] > react_counts[1]:
                    self.points += 1
                    if self.points == 1:
                        ess = ""
                    await self.channel.send("You got it right! You now have {} point".format(self.points)+ess)
                elif react_counts[0] < react_counts[1]:
                    insult = insulter.gen_insult("cogs/insulter/")
                    await self.channel.send("That was wrong, you {}. You still have {} point".format(insult, self.points)+ess)
                else:
                    await self.channel.send("We did not reach a consensus... You still have {} point".format(self.points)+ess)
        else:
            pass

    async def post_final_score(self):
        title = "Your final score is: {}".format(self.points)
        embed = Embed(title=title, color=0xeee657)
        pts = self.points
        if pts < 4:
            msg = "Try again, and again, and again."
        elif 4 <= pts <= 6:
            msg = "That's a good start. Try again!"
        elif 7 <= pts <= 8:
            msg = "You're in the average. Can you do better?"
        elif 9 <= pts <= 10:
            msg = "Wow, not bad at all!"
        elif pts == 11:
            msg = "Awesome! That's a score worth celebrating!"
        elif pts == 12:
            msg = "Incredible! Your friends must be impressed!"
        elif pts >= 13:
            msg = "Perfect score! Can you do it again?"

        embed.add_field(name="Takeaway", value=msg)
        await self.channel.send('', embed=embed)

    def is_answer(self, message):
        is_in_quotes = message.content[:1] == "'" or message.content[:1] == '"'
        is_from_guesser = message.author == self.guesser and message.channel == self.channel
        return self.guess_round and is_in_quotes and is_from_guesser

    def is_hint(self, message):
        is_in_quotes = message.content[:1] == "'" or message.content[:1] == '"'
        is_from_hinter = message.author in self.hinters

        # add restrictions to number of hints per author
        author_cnt = self.gave_hint.count(message.author)
        can_add_more_hints = author_cnt == 0 or (len(self.players) <= 3 and author_cnt < 2)

        full_condition = self.hint_round and is_in_quotes and is_from_hinter and can_add_more_hints

        if full_condition:
            self.gave_hint.append(message.author)

        return full_condition

    async def begin_round(self):
        await self.channel.send("**-------- Beginning Round {} --------**".format(self.round_count+1))

        if self.round_count == 0:
            self.generate_turn_order()
        await self.set_player_roles(self.players)
        await self.assign_blinds()
        await self.assign_players()  # give everyone the hinter role so guesser can see channel after
        await self.assign_quiets()

        # Start hint phase
        self.hint_round = True
        self.secret_word = self.get_secret_word()
        await self.post_secret_word()
        await self.channel.send('DM me your clues wrapped in quotation marks, e.g. "clue".')

        # Register hints
        num_clues = max(3, len(self.hinters))
        for i in range(num_clues):
            try:
                self.hint_msg = await self.bot.wait_for('message', check=self.is_hint, timeout=self.round_delay)
                hint = self.hint_msg.content
                if hint[0] == "'":
                    self.hints.append(hint.split("'")[1])
                else:
                    self.hints.append(hint.split('"')[1])
            except asyncio.TimeoutError:
                pass

        # End hint phase and begin guessing phase
        self.hint_round = False
        self.guess_round = True

        # Post hints
        await self.remove_quiets()
        hint_msg = await self.hints_post()

        await asyncio.sleep(self.round_delay)

        # Delete hints that were voted off
        await self.del_bad_hints(hint_msg)  # edits self.hints

        # Post edited hints
        await self.assign_amnesias()
        await self.remove_blinds()
        await self.hints_post()

        if self.hint_round:
            await self.channel.send('Wrap your clue in quotation marks, e.g. "clue".'
                                    'Remember, one word clues only!')
        elif self.guess_round:
            self.play_guess_tone()  # sound alert
            await self.channel.send('Wrap your answer in quotation marks, e.g. "answer".'
                                    'Remember, one word answers only!')

        await self.channel.send(self.guesser.mention + " You have {} seconds.".format(self.round_delay))
        # Register guess
        # TODO: add check for multiple word clues
        try:
            self.guess_msg = await self.bot.wait_for('message', check=self.is_answer, timeout=self.round_delay)
            answer = self.guess_msg.content
            if answer[0] == "'":
                self.answer = answer.split("'")[1]
            else:
                self.answer = answer.split('"')[1]
        except asyncio.TimeoutError:
            await self.channel.send('You took too long...')

        # Check correctness of guess
        if self.answer != self.default_answer:
            await self.start_vote_on_guess()
        else:
            await self.channel.send("Times up! No answer submitted.")

        # post secret word so people can be reminded
        await self.channel.send('(The secret word was "{}")'.format(self.secret_word))

        await asyncio.sleep(self.round_delay)

        # Tally points
        await self.update_score()

        # End guess phase and start again
        await self.remove_amnesias()
        self.guess_round = False
        self.round_count += 1
        self.reset_hint_data()
        if self.round_count < self.num_rounds:
            await self.begin_round()
        else:
            await self.post_final_score()
            self.game_started = False
            # remove roles
            await self.remove_players()
            await self.remove_amnesias()
            await self.remove_blinds()
            # leave voice channel
            await self.vc.disconnect()
            # reset game
            await self.reset_game()

    @command(name='start_game', aliases=('just_one', 'justone'))
    async def start_game(self, ctx: Context):
        if self.game_started:
            await ctx.send("Ongoing game, please try again when the current game has ended.")
            return

        self.channel = self.bot.get_channel(self.game_channel_id)
        self.voice_channel = self.bot.get_channel(self.voice_channel_id)
        self.vc = await self.voice_channel.connect()

        # eventually replace this with a smarter thing
        player_role_id = 618923454556536893
        blind_role_id = 618923455496060998
        quiet_role_id = 618923456188252180
        amnesia_role_id = 618923461397708811

        # get role objects
        all_roles = ctx.guild.roles  # ctx = context
        for role in all_roles:
            if role.id == player_role_id:
                self.player_role = role
            elif role.id == quiet_role_id:
                self.quiet_role = role
            elif role.id == blind_role_id:
                self.blind_role = role
            elif role.id == amnesia_role_id:
                self.amnesia_role = role

        # tag everyone with role
        self.registration = True  # change flag for registration period
        self.game_started = True
        await ctx.send("Starting Just One! Type !join to play")

        # add player to list of players
        self.players.append(ctx.message.author)

        # wait 60 seconds for people to join
        await asyncio.sleep(self.round_delay)
        await ctx.send("Registration period over, game starting now!")
        self.registration = False  # end registration period

        await self.begin_round()

    @command(name='join')
    async def join(self, ctx: Context):
        if self.game_started and not self.registration:
            await ctx.send("Ongoing game, please try again when the current game has ended.")
            return
        elif not self.game_started:
            await ctx.send("No games currently running. Use !start_game to begin playing!")
            return
        else:
            pass

        # add player to list of players
        if ctx.channel.id == self.game_channel_id:
            self.players.append(ctx.message.author)

    @command(name='rules')
    async def rules(self, ctx: Context):
        embed = Embed(title="Just One Rules", color=0xeee657)
        image_url = "http://press.rprod.com/wp-content/uploads/2018/08/JustOne-Logo.png"
        embed.set_thumbnail(url=image_url)
        objective = "".join(list(open('rules.txt')))
        embed.add_field(name="Object of the game", value=objective)

        setup_text = "".join(list(open('setup.txt')))
        embed.add_field(name="Mechanics", value=setup_text)

        await ctx.send('', embed=embed)



def setup(bot):
    bot.add_cog(JustOne(bot))
    log.info("Cog loaded: Moderation")
