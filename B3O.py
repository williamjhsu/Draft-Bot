
import discord
import random
import asyncio
import sys
import json
import os
import os.path
from os import path
import imagemanipulator
from io import StringIO

BotToken = "NzA3MzI0NjAxNDQ4NzkyMDY0.XrHJbw.mwn0yBiFMXRTBs2W93ePyWwcW64"
GuildName = "fspluver's server"
GuildID = 706652047042412565
client = discord.Client()

from discord.ext import commands
client = commands.Bot(command_prefix = 'B!')

#Connecting
@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GuildName:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )


# not a fan of Python classes, but this is the implemetation I'm doing to allow for a list of just strings as well (for now)
class CardInfo:
    #Left all but name as optional so that we can fall back if that's all we have. Definitely could have more properties in this class, just wanted a good starting point.
    def __init__(self, name, id = -1, cardType="", description = "", imageUrl = ""):
        self.name = name
        self.id = id
        self.cardType = cardType
        self.description = description
        self.imageUrl = imageUrl
    #We're just displaying names for now, but that can change. What these mean is that if you print a list of these, only their names will show.
    def __repr__(self):
        return self.name
    def __str__(self):
        self.name


CardList = []

#import code. Short and sweet.
if (path.exists('list.cub')):
    print('Cube list discovered. Importing.')
    with(open("list.cub", 'r')) as cubeFile:
        #Python makes some things so so easy
        cardDict = json.load(cubeFile)
        #Instantiate a new CardInfo object for each card in the list. Definitely could pull in more info from the JSON - there's a lot there.
        for card in cardDict:
            CardList.append(CardInfo(card['name'], card['id'], card['type'], card['desc'], card['card_images'][0]['image_url']))

else:
    print('Did not find cube list. Falling back to default list.')
    CardNames = [
        'acid trap hole',
        'bad aim',
        'ballista squad',
        'burst rebirth',
        'bottomless trap hole',
        'call of the haunted',
        'ceasefire',
        'compulsory evacuation device',
        'counter gate',
        'dark bribe',
        'dimension slice',
        'dimensional prison',
        'divine wrath',
        'dust tornado',
        'fiendish chain',
        'icarus attack',
        'karma cut',
        'legacy of yata-garasu',
        'liberty at last!',
        'macro cosmos',
        'magic cylinder',
        'magic drain',
        'malevolent catastrophe',
        'metal reflect slime',
        'metalmorph',
        'mirror force',
        'needle ceiling',
        'oasis of dragon souls',
        'ordeal of a traveler',
        'peaceful burial',
        'raigeki break',
        'recall',
        'reckless greed1',
        'reckless greed2',
        'reckless greed3',
        'return from the different dimension',
        'ring of destruction',
        'royal decree',
        'scrap-iron scarecrow',
        'sakuretsu armor',
        'seven tools of the bandit',
        'shadow spell'
        ]

    for cardName in CardNames:
        CardList.append(CardInfo(cardName))

pools = []
pool = []
players = []
playernames = []
packs = []
pack = []
i = 0
x = 0
t = 0
pickNumber = 0

#Welcomes people who join the server
@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )


#Responds in chat to messages. 
@client.event
async def on_message(message):
    global packs
    global CardList
    global FullList
    global w
    global pickNumber
    global t
    w = 0
    #printprint(message.content.lower())
    if message.author == client.user:
        return
 

 #Players - Sign up and check current players

    #Message is someone tries to sign up twice
    if ('!joindraft') in message.content.lower() and message.author in players:
        await message.channel.send('It\'s not possible! No one has the power to be in two draft seats at once!')
    #Registers the player
    if (('!joindraft') in message.content.lower() and packs == []) and (message.author not in players):
        #made it announce name - we might want to look into always sending this to the main server even if draft is joined in PM
        await message.channel.send(message.author.name + ' has joined the draft!')
        players.append(message.author)
        playernames.append(message.author.name)
    #Sends the name of all registered players. Commented out has all the person's info (e.g. Discord ID)    
    if ('!currentplayers') in message.content.lower():
        await message.channel.send(playernames)
        #await message.channel.send(players)
 
        
 #Sends first pack to all players
    if ('!!startdraft') in message.content.lower():
        await message.channel.send('The draft is starting! All players have received their first pack. Good luck!')
        FullList = random.sample(CardList, len(players)*15)
        CardList = [q for q in CardList if q not in FullList] #Removes the cards from the full card list

        i = 0 #For pulling cards from the full list into packs
        for word in players:
            pack = FullList[i:i+15]
            packs.append(pack) #Holds the packs
            i = i+15
            await word.send(content="Here's your first pack! Use !pick _cardname_ to select a card. Happy drafting!\n"+str(pack), file=discord.File(fp=imagemanipulator.create_pack_image(pack),filename="image.jpg"))


 #Puts picks into pool and removes the pick from the pack
    if message.content.lower().strip().startswith('!pick'):     

        #card name, all lower, without trailing or leading spaces
        pickText = message.content.lower().replace('!pick', '').strip()

        #this is my pack, there are many like it, but this one is mine
        workingPack = packs[players.index(message.author)]

        poolCount = len([card for card in pool if message.author.name in card])
        
        if(poolCount % 15 > pickNumber):
            await message.author.send("I know they're all good cards, but one per pack, please. Maybe get a snack or something while you wait.") #we don't like cheaters
            return   


        #index of the card in the pack, if it's -1 after we verify it ain't in there
        cardIndex = -1
        try: #this language's iteration syntax confuses me greatly
            cardIndex = next(i for i, c in enumerate(workingPack) if pickText in c.name.lower())
        except:
            cardIndex = -1

        if cardIndex != -1: #Changed from earlier versions so people can only pick from their pack            
            pool.append([message.author.name, workingPack[cardIndex]]) #add card to pool
            workingPack.remove(workingPack[cardIndex]) #remove card from pack
            await message.author.send('---------------Nice pick! It has been added to your pool.---------------\nType !mypool to view your entire cardpool.')      

            #Automatically passing the pack
            length = len(packs[0])
            if t == (1 or 3): #doubling the below code. If pack 1 or 3 is it passes one way. If not it passes the other way
                if all (len(y)==length for y in packs):
                    packs = packs[1:] + packs[:1] #Play with this to make packs pass reverse. I think can just add - before the 1s
                    for word in players:
                        await word.send(content='Your next pack contains:\n'+str(packs[players.index(word)]), file=discord.File(fp=imagemanipulator.create_pack_image(packs[players.index(word)]), filename="image.jpg"))
                    if len(packs[0]) == 0:
                        packs = []
                        pickNumber = 0
                        t = t+1
                        if t < 4:
                            await message.channel.send('Here is your next pack! It may take a few seconds to load. Good luck!')
                            FullList = random.sample(CardList, len(players)*15)
                            CardList = [q for q in CardList if q not in FullList] #Removes the cards from the full card list

                            i = 0 #For pulling cards from the full list into packs
                            for word in players:
                                pack = FullList[i:i+15]
                                packs.append(pack) #Holds the packs
                                i = i+15
                                await word.send(content="Use !pick _cardname_ to select a card. Happy drafting!\n"+str(pack), file=discord.File(fp=imagemanipulator.create_pack_image(pack),filename="image.jpg"))


                    else:
                        pickNumber = pickNumber + 1

            else:
                if all (len(y)==length for y in packs): #Works (tested with 2 and 3 players)
                    packs = packs[-1:] + packs[:-1] #Play with this to make packs pass reverse. I think can just add - before the 1s
                    for word in players:
                        await word.send(content='Your next pack contains:\n'+str(packs[players.index(word)]), file=discord.File(fp=imagemanipulator.create_pack_image(packs[players.index(word)]), filename="image.jpg"))
                    if len(packs[0]) == 0:
                        packs = []
                        pickNumber = 0
                        t = t+1
                        if t < 4:
                            await message.channel.send('Here is your next pack! It may take a few seconds to load. Good luck!')
                            FullList = random.sample(CardList, len(players)*15)
                            CardList = [q for q in CardList if q not in FullList] #Removes the cards from the full card list

                            i = 0 #For pulling cards from the full list into packs
                            for word in players:
                                pack = FullList[i:i+15]
                                packs.append(pack) #Holds the packs
                                i = i+15
                                await word.send(content="Use !pick _cardname_ to select a card. Happy drafting!\n"+str(pack), file=discord.File(fp=imagemanipulator.create_pack_image(pack),filename="image.jpg"))


                    else:
                        pickNumber = pickNumber + 1



        else:
            await message.author.send("Sorry! That card doesn't look like it's in this pack. Try again.") #Git gud, learn how 2 read   

       

    if ('!mypool' in message.content.lower()):
        temppool = []
        for word in pool:
            if message.author.name in word:
                temppool.append(word[1].name)# + " : " + word[1].imageUrl) #could send any combination of card properties in any sort of format
        await message.author.send(temppool)
        

    if ('!ydk' in message.content.lower()):
        tempidpoolnoextra = []
        tempidpoolextra = []
        tempidpoolside = []
        r = 0
        for word in pool:
            if (word[1].cardType != ("Synchro Monster") or ("Synchro Tuner Monster")) and word[1].cardType != "XYZ Monster":                
                if message.author.name in word:
                    tempidpoolnoextra.append(word[1].id) #puts the ids of the main deck cards in a list
            if ((word[1].cardType == ("Synchro Monster") or ("Synchro Tuner Monster")) or (word[1].cardType == "XYZ Monster")) and (r < 14):
                if message.author.name in word:
                    tempidpoolextra.append(word[1].id) #puts the ids of the extra deck cards in a list
                    r = r + 1
            if ((word[1].cardType == ("Synchro Monster") or ("Synchro Tuner Monster")) or (word[1].cardType == "XYZ Monster")) and (r > 13):
                if message.author.name in word:
                    tempidpoolside.append(word[1].id) #puts the ids of the extra deck cards in an overflow side list

        ydkString = ""
        ydkstuff = ["#created by ...", "#main"]
        for listitem in ydkstuff: #puts in the necessary ydk stuff
            ydkString+='%s\n' % listitem
        for listitem in tempidpoolnoextra:
            ydkString+=('%s\n' % listitem) #should put main deck cards in the ydk file
        ydkextraline = ["#extra"]
        for listitem in ydkextraline: #Stuff after this gets put in the extra deck (until side)
            ydkString+='%s\n' % listitem
        for listitem in tempidpoolextra:
            ydkString+='%s\n' % listitem
        ydksidestuff = ["!side"] #Stuff after this gets put in the side
        for listitem in ydksidestuff:
            ydkString+='%s\n' % listitem           
        for listitem in tempidpoolside:
            ydkString+='%s\n' % listitem
        await message.author.send(file=discord.File(fp=StringIO(ydkString),filename="YourDraftPool.ydk"))

    if ('!draftdone') in message.content.lower():
        await message.players.send('The draft has concluded! Type "!mypool" to see your cardpool! Good luck in your duels!')





client.run(BotToken)





