from modules.data.GameState import GameState
from modules.Files import WriteFile
from modules.Image import DetectTemplate
from modules.Inputs import EmuCombo, ReleaseAllInputs, PressButton
from modules.Stats import EncounterPokemon

# TODO
def mode_starters():
    choice = config["starter"].lower()
    starter_frames = get_rngState(GetTrainer()['tid'], choice)

    if choice not in ["treecko", "torchic", "mudkip"]:
        log.info(f"Unknown starter \"{config['starter']}\". Please edit the value in config.yml and restart the script.")
        os._exit(1)

    log.info(f"Soft resetting starter Pokemon...")
    
    while True:
        ReleaseAllInputs()

        while GetTrainer()["state"] != GameState.OVERWORLD: 
            PressButton("A")

        # Short delay between A inputs to prevent accidental selection confirmations
        while GetTrainer()["state"] == GameState.OVERWORLD: 
            EmuCombo(["A", 10])

        # Press B to back out of an accidental selection when scrolling to chosen starter
        if choice == "mudkip":
            while not DetectTemplate("mudkip.png"): 
                EmuCombo(["B", "Right"])
        elif choice == "treecko":
            while not DetectTemplate("treecko.png"): 
                EmuCombo(["B", "Left"])

        while True:
            emu = GetEmu()
            if emu["rngState"] in starter_frames["rngState"]:
                log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
            else:
                while GetTrainer()["state"] == GameState.MISC_MENU: 
                    PressButton("A")

                starter_frames["rngState"].append(emu["rngState"])
                WriteFile(f"stats/{GetTrainer()['tid']}/{choice}.json", json.dumps(starter_frames, indent=4, sort_keys=True))

                while not DetectTemplate("battle/fight.png"):
                    PressButton("B")

                    if config["mem_hacks"] and GetParty()[0]:
                        if EncounterPokemon(starter=True):
                            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")
                        else:
                            reset_game()
                            break
                else:
                    while True:
                        if GetParty()[0]:
                            if EncounterPokemon(starter=True): 
                                input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")
                            else:
                                reset_game()
                                break
            continue
