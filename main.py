import pygame
import sys
import os
from game_logic import Skill, Weapon, Player, Enemy

# Initialize Pygame
pygame.init()

# Screen Dimensions & Frame Rate
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Turn-Based RPG")
clock = pygame.time.Clock()
FPS = 60

# Colors
BACKGROUND_COLOR = (30, 30, 40)
UI_PANEL_COLOR = (20, 20, 25)
BUTTON_COLOR = (70, 70, 90)
BUTTON_HOVER_COLOR = (100, 100, 120)
END_TURN_COLOR = (150, 40, 40)
END_TURN_HOVER = (200, 50, 50)
TEXT_COLOR = (255, 255, 255)
INTENT_TEXT_COLOR = (255, 200, 100)

# Character Colors (Placeholder Sprites)
HERO_COLOR = (50, 150, 255)   
GOBLIN_COLOR = (50, 200, 50)  

# Fonts
font_large = pygame.font.SysFont("Arial", 28, bold=True)
font_medium = pygame.font.SysFont("Arial", 20, bold=True)
font_small = pygame.font.SysFont("Arial", 16)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_health_bar(surface, x, y, current_hp, max_hp, width=150, height=20):
    ratio = max(0, current_hp / max_hp)
    pygame.draw.rect(surface, (100, 30, 30), (x, y, width, height))           
    pygame.draw.rect(surface, (40, 180, 40), (x, y, width * ratio, height))   
    pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)      

def main():
    # --- LOAD BACKGROUND IMAGE ---
   # --- LOAD BACKGROUND IMAGE ---
    bg_image_path = "bcgpc.png"  # <--- Change this line
    if os.path.exists(bg_image_path):
        bg_image = pygame.image.load(bg_image_path).convert()
        bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT)) # Stretches to fit screen
    else:
        print(f"Warning: '{bg_image_path}' not found. Using solid color fallback.")
        bg_image = None
    # -----------------------------

    # --- GAME LOGIC SETUP ---
    slash = Skill(name="Slash", energy_cost=1, damage=8, description="A basic blade attack.")
    parry = Skill(name="Parry", energy_cost=1, block=6, description="Raise guard to gain Block.")
    heavy_strike = Skill(name="Heavy Strike", energy_cost=2, damage=14, description="Powerful blow.")
    second_wind = Skill(name="Second Wind", energy_cost=1, heal=5, block=3, description="Recover HP & Block.")

    starter_sword = Weapon(name="Iron Sword", stat_bonus=2, skills=[slash, parry, heavy_strike, second_wind])
    hero = Player(name="Hero", gender="Boy", weapon=starter_sword)

    goblin = Enemy(name="Goblin Warrior", max_hp=30)
    goblin.decide_intent()
    # ------------------------

    running = True
    
    # UI Layout Variables
    ui_panel_height = 200
    ui_panel_rect = pygame.Rect(0, HEIGHT - ui_panel_height, WIDTH, ui_panel_height)
    
    button_width, button_height = 200, 120
    button_spacing = 40
    start_x = (WIDTH - (4 * button_width + 3 * button_spacing)) // 2 
    button_y = HEIGHT - ui_panel_height + 40
    
    buttons = []
    for i, skill in enumerate(hero.equipped_skills):
        rect = pygame.Rect(start_x + i * (button_width + button_spacing), button_y, button_width, button_height)
        buttons.append({"rect": rect, "skill": skill})

    end_turn_rect = pygame.Rect(WIDTH - 220, HEIGHT - ui_panel_height - 70, 180, 50)

    # Character Sprite Positions
    hero_rect = pygame.Rect(200, 250, 120, 200)
    goblin_rect = pygame.Rect(WIDTH - 320, 250, 140, 200)

    while running:
        mouse_pos = pygame.mouse.get_pos()

        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
                # Skill Buttons
                if hero.current_hp > 0 and goblin.current_hp > 0:
                    for btn in buttons:
                        if btn["rect"].collidepoint(mouse_pos) and hero.energy >= btn["skill"].energy_cost:
                            btn["skill"].execute(hero, goblin)
                
                # End Turn Button
                if end_turn_rect.collidepoint(mouse_pos) and goblin.current_hp > 0 and hero.current_hp > 0:
                    goblin.execute_intent(hero)
                    hero.reset_turn()
                    if hero.current_hp > 0:
                        goblin.decide_intent()
                
        # 2. Draw Background
        if bg_image:
            screen.blit(bg_image, (0, 0)) # Draws the image starting at the top-left corner
        else:
            screen.fill(BACKGROUND_COLOR)
        
        # 3. Draw Characters & Health Bars
        if hero.current_hp > 0:
            pygame.draw.rect(screen, HERO_COLOR, hero_rect, border_radius=15)
            draw_text(f"{hero.name}", font_large, TEXT_COLOR, hero_rect.x, hero_rect.y - 70)
            draw_health_bar(screen, hero_rect.x, hero_rect.y - 35, hero.current_hp, hero.max_hp, width=150)
            draw_text(f"{hero.current_hp}/{hero.max_hp} HP", font_small, TEXT_COLOR, hero_rect.x + 45, hero_rect.y - 32)
            draw_text(f"Energy: {hero.energy}/{hero.max_energy}  |  Block: {hero.block}", font_medium, TEXT_COLOR, hero_rect.x, hero_rect.bottom + 15)
        else:
            draw_text("GAME OVER", font_large, (255, 100, 100), hero_rect.x, hero_rect.y)

        if goblin.current_hp > 0:
            pygame.draw.rect(screen, GOBLIN_COLOR, goblin_rect, border_radius=15)
            draw_text(f"{goblin.name}", font_large, TEXT_COLOR, goblin_rect.x, goblin_rect.y - 70)
            draw_health_bar(screen, goblin_rect.x, goblin_rect.y - 35, goblin.current_hp, goblin.max_hp, width=150)
            draw_text(f"{goblin.current_hp}/{goblin.max_hp} HP", font_small, TEXT_COLOR, goblin_rect.x + 45, goblin_rect.y - 32)
            draw_text(f"Block: {goblin.block}", font_medium, TEXT_COLOR, goblin_rect.x, goblin_rect.bottom + 15)
            draw_text(f"Intent: {goblin.intent['desc']} ({goblin.intent['val']})", font_medium, INTENT_TEXT_COLOR, goblin_rect.x, goblin_rect.y - 110)
        else:
            draw_text("VICTORY!", font_large, (100, 255, 100), goblin_rect.x, goblin_rect.y)

        # 4. Draw UI Panel
        pygame.draw.rect(screen, UI_PANEL_COLOR, ui_panel_rect)
        
        # 5. Draw Skill Buttons
        for btn in buttons:
            skill = btn["skill"]
            
            if btn["rect"].collidepoint(mouse_pos) and hero.energy >= skill.energy_cost and hero.current_hp > 0 and goblin.current_hp > 0:
                pygame.draw.rect(screen, BUTTON_HOVER_COLOR, btn["rect"], border_radius=10)
            else:
                color = BUTTON_COLOR if (hero.energy >= skill.energy_cost and hero.current_hp > 0 and goblin.current_hp > 0) else (40, 40, 50)
                pygame.draw.rect(screen, color, btn["rect"], border_radius=10)
            
            pygame.draw.rect(screen, TEXT_COLOR, btn["rect"], 2, border_radius=10)
            
            name_surf = font_medium.render(skill.name, True, TEXT_COLOR)
            cost_surf = font_small.render(f"Cost: {skill.energy_cost} EN", True, (150, 200, 255))
            
            screen.blit(name_surf, (btn["rect"].x + 15, btn["rect"].y + 15))
            screen.blit(cost_surf, (btn["rect"].x + 15, btn["rect"].y + 45))

        # 6. Draw End Turn Button
        if goblin.current_hp > 0 and hero.current_hp > 0:
            if end_turn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, END_TURN_HOVER, end_turn_rect, border_radius=8)
            else:
                pygame.draw.rect(screen, END_TURN_COLOR, end_turn_rect, border_radius=8)
            
            pygame.draw.rect(screen, TEXT_COLOR, end_turn_rect, 2, border_radius=8)
            
            end_text = font_medium.render("End Turn", True, TEXT_COLOR)
            end_text_rect = end_text.get_rect(center=end_turn_rect.center)
            screen.blit(end_text, end_text_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()