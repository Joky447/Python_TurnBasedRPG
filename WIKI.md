# Spells x Blades — Wiki

A 2D turn-based RPG built with Python and Pygame. Battle through 5 themed floors, build a roster of heroes, grow your skills and gear, and defeat each floor's boss to unlock the next.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Game Overview](#game-overview)
- [Controls](#controls)
- [Characters](#characters)
- [Combat System](#combat-system)
- [World Map & Floors](#world-map--floors)
- [Skills](#skills)
- [Equipment](#equipment)
- [Enemies](#enemies)
- [Rewards & Progression](#rewards--progression)
- [Audio](#audio)
- [Settings](#settings)
- [Credits](#credits)
- [Save System](#save-system)
- [Asset Pipeline](#asset-pipeline)
- [Project Structure](#project-structure)
- [Tips & Strategies](#tips--strategies)

---

## Getting Started

### Requirements

- Python 3.x
- Pygame Community Edition (`pip install pygame-ce`)

### Running the Game

```bash
python main.py
```

---

## Game Overview

**Spells x Blades** is a turn-based RPG where you build a roster of up to 2 heroes and fight through 5 floors of increasingly tough enemies. Each floor is a chain of fights that ends with a boss. Beat the boss to open the next floor and grow stronger.

### Core Loop

1. **Create** a character (name, gender, class) and go to Base Camp
2. **Begin the adventure** and fight through a floor's encounters, one after another
3. **Receive** the floor's gear and a skill upgrade right before the boss
4. **Defeat** the boss and **learn a new skill**
5. **Repeat** on the next floor, up to floor 5

---

## Controls

| Where | Input | Action |
|-------|-------|--------|
| Everywhere | **F11** or **Alt+Enter** | Toggle fullscreen |
| Main menu | Mouse, or Up/Down + Enter | Choose an option |
| Main menu | **C** / **O** | Credits / Settings |
| World map | **Enter** | Open the floor's fight list, then start the next fight |
| World map | **B** | Go to Base Camp (asks to confirm if the floor would reset) |
| Combat | **1–4** (top row or numpad) | Use skill 1–4 |
| Combat | **E**, **Space** or **Enter** | End turn |
| Combat | **Esc** | Exit the fight (asks to confirm) |
| Skill reward | **1–3**, **S** | Pick a skill, skip |

---

## Characters

### Creation

| Option | Choices |
|--------|---------|
| **Name** | Any name, up to 14 characters |
| **Gender** | Boy / Girl (changes the look only) |
| **Class** | Swordsman / Sorcerist |

### Classes

| Class | Base HP | Base Energy | Starting weapon | Starting skills |
|-------|---------|-------------|-----------------|-----------------|
| **Swordsman** | 80 | 3 | Iron Sword (+2 dmg) | Slash, Parry, Heavy Strike, Second Wind |
| **Sorcerist** | 70 | 3 | Novice Staff (+1 dmg) | Fireball, Mana Shield, Magic Missile, Heal |

Gear adds to these stats (see [Equipment](#equipment)).

### Roster

- Up to **2 characters** can be in your roster
- Each character has **independent progress** (items, skills, cleared floors)
- Switch the active character at Base Camp
- Deleting a character needs a second confirmation click. The active character can't be deleted

### Persistence

- Characters **keep their items, skills and cleared floors** even after dying
- Only the **current floor's unfinished progress** resets

---

## Combat System

You and the enemy take turns. On your turn you spend energy on skills, then end your turn and the enemy acts.

### Energy

- Your energy **refills to your maximum at the start of every turn** (3 by default; some gear adds more)
- Every skill has an energy cost. Unused energy does **not** carry over

### Block

- Block absorbs incoming damage before HP
- Block **expires at the start of that fighter's own next turn**
- Some gear gives free Block at the start of each of your turns

### Status Effects

| Effect | Description |
|--------|-------------|
| **Burn** | At turn start, takes damage equal to its stacks (ignores Block), then loses 1 stack |
| **Poison** | Works the same as Burn (a different color, and some enemies and skills favour it) |
| **Weak** | Deals 25% less damage. Lasts that many turns |
| **Vulnerable** | Takes 50% more damage. Lasts that many turns |
| **Strength** | Deals +1 damage per stack. Lasts the whole fight |

Hover a status icon in combat to read it.

### Multi-Hit Attacks

Some skills hit several times (shown as `Deal 7 x3`). Each hit is calculated separately, including Block absorption. There are no random critical hits.

### Enemy Intent

Enemies show their **next action** above their head: icons for attack, defend, heal, buff or debuff, plus the damage number for attacks (already adjusted for Weak and Vulnerable). Hover it for the move's name and details. The enemy then does exactly that.

### Ending a Fight

- **Victory:** the enemy is defeated
- **Defeat:** your HP reaches 0 and the Game Over screen appears
- **Exit Fight:** the button at the top right (or Esc). A warning dialog asks you to confirm before leaving (see [Run Structure](#run-structure))

---

## World Map & Floors

### Structure

The game has **5 floors**. Each floor has a fixed fight order:

1. Regular enemies, from weakest to strongest (by base HP)
2. An **elite** (floors 3, 4 and 5 only)
3. The **boss**

| Floor | Theme | Fights | Boss |
|-------|-------|--------|------|
| 1 | Goblins | 3 | Goblin Shaman |
| 2 | Castle | 4 | The Iron Paladin |
| 3 | Frost | 5 | Glacius, the Frost King |
| 4 | Grove | 6 | Sylvara, Queen of the Grove |
| 5 | Inferno | 7 | Ignis, the Demon Lord |

### Floor Unlocking

- Floors unlock **in order**: beat a floor's boss to open the next
- Cleared floors are marked with a green check on the map

### Run Structure

- A "run" starts at the **first uncleared floor**
- Fights are **continuous**: after each win the next fight starts straight away, up to the boss. Your HP carries over from fight to fight; only the pre-boss reward screen interrupts the chain
- **Exit Fight** in combat (with a confirmation dialog) sends the floor back to its first fight, restores your HP and returns you to the map. In a rematch, exiting just counts as a loss
- Leaving for Base Camp mid-floor also resets that floor's progress, and asks for a second click first. Items, skills and cleared floors are kept
- You get a **full heal** between floors and when returning to camp

### Rematches and Free Play

- Click a **cleared floor** on the map to pick any single enemy of that floor and fight it again
- Rematches give **no gear and no floor progress**, and your HP is restored afterwards
- Beating a **boss** in a rematch offers a new skill choice
- After clearing all 5 floors the map enters **Free Play**: there is no run to continue, and you pick any floor and enemy

### Test Mode

Set `UNLOCK_ALL_FLOORS = True` in `game_state/game_manager.py` to unlock every floor. Click a floor or press 1-5 to jump to it.

---

## Skills

### Overview

There are **27 skills**: 14 for the Swordsman and 13 for the Sorcerist. You fight with **4 skills at a time**, and they belong to your equipped **weapon** (learned and empowered skills stay on that weapon if you swap it out).

### Swordsman Skills

Slash, Parry, Heavy Strike, Second Wind, Twin Cut, Shield Bash, Sunder, Battle Cry, Flame Slash, Frost Edge, Venom Stab, Whirlwind, Iron Wall, Holy Blade

### Sorcerist Skills

Fireball, Mana Shield, Magic Missile, Heal, Ignite, Frost Nova, Ice Lance, Toxic Cloud, Hex, Arcane Surge, Chain Lightning, Meteor, Radiance

### Skill Properties

| Property | Description |
|----------|-------------|
| **Cost** | Energy needed to use it (1–3) |
| **Damage** | Damage per hit (your damage bonus and Strength are added) |
| **Hits** | Number of hits |
| **Block / Heal** | Block gained or HP restored |
| **Effects** | Statuses put on the enemy (Burn, Poison, Weak, Vulnerable) |
| **Self effects** | Statuses you gain (Strength) |
| **Element** | Physical, Fire, Ice, Poison, Arcane or Holy. Only changes the card's color |

### Skill Empowerment

- Empowering to floor level *N* multiplies damage, Block and healing by **(1 + 0.3 × N)** compared to the base skill
- It also adds **+1 effect stack for every 2 levels**
- Empowerment is permanent for that weapon's skill

### Skill Acquisition

- **Before each boss:** all 4 of your skills are empowered to the current floor's level
- **After each boss:** choose 1 of 3 random skills from your class pool (never ones you already have), empowered to the cleared floor's level, and pick which of your 4 skills it replaces. You can skip
- **Boss rematches:** the same choice, empowered to your furthest cleared floor

---

## Equipment

### Gear Slots

Each character has **5 slots**: **Helmet, Armor, Weapon, Shield, Wings**. Gear can add:

| Stat | Effect |
|------|--------|
| Damage | Added to every hit |
| Max HP | More health |
| Energy | More energy each turn |
| Block per turn | Block gained at the start of each of your turns |

### Floor Gear

Each floor's boss has a prepared reward, given automatically **before the boss fight** and **equipped straight away** (the piece it replaces goes to the inventory). It is class-specific:

| Floor | Swordsman (Aurora Knight set) | Sorcerist (Astral Sage set) |
|-------|-------------------------------|------------------------------|
| 1 | Aurora Greatsword (weapon) | Astral Wand (weapon) |
| 2 | Aurora Plate (armor) | Astral Robes (armor) |
| 3 | Aurora Helm (helmet; a mask for girls) | Astral Mask (helmet) |
| 4 | Aurora Aegis (shield) | Astral Aura (shield) |
| 5 | Aurora Wings (wings) | Astral Scythe (weapon, final form) |

- A character never receives the same item twice
- Set pieces only work while the set's weapon is equipped. With the starting weapon they give no stats and no visual outfit
- The character's on-screen outfit grows piece by piece as the set is collected

### Inventory

- Swapped-out gear goes to the **inventory**; it is kept even if you die
- Click an item to equip it, or click an equipped slot to unequip it
- The **weapon can't be unequipped**, only swapped for another weapon, because your skills come from it

---

## Enemies

### Overview

There are **25 enemies** across the 5 floors: 17 regular enemies, 3 elites (floors 3–5) and 5 bosses.

| Floor | Regular enemies | Elite | Boss |
|-------|-----------------|-------|------|
| 1 | Goblin, Goblin Archer | — | Goblin Shaman |
| 2 | Castle Archer, Knight, Castle Priest | — | The Iron Paladin |
| 3 | Frostbite Goblin, Ice Archer, Frost Knight | Snow Witch | Glacius, the Frost King |
| 4 | Thorn Sprite, Mushroom Brute, Crystal Golem, Forest Druid | Treant Guardian | Sylvara, Queen of the Grove |
| 5 | Magma Imp, Cinder Stalker, Ash Archer, Obsidian Knight, Flame Priest | Infernal Warlord | Ignis, the Demon Lord |

### Scaling

Enemies grow with the floor number and with their position in the floor's fight order. Their HP goes up by 25% per floor and by 8% per later fight. Their damage bonus goes up by 1 per floor and by 1 per later fight. Bosses scale with the floor only.

### Behavior

- Each enemy has a small set of moves and shows its next one (see [Enemy Intent](#enemy-intent))
- Regular enemies pick a **random** move, never the same one three times in a row
- All elites and bosses follow a **fixed cycle**, so their pattern can be learned
- Melee enemies dash to your hero when they attack

---

## Rewards & Progression

### Before the Boss (Automatic)

1. **Floor gear**, equipped immediately
2. **Skill empowerment**: all 4 skills grow to this floor's level

Click **Fight the Boss** (or press Enter) to continue.

### After the Boss (Choice)

- 3 random skills from your class pool, empowered to the cleared floor's level
- Pick one, then choose which skill it replaces, or skip

### Rematch Rewards

Only a boss rematch gives a reward: another skill choice at your furthest cleared floor's level.

---

## Audio

### Music

| Track | When played |
|-------|-------------|
| Teller of the Tales | Title screen |
| That Zen Moment | World map |
| Darkling | Regular fights |
| Burnt Spirit | Final boss (floor 5) |

- Tracks **loop** and fade between screens

### Sound Effects

| SFX | Used for |
|-----|----------|
| Sword (basic / great) | Swordsman attacks. The great sword sound plays once you own a better weapon |
| Wand (basic / great) | Sorcerist attacks, same rule |
| Victory / Defeat | End of a fight |

The game also asks for `battle_start`, `hit`, `block`, `buff` and `reward` sounds. They play only if matching `.wav`, `.ogg` or `.mp3` files are placed in a `sounds/` folder, and are silent otherwise.

- The great sword and great wand sounds are trimmed to a maximum play time so they don't overlap
- **Graceful degradation:** the game runs silently if there is no audio device

### Music Credit

Music by Kevin MacLeod (incompetech.com): "Teller of the Tales", "Darkling", "Burnt Spirit" and "That Zen Moment". Licensed under Creative Commons: By Attribution 4.0 License (http://creativecommons.org/licenses/by/4.0/). This is also shown on the in-game credits screen.

---

## Settings

Open from the **Settings** button on the main menu (bottom right, or **O**) or on the world map (bottom left). Esc goes back.

| Option | Description |
|--------|-------------|
| **Music** | Volume slider, 0–100%, applies immediately |
| **Sound Effects** | Volume slider, 0–100% (plays a test sound when changed) |
| **Fullscreen** | On/off, same as F11 |

Drag sliders with the mouse, or pick with Up/Down and change with Left/Right. Settings are saved to `settings.json` and applied on the next launch. The window is resizable and scales to fit, with black bars on non-16:9 windows.

---

## Credits

**Credits** on the main menu (bottom left, or **C**) shows the development team as role cards, plus the music credit. The names are in the `TEAM` list at the top of `game_state/credits_state.py`.

| Role | Team |
|------|------|
| Project Lead | Bernce Joseph E. Borabo |
| DevOps Engineer | Demel M. Vivares Jr. |
| Character Design and Development | Claude Emil A. Lorejo and AJ Nathaniel Manisan |
| Menu and UI | Stephanie E. Marapao and Aloha Jean C. Lapiz |
| Map Design | Steven Jey G. Decenan and Cedrick Samonte |
| Mobs and Boss | Belle Brainner B. Villagonzalo and Neil Bryan C. Cagadas |
| QA, Game Tester & Sound Effects | Cliff Harry E. Paran and Levon Jenu V. Lacia |
| Inventory & Mechanics | Rynz Karl J. Cebua and Lyster Loyd C. Cabillas |
| Skills | Mhike Clifford D. Boniao |

---

## Save System

### Files

- `save.json` in the project root: the roster and progress
- `settings.json`: volume and fullscreen (see [Settings](#settings))
- Both are git-ignored and created on first use

### What Is Saved

- Active character
- For each character: name, gender, class, bonus damage, cleared floors, equipped items and inventory (items keep their skills, empowerment and upgrades)
- HP is not saved; characters start at full HP

### When It Saves

- Character creation, selection and deletion
- Equipment changes at Base Camp
- Receiving floor gear and skill empowerment before a boss
- Clearing a floor
- Claiming or skipping a skill reward
- Returning to Base Camp

### Save Migration

- `weapon_library.py` has a `RENAMED` table for items renamed since older saves
- Items that no longer exist are dropped when an old save loads

---

## Asset Pipeline

The project can turn hand-drawn sprite sheets into animated characters.

### Sprite Sheet Slicing (`assets.py`)

- **Grid sheets:** uniform columns and rows
- **Single-row sheets:** poses found automatically (`"auto"`), or cut at hand-picked x positions
- Every frame is scaled to the same size and cropped, and offsets keep the feet steady

### Background Removal

- Near-white pixels connected to the edge (and large enclosed areas) become transparent
- Results are cached in `cache/` (safe to delete; rebuilt when the art changes)

### Feet Alignment

| Mode | Description |
|------|-------------|
| `cell` | Frames keep their position inside the sheet |
| `body` | Lined up on the character's own feet, ignoring glowing effects |
| `body-wide` | Same, using a wider lower band (wide stances) |
| `first-body` | Every frame uses the feet found in frame 0 |

### Edge Cleanup

Removes pieces of neighbouring frames, reddish halos along outlines and small loose specks.

### Tools (`tools/`)

Run from the project folder:

| Script | Purpose |
|--------|---------|
| `make_idle_sprites.py` | Idle sheets for hero outfits that only have an attack sheet |
| `make_hurt_sprites.py` | Hurt sheets for every hero idle sheet |
| `make_enemy_anims.py` | Idle and hurt animations for enemies with a drawn attack sheet |
| `align_idle.py` | Lines up the poses of an idle sheet |
| `seam_split.py` | Re-lays sheets whose poses overlap sideways |
| `make_ui_templates.py` | Turns the Base Camp and Create Character mockups into live UI templates |

---

## Project Structure

```
Python_TurnBasedRPG/
├── main.py                  # Entry point: window, settings, registers the game states
├── assets.py                # Image/sprite loading, sounds and music, saved settings
├── animation.py             # Sprite animation playback
├── ui.py                    # Shared UI drawing: panels, buttons, bars, icons
├── game_state/
│   ├── game_manager.py      # Run data, floor progression, save/load, fullscreen
│   ├── main_menu.py         # Title screen
│   ├── character_creation_state.py
│   ├── lobby_state.py       # Base Camp: roster, skills, equipment
│   ├── map_state.py         # World map and floor fight list
│   ├── combat_state.py      # Turn-based combat screen
│   ├── reward_state.py      # Pre-boss rewards and skill choice
│   ├── game_over_state.py
│   ├── settings_state.py    # Volume and fullscreen options
│   ├── credits_state.py     # Development team and music credit
│   └── ui_layouts.py
├── character/               # Entity and Player classes, hero sprites and inventory art
├── mobs_boss/               # Enemy class and library, floor 1-5 sprites
├── skills/                  # Skill class and skill library
├── inventory_mechanics/     # Items and the weapon/gear library
├── world/floor_map.py       # Fight order for each floor
├── map/, menu_ui/, items/   # Backgrounds, UI art, item art
├── sound_effects/           # Music and SFX files
├── tools/                   # Sprite and UI generation scripts
├── cache/                   # Processed sprite cache (safe to delete)
├── save.json                # Character save (created on first run)
└── settings.json            # Volume/fullscreen options (created on first change)
```

---

## Tips & Strategies

1. **Watch enemy intents:** put up Block when a big attack is coming, and attack when the enemy defends or buffs
2. **Apply Vulnerable first:** it adds 50% to everything that follows, and multi-hit skills benefit on every hit
3. **Burn and Poison ignore Block:** they're strong against enemies that turtle up
4. **Fights are back to back:** your HP carries over, so save healing skills for when you need them
5. **Learn the cycle:** elites and bosses repeat a fixed move order
6. **Use the number keys 1–4** for faster turns
7. **Exit Fight resets the floor:** only leave when you're happy to start that floor again
