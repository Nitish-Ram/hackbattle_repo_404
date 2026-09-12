# frontend.py
import sys
import pygame

pygame.init()
pygame.mixer.init()

# Colors
BG_COLOR = (15, 15, 25)
TEXT_COLOR = (240, 240, 240)
ACCENT_COLOR = (255, 69, 58)
HOVER_COLOR = (255, 204, 0)


class FrontendUI:

  def __init__(self, width, height):
    self.width = width
    self.height = height
    # Load your pixel font for the title and menu options
    try:
      self.title_font = pygame.font.Font("assets/fonts/pixel_bod.ttf", 64)
      # Use a smaller size of the same pixel font for the menu options
      self.menu_font = pygame.font.Font("assets/fonts/pixel_bod.ttf", 24)
    except FileNotFoundError:
      # Fallback if the .ttf file isn't found
      self.title_font = pygame.font.SysFont("Courier", 52, bold=True)
      self.menu_font = pygame.font.SysFont("Courier", 24)

  def draw_main_menu(self, surface):
    surface.fill(BG_COLOR)

    # 1. Load your pixel font (Make sure you drop your .ttf font file into assets/fonts/)
    # If you haven't added a font file yet, this will fallback to a chunky system font
    try:
      custom_title_font = pygame.font.Font("assets/fonts/pixel_font.ttf", 64)
      custom_sub_font = pygame.font.Font("assets/fonts/pixel_sub.ttf", 24)
    except FileNotFoundError:
      # Fallback if the .ttf file isn't in assets/fonts/ yet
      custom_title_font = pygame.font.SysFont("Courier", 52, bold=True)
      custom_sub_font = pygame.font.SysFont("Courier", 24)

    # 2. Render "ONE NIGHT" (Yellow) and "BEFORE" (Red) separately
    yellow_part = custom_title_font.render("ONE NIGHT ", True, (255, 204, 0))
    red_part = custom_title_font.render("BEFORE", True, (255, 69, 58))

    # Calculate total width to center them perfectly together as one title
    total_width = yellow_part.get_width() + red_part.get_width()
    title_x = (self.width - total_width) // 2
    title_y = self.height // 3

    # Blit both parts side by side
    surface.blit(yellow_part, (title_x, title_y))
    surface.blit(red_part, (title_x + yellow_part.get_width(), title_y))

    # Subtitle
    sub_surface = custom_sub_font.render(
        "The Ultimate VIT Campus Heist", True, TEXT_COLOR
    )
    sub_rect = sub_surface.get_rect(
        center=(self.width // 2, title_y + 90)
    )
    surface.blit(sub_surface, sub_rect)

    # Menu Options
    start_surface = self.menu_font.render(
        "> Press ENTER to Start Heist", True, HOVER_COLOR
    )
    start_rect = start_surface.get_rect(
        center=(self.width // 2, self.height // 2 + 80)
    )
    surface.blit(start_surface, start_rect)

    quit_surface = self.menu_font.render(
        "Press ESC to Quit", True, (150, 150, 150)
    )
    quit_rect = quit_surface.get_rect(
        center=(self.width // 2, self.height // 2 + 140)
    )
    surface.blit(quit_surface, quit_rect)

  def draw_prologue(self, surface):
    surface.fill(BG_COLOR)
    prologue_text = self.menu_font.render(
        "Prologue: Finals week is here. Time to hack the system...", True, TEXT_COLOR
    )
    rect = prologue_text.get_rect(center=(self.width // 2, self.height // 2))
    surface.blit(prologue_text, rect)

    continue_hint = self.menu_font.render(
        "Press SPACE to enter Level 1 (Hostel)", True, HOVER_COLOR
    )
    hint_rect = continue_hint.get_rect(
        center=(self.width // 2, self.height // 2 + 60)
    )
    surface.blit(continue_hint, hint_rect)

    # --- Standalone Test Execution ---
if __name__ == "__main__":
  WIDTH, HEIGHT = 800, 600
  test_screen = pygame.display.set_mode((WIDTH, HEIGHT))
  pygame.display.set_caption("Frontend Preview - One Night Before")
  clock = pygame.time.Clock()

  ui = FrontendUI(WIDTH, HEIGHT)
  test_state = "MENU"

  # Load your sound effect (make sure your file is inside assets/audio/sfx/)
  try:
    select_sound = pygame.mixer.Sound("assets/audio/sfx/select.wav")
  except pygame.error:
    print(
        "Warning: 'click.wav' not found in assets/audio/sfx/. Sound will be"
        " skipped."
    )
    select_sound = None

  running = True
  while running:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          running = False

        elif test_state == "MENU" and event.key == pygame.K_RETURN:
          if select_sound:
            select_sound.play()  # Play SFX on selection
          test_state = "PROLOGUE"

        elif test_state == "PROLOGUE" and event.key == pygame.K_SPACE:
          if select_sound:
            select_sound.play()  # Play SFX on selection
          test_state = "MENU"  # Loops back to menu for easy testing

    # Draw based on state
    if test_state == "MENU":
      ui.draw_main_menu(test_screen)
    elif test_state == "PROLOGUE":
      ui.draw_prologue(test_screen)

    pygame.display.flip()
    clock.tick(60)

  pygame.quit()
  sys.exit()