import asyncio
import os
import pickle
import random
import discord
import numpy as np
import pandas as pd

import imagemanipulator
import math
import pandas

# Constants

reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '0️⃣', '🇦', '🇧', '🇨', '🇩', '🇪', '🇫',
             '🇬', '🇭', '🇮', '🇯']

# Starting with a list that will hold pick data
pickdata = [['Name', 'Pick', 'User', 'Cube', 'Pack']]


# Stores their pool of picked cards and discord user. Store within drafts.
class Player:
    def __init__(self, user, draft):
        # req saved data
        self.draft = draft
        self.pool = []
        self.user = user

        self.cards_in_pack = None

        # picking data
        self._temp_pick_name = None
        self._temp_pick_idx = -1
        self.picks = []
        self.has_picked = False
        self.current_message_id = ""
        self.selected_arr = []
        self.temppickdata = []

    def __repr__(self):
        return self.user

    def hasPicked(self):
        return self.has_picked
        # pack_nums = self.draft.pack_numbers()
        # return not (len(self.pack) + self.draft.currentPick == pack_nums[self.draft.currentPack-1]+1)

    def finished_pack(self):
        return len(self.cards_in_pack) == 0

    def pick(self, cardIndex):
        # Checking if the card is in the pack.
        if cardIndex <= (len(self.cards_in_pack) - 1):
            # Making sure they havent already picked
            if not self.hasPicked():
                asyncio.create_task(
                    self.user.send('Pick: ' + self.cards_in_pack[cardIndex].name + '.'))
            else:
                asyncio.create_task(
                    self.user.send('Changed Pick: ' + self.cards_in_pack[cardIndex].name + '.'))

            self._temp_pick_name = str(self.cards_in_pack[cardIndex].name)  # Adding the card name to the temppickdata vector
            # to append to file
            self._temp_pick_idx = cardIndex
            self.has_picked = True
            self.draft.checkPacks()

    def validate_pick(self):
        temppickdata = []
        # tempcardname = self._temp_pick_name.replace(',', " ")  # Removing commas for CSV purposes
        temppickdata.append(self._temp_pick_name)
        temppickdata.append(len(self.cards_in_pack))  # Adding pick #
        temppickdata.append(self.user.id)  # Adding the person who picked
        temppickdata.append('x')  # Noting which cube was used. Will add once I get this working
        self.pool.append(self.cards_in_pack[self._temp_pick_idx])
        self.cards_in_pack.pop(self._temp_pick_idx)
        self.has_picked = False
        self.temppickdata = temppickdata

    def save_pick(self):
        temppickdata = self.temppickdata
        card_str_arr = ""
        idx = 0
        for card in self.cards_in_pack:
            if idx != 0:
                card_str_arr += "|"
            card_str_arr += card.name
            idx += 1
        temppickdata.append(card_str_arr)
        pickdata.append(temppickdata)


class Draft:
    # cube: The cube the pool was created from
    # pool: The cards remaining to be picked from
    # players: The players in the draft. Player class.
    # channel: The channel the draft was started from
    draft_directory = "SavedDrafts"
    draft_file_name = "draftfile.csv"

    def __init__(self, cube, channel):
        self.cube = cube[:]
        self.pool = cube[:]
        self.players = []  # Was orginally a default value. Created very complicated errors with underlying objects
        # and references in the Python interpter. Wasn't being used at the time anyway.
        self.channel = channel
        self.currentPick = -1
        self.currentPack = 0

    def save_draft(self):
        # save cards
        df = pd.DataFrame(data=pickdata)
        draft_dir = f"{self.draft_directory}/{self.channel}"
        if not os.path.exists(draft_dir):
            os.makedirs(draft_dir)
        df.to_csv(path_or_buf=f"{draft_dir}/{self.draft_file_name}", mode="w", index=False, header=False)

        # save draft meta data
        with open(f'{draft_dir}/objs.pkl', 'wb') as f:  # Python 3: open(..., 'wb')
            #print(self.cube, self.pool,
                  # self.currentPick, self.currentPack)
            pickle.dump([self.currentPick, self.currentPack, self.cube, self.pool], f)

    @classmethod
    def reload_draft(cls, draft_channel, client, card_map):
        # load meta data
        draft_dir = f"{cls.draft_directory}/{draft_channel}"
        if not os.path.exists(f'{draft_dir}/objs.pkl'):
            return None
        with open(f"{draft_dir}/objs.pkl", "rb") as f:
            current_pick, current_pack, cube, pool = pickle.load(f)
        # print(cube, pool, current_pick, current_pack)
        draft = cls(cube, draft_channel)
        draft.cube = cube
        draft.pool = pool
        draft.currentPick = int(current_pick)
        draft.currentPack = int(current_pack)

        # load player data
        df = pd.read_csv(f'{draft_dir}/draftfile.csv')
        user_card_map = {

        }
        user_pack_map = {

        }

        # map card to each user
        for i in range(len(df.index)):
            arr = df.iloc[i].to_numpy()
            pickdata.append(arr)
            card = card_map[arr[0]]
            user = arr[2]
            if user not in user_card_map:
                user_card_map[user] = []
                user_pack_map[user] = []
            user_card_map[user].append(card)
            if isinstance(arr[4], str):
                pack = arr[4].split("|")
                pack = [card_map[p] for p in pack]
                # print(pack)
                user_pack_map[user] = pack
        # append players to draft
        for key, items in user_card_map.items():
            user = client.get_user(key)
            player = Player(user, draft)
            # add cards to player
            for item in items:
                player.pool.append(item)
            player.cards_in_pack = user_pack_map[key]
            draft.players.append(player)
            # print(f"added player {user.name}, with cards:\n"
                  # f"{player.pool}")

        return draft

    def newPacks(self):  # TODO get rid of separated functions of rotate
        """
        need to edit to distribute number of cards per pack based on how many players
        :return:
        """
        self.currentPick = 1
        self.currentPack += 1
        self.players.reverse()

        pack_nums = self.pack_numbers()
        FullList = random.sample(self.pool, len(self.players) * int(pack_nums[self.currentPack - 1]))
        # adjusts to number of players
        self.pool = [q for q in self.pool if q not in FullList]  # Removes the cards from the full card list

        i = 0  # For pulling cards from the full list into packs
        for player in self.players:
            pack = sortPack(FullList[i:i + int(pack_nums[self.currentPack - 1])])
            player.cards_in_pack = pack  # Holds the packs
            i = i + int(pack_nums[self.currentPack - 1])
            # splices reactions into pack
            packWithReactions = self._helper_cardnames(player.cards_in_pack)
            asyncio.create_task(send_pack_message("Here's your #" + str(self.currentPack)
                                                  + " pack! React to select a card\n"
                                                  + str(packWithReactions), player, pack))

    def pack_numbers(self):
        """
        1000/player_num = number of cards per person
        if number of cards is not whole number:
            cut to nearest whole number
            take leftover cards, and randomly give them to players
                write message at end saying "you received an extra card(s)"

        :param
        :return: array of cards per pack in order
        """
        player_num = len(self.players)
        leftover_cards = len(self.cube) % player_num
        if leftover_cards != 0:  # if 1000/number of players isn't a whole number
            rounded_num = math.floor(len(self.cube) / player_num)
            # print("leftover_cards")
        else:
            rounded_num = len(self.cube) / player_num

        return self.split_packs(rounded_num)

    def split_packs(self, rounded):
        """
        split packs in half, round up and down if necessary
        return list of number of cards per pack in order <= 20 each
        :param rounded:
        :return: list
        """
        if rounded <= 20:  # if the list is already <= 20, then no splitting
            return [rounded]

        splitting = 1
        cards_per_pack = []
        rounded /= 2
        cards_per_pack.append(math.ceil(rounded))
        cards_per_pack.append(math.floor(rounded))

        if rounded <= 20:  # if the list is already <= 20, then no splitting
            return [rounded]

        while splitting:
            copy_list = []
            for a in cards_per_pack:
                copy_list.append(math.ceil(a / 2))
                copy_list.append(math.floor(a / 2))
            cards_per_pack = copy_list
            if cards_per_pack[0] <= 20:  # first element will always be the highest number
                splitting = 0

        return cards_per_pack

    def leftover_distribution(self):
        """
        take number of leftover cards
        pull them from the cardpool and then somewhat evenly distribute them at the end
        :param self:
        :param
        :return:
        """
        player_id = 0
        cards_to_players = []
        for x in self.players:  # make list of lists with number of players
            cards_to_players.append([])

        gifted_cards = []
        for a in self.pool:  # only called when JUST the leftover cards are left in the pool
            if player_id > len(self.players) - 1:  # wrap around if still more cards
                player_id = 0
            cards_to_players[player_id].append(a.name)
            player_id += 1

        player_id = 0
        for y in self.players:  # send message of leftover cards to players
            asyncio.create_task(gift_leftovers(cards_to_players[player_id], self.players))
            player_id += 1

    def rotatePacks(self):
        self.currentPick += 1

        # Creates a list of all the packs
        packs = [player.cards_in_pack for player in self.players]
        for player in self.players:
            # Gives the player the next pack in the list. If that would be out of bounds give them the first pack.
            player.cards_in_pack = packs[0] if (packs.index(player.cards_in_pack) + 1) \
                                               >= len(packs) else packs[packs.index(player.cards_in_pack) + 1]
            # splices reactions into pack
            packWithReactions = self._helper_cardnames(player.cards_in_pack)
            asyncio.create_task(send_pack_message('Your next pack: \n' + str(packWithReactions), player, player.cards_in_pack))

    def _helper_cardnames(self, pack):
        """
        function to get card names
        :return: str
        """
        pack_str = ''
        for a, b in zip(reactions, pack):
            # Card Errata print exceptions to display their errata page to have OG eff
            if (f'{b.name}' == "Blast with Chain") \
                    or (f'{b.name}' == "Brain Control") \
                    or (f'{b.name}' == "Crush Card Virus") \
                    or (f'{b.name}' == "Chaos Emperor Dragon") \
                    or (f'{b.name}' == "Destiny HERO - Disk Commander") \
                    or (f'{b.name}' == "Dark Magician of Chaos") \
                    or (f'{b.name}' == "Exchange of the Spirit") \
                    or (f'{b.name}' == "Imperial Order") \
                    or (f'{b.name}' == "Makyura the Destructor") \
                    or (f'{b.name}' == "Necrovalley") \
                    or (f'{b.name}' == "Night Assailant") \
                    or (f'{b.name}' == "Rescue Cat") \
                    or (f'{b.name}' == "Ring of Destruction") \
                    or (f'{b.name}' == "Sangan") \
                    or (f'{b.name}' == "Sinister Serpent") \
                    or (f'{b.name}' == "Witch of the Black Forest"):
                pack_str += f'{a} :  [{b.name}](<https://yugioh.fandom.com/wiki/Card_Errata:' \
                            f'{b.name.replace(" ", "_")}>)\n'
            # exception for labyrinth of nightmare
            elif (f'{b.name}' == "Labyrinth of Nightmare"):
                pack_str += f'{a} :  [{b.name}](<https://yugioh.fandom.com/wiki/Labyrinth_of_Nightmare_(card)>)\n'
            # else > print the main wiki card page
            else:
                pack_str += f'{a} :  [{b.name}](<https://yugioh.fandom.com/wiki/{b.name.replace(" ", "_")}>)\n'

        return pack_str

        # Decides if its time to rotate or send a new pack yet.

    def resume_draft(self):
        pack_nums = self.pack_numbers()
        if self.currentPick < int(pack_nums[self.currentPack - 1]):  #
            for player in self.players:
                player.picks = []  # clear picks
            self.rotatePacks()
        elif self.currentPack >= len(self.pack_numbers()):  # draft complete
            for player in self.players:
                player.picks = []  # clear picks
                asyncio.create_task(player.user.send(
                    'The finished draft is resumed. Use !ydk or !mypool to get started on deckbuilding.'))
                self.leftover_distribution()
        else:  # new draft
            for player in self.players:
                player.picks = []  # clear picks
            self.newPacks()

    def checkPacks(self):
        # Checks if every player has picked.
        pack_nums = self.pack_numbers()
        if len([player for player in self.players if not player.hasPicked()]) == 0:  # rotating to new packs
            # validate all player picks
            for player in self.players:
                player.validate_pick()
                player.picks = []

            self.save_draft()
                # save drafts

            if not self.players[0].finished_pack():  # still have cards in current pack
                for player in self.players:
                    player.save_pick()
                self.save_draft()
                for player in self.players:
                    player.picks = []  # clear picks
                self.rotatePacks()
            elif self.currentPack >= len(self.pack_numbers()):  # draft complete
                for player in self.players:
                    player.save_pick()
                self.save_draft()
                for player in self.players:
                    player.picks = []  # clear picks
                    asyncio.create_task(player.user.send(
                        'The draft is now finished. Use !ydk or !mypool to get started on deckbuilding.'))
                    self.leftover_distribution()
            else:  # new draft
                for player in self.players:
                    player.picks = []  # clear picks
                self.newPacks()
                for player in self.players:
                    player.save_pick()
                self.save_draft()


    def startDraft(self):
            self.newPacks()


def kick(self, player):
    # A little worried about how we currently call this from the seperate timer thread from all the other main logic.
    # Drops the players pack into the void currently.
    self.players.remove(player)
    self.checkPacks()
    asyncio.create_task(self.channel.send("A player has been kicked from the draft"))


def sortPack(pack):
    monsters = [card for card in pack if 'monster' in card.cardType.lower()
                and ('synchro' not in card.cardType.lower() and 'xyz' not in card.cardType.lower())]
    spells = [card for card in pack if 'spell' in card.cardType.lower()]
    traps = [card for card in pack if 'trap' in card.cardType.lower()]
    extras = [card for card in pack if 'xyz' in card.cardType.lower() or 'synchro' in card.cardType.lower()]
    return monsters + spells + traps + extras


async def add_reactions(message, emojis):
    for emoji in emojis:
        asyncio.create_task(message.add_reaction(emoji))


# This exists to allow making the pack messages async.
async def send_pack_message(text, player, pack):
    msg = await player.user.send(content=text,
                                 file=discord.File(fp=imagemanipulator.create_pack_image(pack),
                                                   filename="image.jpg"))
    player.current_message_id = msg.id
    # print(msg.id)
    asyncio.create_task(add_reactions(msg, reactions[:len(pack)]))


# send players message about gifted leftover cards
async def gift_leftovers(cards, players):
    player_ind = 0
    for player in players:
        if len(cards) < player_ind:
            asyncio.create_task(player.user.send('This your free card: ' + cards[player_ind] + '.'))
        player_ind += 1
