"""Nicknames fans actually search with, mapped to the names in the catalog.

Small embedding models do not know that "web swinger" means Spider-Man, so the
query is expanded with the canonical name before it is embedded and before
title matching. Keys are matched on normalized text (lowercase, no punctuation).
"""
import re

ALIASES: dict[str, list[str]] = {
    # Marvel
    "web swinger": ["Spider-Man"], "web slinger": ["Spider-Man"], "web head": ["Spider-Man"],
    "wall crawler": ["Spider-Man"], "spidey": ["Spider-Man"], "friendly neighborhood": ["Spider-Man"],
    "peter parker": ["Spider-Man"], "miles morales": ["Spider-Man", "Miles Morales"],
    "spider woman": ["Spider-Woman"], "spider gwen": ["Spider-Gwen"], "ghost spider": ["Spider-Gwen"],
    "symbiote": ["Venom"], "eddie brock": ["Venom"], "carnage": ["Carnage"],
    "merc with a mouth": ["Deadpool"], "wade wilson": ["Deadpool"],
    "adamantium claws": ["Wolverine"], "logan": ["Wolverine"], "weapon x": ["Wolverine"],
    "mutants": ["X-Men"], "professor x": ["X-Men"], "magneto": ["X-Men", "Magneto"],
    "god of thunder": ["Thor"], "mjolnir": ["Thor"], "god of mischief": ["Loki"],
    "jade giant": ["Hulk"], "green goliath": ["Hulk"], "bruce banner": ["Hulk"],
    "iron suit": ["Iron Man"], "tony stark": ["Iron Man"], "armored avenger": ["Iron Man"],
    "first avenger": ["Captain America"], "star spangled": ["Captain America"], "steve rogers": ["Captain America"],
    "sorcerer supreme": ["Doctor Strange"], "man without fear": ["Daredevil"], "blind lawyer": ["Daredevil"],
    "punisher": ["Punisher"], "frank castle": ["Punisher"], "black widow": ["Black Widow"],
    "wakanda": ["Black Panther"], "first family": ["Fantastic Four"], "reed richards": ["Fantastic Four"],
    "galactus": ["Silver Surfer", "Fantastic Four"], "cosmic surfer": ["Silver Surfer"],
    "earths mightiest heroes": ["Avengers"], "avengers assemble": ["Avengers"],
    "space raccoon": ["Guardians of the Galaxy"], "infinity gauntlet": ["Infinity Gauntlet", "Thanos"],
    "moon knight": ["Moon Knight"], "ghost rider": ["Ghost Rider"], "flaming skull": ["Ghost Rider"],
    "ms marvel": ["Ms. Marvel"], "kamala khan": ["Ms. Marvel"], "captain marvel": ["Captain Marvel"],
    # DC
    "dark knight": ["Batman"], "caped crusader": ["Batman"], "worlds greatest detective": ["Batman", "Detective Comics"],
    "bruce wayne": ["Batman"], "gotham": ["Batman", "Gotham"], "boy wonder": ["Robin"],
    "clown prince of crime": ["Joker"], "harley": ["Harley Quinn"],
    "man of steel": ["Superman"], "last son of krypton": ["Superman"], "clark kent": ["Superman"],
    "kryptonian": ["Superman", "Supergirl"], "girl of steel": ["Supergirl"],
    "amazon princess": ["Wonder Woman"], "lasso of truth": ["Wonder Woman"], "diana prince": ["Wonder Woman"],
    "scarlet speedster": ["Flash"], "fastest man alive": ["Flash"], "speed force": ["Flash"],
    "emerald knight": ["Green Lantern"], "power ring": ["Green Lantern"], "lantern corps": ["Green Lantern"],
    "emerald archer": ["Green Arrow"], "king of atlantis": ["Aquaman"], "atlantis": ["Aquaman"],
    "justice league": ["Justice League"], "teen titans": ["Teen Titans"], "suicide squad": ["Suicide Squad"],
    "swamp thing": ["Swamp Thing"], "hellblazer": ["Hellblazer", "John Constantine"], "constantine": ["Hellblazer"],
    "dream of the endless": ["Sandman"], "morpheus": ["Sandman"], "rorschach": ["Watchmen"],
    # Other Western
    "zombie apocalypse": ["The Walking Dead"], "rick grimes": ["The Walking Dead"],
    "hellboy": ["Hellboy"], "ninja turtles": ["Teenage Mutant Ninja Turtles"], "tmnt": ["Teenage Mutant Ninja Turtles"],
    "spawn": ["Spawn"], "the boys": ["The Boys"], "invincible": ["Invincible"],
    # Manga / manhwa
    "straw hat": ["One Piece"], "pirate king": ["One Piece"], "luffy": ["One Piece"],
    "titans behind walls": ["Attack on Titan"], "giants behind walls": ["Attack on Titan"], "eren": ["Attack on Titan"],
    "death note": ["Death Note"], "notebook that kills": ["Death Note"],
    "ninja village": ["Naruto"], "hidden leaf": ["Naruto"], "nine tailed fox": ["Naruto"],
    "dragon balls": ["Dragon Ball"], "goku": ["Dragon Ball"], "super saiyan": ["Dragon Ball"],
    "demon slayer": ["Demon Slayer"], "tanjiro": ["Demon Slayer"], "cursed energy": ["Jujutsu Kaisen"],
    "chainsaw": ["Chainsaw Man"], "one punch": ["One-Punch Man"], "bald hero": ["One-Punch Man"],
    "alchemy brothers": ["Fullmetal Alchemist"], "philosophers stone": ["Fullmetal Alchemist"],
    "shadow monarch": ["Solo Leveling"], "sung jinwoo": ["Solo Leveling"],
    "tower climbing": ["Tower of God"], "black swordsman": ["Berserk"], "guts": ["Berserk"],
    "hunter exam": ["Hunter x Hunter"], "jojo": ["JoJo's Bizarre Adventure"], "stands": ["JoJo's Bizarre Adventure"],
}


def normalize(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text.replace("'", "").replace("-", ""))
    return re.sub(r"\s+", " ", text).strip()


_NORMALIZED = {normalize(k): v for k, v in ALIASES.items()}


def expand(query: str) -> list[str]:
    """Canonical names implied by the query, in order, without duplicates."""
    q = f" {normalize(query)} "
    found: list[str] = []
    for alias, names in _NORMALIZED.items():
        if f" {alias} " in q:
            found.extend(n for n in names if n not in found)
    return found
