import json
import logging

from modules.Config import GetConfig
from modules.data.GameState import GameState
from modules.Files import ReadFile
from modules.Image import DetectTemplate
from modules.Inputs import ButtonCombo, HoldButton, ReleaseAllInputs, ReleaseButton, PressButton, WaitFrames
from modules.mmf.Pokemon import GetOpponent, GetParty
from modules.mmf.Trainer import GetTrainer

log = logging.getLogger(__name__)
config = GetConfig()

no_sleep_abilities = ["Shed Skin", "Insomnia", "Vital Spirit"]
pickup_pokemon = ["Meowth", "Aipom", "Phanpy", "Teddiursa", "Zigzagoon", "Linoone"]

type_list = json.loads(ReadFile("./modules/data/types.json"))

def StartMenu(entry: str): # Function to open any start menu item - presses START, finds the menu entry and opens it
    if not entry in ["bag", "bot", "exit", "option", "pokedex", "pokemon", "pokenav", "save"]:
        return False

    log.info(f"Opening start menu entry: {entry}")
    filename = f"start_menu/{entry.lower()}.png"
    
    ReleaseAllInputs()

    while not DetectTemplate("start_menu/select.png"):
        ButtonCombo(["B", "Start"])
        
        for i in range(0, 10):
            if DetectTemplate("start_menu/select.png"):
                break
            WaitFrames(1)

    WaitFrames(5)

    while not DetectTemplate(filename): # Find menu entry
        ButtonCombo(["Down", 10])

    while DetectTemplate(filename): # Press menu entry
        ButtonCombo(["A", 10])

def BagMenu(category: str, item: str): # Function to find an item in the bag and use item in battle such as a pokeball
    if not category in ["berries", "items", "key_items", "pokeballs", "tms&hms"]:
        return False

    log.info(f"Scrolling to bag category: {category}...")

    while not DetectTemplate(f"start_menu/bag/{category.lower()}.png"):
        ButtonCombo(["Right", 25]) # Press right until the correct category is selected

    WaitFrames(60) # Wait for animations

    log.info(f"Scanning for item: {item}...")
    
    i = 0
    while not DetectTemplate(f"start_menu/bag/items/{item}.png") and i < 50:
        if i < 25: ButtonCombo(["Down", 15])
        else: ButtonCombo(["Up", 15])
        i += 1

    if DetectTemplate(f"start_menu/bag/items/{item}.png"):
        log.info(f"Using item: {item}...")
        while GetTrainer()["state"] == GameState.BAG_MENU: 
            ButtonCombo(["A", 30]) # Press A to use the item
        return True
    else:
        return False

def PickupItems(): # If using a team of Pokemon with the ability "pickup", this function will take the items from the pokemon in your party if 3 or more Pokemon have an item
    if GetTrainer()["state"] != GameState.OVERWORLD:
        return

    item_count = 0
    pickup_mon_count = 0
    party_size = len(GetParty())

    i = 0
    while i < party_size:
        pokemon = GetParty()[i]
        held_item = pokemon['heldItem']

        if pokemon["speciesName"] in pickup_pokemon:
            if held_item != 0:
                item_count += 1

            pickup_mon_count += 1
            log.info(f"Pokemon {i}: {pokemon['speciesName']} has item: {item_list[held_item]}")

        i += 1

    if item_count < config["pickup_threshold"]:
        log.info(f"Party has {item_count} item(s), won't collect until at threshold {config['pickup_threshold']}")
        return

    WaitFrames(60) # Wait for animations
    StartMenu("pokemon") # Open Pokemon menu
    WaitFrames(65)

    i = 0
    while i < party_size:
        pokemon = GetParty()[i]
        if pokemon["speciesName"] in pickup_pokemon and pokemon["heldItem"] != 0:
            # Take the item from the pokemon
            ButtonCombo(["A", 15, "Up", 15, "Up", 15, "A", 15, "Down", 15, "A", 75, "B"])
            item_count -= 1
        
        if item_count == 0:
            break

        ButtonCombo([15, "Down", 15])
        i += 1

    # Close out of menus
    for i in range(0, 5):
        PressButton("B")
        WaitFrames(20)

def SaveGame(): # Function to save the game via the save option in the start menu
    try:
        log.info("Saving the game...")

        i = 0
        StartMenu("save")
        while i < 2:
            while not DetectTemplate("start_menu/save/yes.png"):
                WaitFrames(10)
            while DetectTemplate("start_menu/save/yes.png"):
                ButtonCombo(["A", 30])
                i += 1
        WaitFrames(500) # Wait for game to save
        PressButton("SaveRAM") # Flush Bizhawk SaveRAM to disk
    except Exception as e:
        log.exception(str(e))

def ResetGame():
    log.info("Resetting...")
    HoldButton("Power")
    WaitFrames(60)
    ReleaseButton("Power")

def CatchPokemon(): # Function to catch pokemon
    try:
        while not DetectTemplate("battle/fight.png"):
            ReleaseAllInputs()
            ButtonCombo(["B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible
        
        if config["manual_catch"]:
            input("Pausing bot for manual catch (don't forget to pause pokebot.lua script so you can provide inputs). Press Enter to continue...")
            return True
        else:
            log.info("Attempting to catch Pokemon...")
        
        if config["use_spore"]: # Use Spore to put opponent to sleep to make catches much easier
            log.info("Attempting to sleep the opponent...")
            i, spore_pp = 0, 0
            
            opponent = GetOpponent()
            ability = opponent["ability"][opponent["altAbility"]]
            can_spore = ability not in no_sleep_abilities

            if (opponent["status"] == 0) and can_spore:
                for move in GetParty()[0]["enrichedMoves"]:
                    if move["name"] == "Spore":
                        spore_pp = move["pp"]
                        spore_move_num = i
                    i += 1

                if spore_pp != 0:
                    ButtonCombo(["A", 15])
                    if spore_move_num == 0: seq = ["Up", "Left"]
                    elif spore_move_num == 1: seq = ["Up", "Right"]
                    elif spore_move_num == 2: seq = ["Left", "Down"]
                    elif spore_move_num == 3: seq = ["Right", "Down"]

                    while not DetectTemplate("spore.png"):
                        ButtonCombo(seq)

                    ButtonCombo(["A", 240]) # Select move and wait for animations
            elif not can_spore:
                log.info(f"Can't sleep the opponent! Ability is {ability}")

            while not DetectTemplate("battle/bag.png"): 
                ReleaseAllInputs()
                ButtonCombo(["B", "Up", "Right"]) # Press B + up + right until BAG menu is visible

        while True:
            if DetectTemplate("battle/bag.png"): PressButton("A")

            # Preferred ball order to catch wild mons + exceptions 
            # TODO read this data from memory instead
            if GetTrainer()["state"] == GameState.BAG_MENU:
                can_catch = False

                # Check if current species has a preferred ball
                if opponent["speciesName"] in config["pokeball_override"]:
                    species_rule = config["pokeball_override"][opponent["speciesName"]]
                    
                    for ball in species_rule:
                        if BagMenu(category="pokeballs", item=ball):
                            can_catch = True
                            break

                # Check global pokeball priority 
                if not can_catch:
                    for ball in config["pokeball_priority"]:
                        if BagMenu(category="pokeballs", item=ball):
                            can_catch = True
                            break

                if not can_catch:
                    log.info("No balls to catch the Pokemon found. Killing the script!")
                    os._exit(1)

            if DetectTemplate("gotcha.png"): # Check for gotcha! text when a pokemon is successfully caught
                log.info("Pokemon caught!")

                while GetTrainer()["state"] != GameState.OVERWORLD:
                    PressButton("B")

                WaitFrames(120) # Wait for animations
                
                if config["save_game_after_catch"]: 
                    SaveGame()
                
                return True

            if GetTrainer()["state"] == GameState.OVERWORLD:
                return False
    except Exception as e:
        log.exception(str(e))
        return False

def battle(): # Function to battle wild pokemon
    # This will only battle with the lead pokemon of the party, and will run if it dies or runs out of PP
    ally_fainted = False
    foe_fainted = False

    while not ally_fainted and not foe_fainted and GetTrainer()["state"] != GameState.OVERWORLD:
        log.info("Navigating to the FIGHT button...")

        while not DetectTemplate("battle/fight.png") and GetTrainer()["state"] != GameState.OVERWORLD:
            ButtonCombo(["B", 10, "Up", 10, "Left", 10]) # Press B + up + left until FIGHT menu is visible
        
        if GetTrainer()["state"] == GameState.OVERWORLD:
            return True

        best_move = FindEffectiveMove(GetParty()[0], GetOpponent())
        
        if best_move["power"] <= 10:
            log.info("Lead Pokemon has no effective moves to battle the foe!")
            FleeBattle()
            return False
        
        PressButton("A")

        WaitFrames(5)

        log.info(f"Best move against foe is {best_move['name']} (Effective power is {best_move['power']})")

        i = int(best_move["index"])

        if i == 0:
            ButtonCombo(["Up", "Left"])
        elif i == 1:
            ButtonCombo(["Up", "Right"])
        elif i == 2:
            ButtonCombo(["Down", "Left"])
        elif i == 3:
            ButtonCombo(["Down", "Right"])
        
        PressButton("A")

        WaitFrames(5)

        while GetTrainer()["state"] != GameState.OVERWORLD and not DetectTemplate("battle/fight.png"):
            PressButton("B")
            WaitFrames(1)
        
        ally_fainted = GetParty()[0]["hp"] == 0
        foe_fainted = GetOpponent()["hp"] == 0
    
    if ally_fainted:
        log.info("Lead Pokemon fainted!")
        FleeBattle()
        return False
    elif foe_fainted:
        log.info("Battle won!")
        return True
    return True

def IsValidMove(move: dict):
    return not move["name"] in config["banned_moves"] and move["power"] > 0

def FindEffectiveMove(ally: dict, foe: dict):
    i = 0
    move_power = []

    for move in ally["enrichedMoves"]:
        power = move["power"]

        # Ignore banned moves and those with 0 PP
        if not IsValidMove(move) or ally["pp"][i] == 0:
            move_power.append(0)
            i += 1
            continue

        # Calculate effectiveness against opponent's type(s)
        matchups = type_list[move["type"]]

        for foe_type in foe["type"]:
            if foe_type in matchups["immunes"]:
                power *= 0
            elif foe_type in matchups["weaknesses"]:
                power *= 0.5
            elif foe_type in matchups["strengths"]:
                power *= 2

        # STAB
        for ally_type in ally["type"]:
            if ally_type == move["type"]:
                power *= 1.5

        move_power.append(power)
        i += 1

    # Return info on the best move
    move_idx = move_power.index(max(move_power))
    return {
        "name": ally["enrichedMoves"][move_idx]["name"],
        "index": move_idx,
        "power": max(move_power)
    }

def FleeBattle(): # Function to run from wild pokemon
    try:
        log.info("Running from battle...")
        while GetTrainer()["state"] != GameState.OVERWORLD:
            while not DetectTemplate("battle/run.png") and GetTrainer()["state"] != GameState.OVERWORLD: 
                ButtonCombo(["Right", 5, "Down", "B", 5])
            while DetectTemplate("battle/run.png") and GetTrainer()["state"] != GameState.OVERWORLD: 
                PressButton("A")
            PressButton("B")
        WaitFrames(30) # Wait for battle fade animation
    except Exception as e:
        log.exception(str(e))
