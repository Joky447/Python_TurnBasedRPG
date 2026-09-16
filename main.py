import pygame
import sys
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
ENEMY_TEXT_COLOR = (255, 100, 100)
INTENT_TEXT_COLOR = (255, 200, 100)

# Fonts
font_large = pygame.font.SysFont("Arial", 28, bold=True)
font_medium = pygame.font.SysFont("Arial", 20, bold=True)
font_small = pygame.font.SysFont("Arial", 16)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def main():
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
    
    # Define UI layout variables
    ui_panel_height = 200
    ui_panel_rect = pygame.Rect(0, HEIGHT - ui_panel_height, WIDTH, ui_panel_height)
    
    # Define 4 Skill Buttons
    button_width, button_height = 200, 120
    button_spacing = 40
    start_x = (WIDTH - (4 * button_width + 3 * button_spacing)) // 2 
    button_y = HEIGHT - ui_panel_height + 40
    
    buttons = []
    for i, skill in enumerate(hero.equipped_skills):
        rect = pygame.Rect(start_x + i * (button_width + button_spacing), button_y, button_width, button_height)
        buttons.append({"rect": rect, "skill": skill})

    # Define End Turn Button (Positioned on the right, above the UI panel)
    end_turn_rect = pygame.Rect(WIDTH - 220, HEIGHT - ui_panel_height - 70, 180, 50)

    while running:
        mouse_pos = pygame.mouse.get_pos()

        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Detect Mouse Clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    # Check Skill Button Clicks
                    if hero.current_hp > 0 and goblin.current_hp > 0:
                        for btn in buttons:
                            if btn["rect"].collidepoint(mouse_pos):
                                btn["skill"].execute(hero, goblin)
                                if goblin.current_hp <= 0:
                                    print(f"{goblin.name} was defeated!")
                    
                    # Check End Turn Click
                    if end_turn_rect.collidepoint(mouse_pos) and goblin.current_hp > 0 and hero.current_hp > 0:
                        print("--- ENEMY TURN ---")
                        goblin.execute_intent(hero) # Enemy does its action
                        hero.reset_turn()           # Player gets Energy back, Block resets
                        if hero.current_hp > 0:
                            goblin.decide_intent()  # Enemy rolls a new intent for next turn
                
        # 2. Draw Background
        screen.fill(BACKGROUND_COLOR)
        
        # 3. Draw Game State (HUD)
        # Player Stats
        if hero.current_hp > 0:
            draw_text(f"{hero.name} (HP: {hero.current_hp}/{hero.max_hp})", font_large, TEXT_COLOR, 50, 50)
            draw_text(f"Energy: {hero.energy}/{hero.max_energy}   Block: {hero.block}", font_medium, TEXT_COLOR, 50, 90)
        else:
            draw_text("GAME OVER", font_large, ENEMY_TEXT_COLOR, 50, 50)
        
        # Enemy Stats
        if goblin.current_hp > 0:
            draw_text(f"{goblin.name} (HP: {goblin.current_hp}/{goblin.max_hp})", font_large, ENEMY_TEXT_COLOR, WIDTH - 400, 50)
            draw_text(f"Block: {goblin.block}", font_medium, ENEMY_TEXT_COLOR, WIDTH - 400, 90)
            draw_text(f"Intent: {goblin.intent['desc']} ({goblin.intent['val']})", font_medium, INTENT_TEXT_COLOR, WIDTH - 400, 130)
        else:
            draw_text("VICTORY!", font_large, (100, 255, 100), WIDTH - 400, 50)

        # 4. Draw UI Panel
        pygame.draw.rect(screen, UI_PANEL_COLOR, ui_panel_rect)
        
        # 5. Draw Skill Buttons
        for btn in buttons:
            skill = btn["skill"]
            
            # Hover & Energy logic
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

        # Update display
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()