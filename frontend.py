import os
import sys
import pygame

pygame.init()
pygame.mixer.init()

# Colors
BG_COLOR = (15, 15, 25)
TEXT_COLOR = (240, 240, 240)
HOVER_COLOR = (255, 204, 0)
PANEL_BG = (20, 20, 30, 210)  # Semi-transparent comic box background
BORDER_COLOR = (220, 220, 240)


class FrontendUI:

  def __init__(self, width, height):
    self.width = width
    self.height = height

    # Fonts
    try:
      self.title_font = pygame.font.Font("assets/fonts/pixel_font.ttf", 64)
      self.menu_font = pygame.font.Font("assets/fonts/pixel_font.ttf", 22)
      self.comic_font = pygame.font.Font("assets/fonts/pixel_font.ttf", 18)
    except FileNotFoundError:
      self.title_font = pygame.font.SysFont("Courier", 52, bold=True)
      self.menu_font = pygame.font.SysFont("Courier", 22)
      self.comic_font = pygame.font.SysFont("Courier", 18)

    # Load Background Map & Hostel Room
    self.bg_map = self._load_and_blur_map()
    self.hostel_room_bg = self._load_hostel_room()

    # Load Character Walk Cycle Animation Frames
    self.walk_frames = self._load_character_frames()
    self.anim_frame_index = 0
    self.anim_timer = 0
    self.char_x = -100  # Start off-screen to the left

    # Load Sound Effects
    self.select_sound = self._load_sound("assets/audio/sfx/select.wav")
    self.panel_sound = self._load_sound("assets/audio/sfx/panel.wav")

    # Prologue State Management & Comic Panels
    self.prologue_step = 0
    self.panels_data = [
        {
            "text": (
                "Final year. Finals week. One rumor everyone's heard but"
                " nobody's dared act on."
            ),
            "pos": (80, 100),
            "size": (550, 110),
        },
        {
            "text": (
                '“...they keep the actual paper in a safe. Inside the library.'
                ' Nobody\'s even allowed in that block after 10.” V heard these'
                ' words yesterday on his door.'
            ),
            "pos": (self.width - 640, 240),
            "size": (580, 140),
        },
        {
            "text": "Six minutes to curfew . . . ",
            "pos": (120, 420),
            "size": (400, 90),
        },
        {
            "text": "Just enough time for V to dare.",
            "pos": (self.width // 2 - 275, self.height - 180),
            "size": (550, 100),
        },
    ]
    self.char_typed_len = 0
    self.type_timer = 0

  def _load_sound(self, path):
    if os.path.exists(path):
      try:
        return pygame.mixer.Sound(path)
      except Exception:
        pass
    return None

  def _load_and_blur_map(self):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(script_dir, "assets", "vit_16bit_map.png")
    if not os.path.exists(map_path):
      map_path = os.path.join(script_dir, "vit_16bit_map.png")

    if os.path.exists(map_path):
      try:
        img = pygame.image.load(map_path).convert()
        scaled = pygame.transform.smoothscale(img, (self.width, self.height))
        small = pygame.transform.smoothscale(
            scaled, (self.width // 8, self.height // 8)
        )
        blurred = pygame.transform.smoothscale(small, (self.width, self.height))
        dark_overlay = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        dark_overlay.fill((10, 10, 18, 160))
        blurred.blit(dark_overlay, (0, 0))
        return blurred
      except Exception as e:
        print(f"Error loading map background: {e}")

    fallback = pygame.Surface((self.width, self.height))
    fallback.fill(BG_COLOR)
    return fallback

  def _load_hostel_room(self):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    room_path = os.path.join(script_dir, "assets", "hostel room.png")
    if not os.path.exists(room_path):
      room_path = os.path.join(script_dir, "hostel room.png")

    if os.path.exists(room_path):
      try:
        img = pygame.image.load(room_path).convert()
        scaled = pygame.transform.smoothscale(img, (self.width, self.height))
        dark_tint = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dark_tint.fill((0, 0, 0, 90))
        scaled.blit(dark_tint, (0, 0))
        return scaled
      except Exception as e:
        print(f"Error loading hostel room background: {e}")

    fallback = pygame.Surface((self.width, self.height))
    fallback.fill((30, 30, 40))
    return fallback

  def _load_character_frames(self):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chars_dir = os.path.join(script_dir, "chars")

    frames = []
    frame_filenames = [
        "image_66845d.png",
        "image_6684b9.png",
        "image_66849a.png",
    ]

    for fname in frame_filenames:
      path = os.path.join(chars_dir, fname)
      if os.path.exists(path):
        try:
          img = pygame.image.load(path).convert_alpha()
          img = pygame.transform.scale(img, (64, 64))
          frames.append(img)
        except Exception:
          pass

    if not frames:
      placeholder = pygame.Surface((64, 64), pygame.SRCALPHA)
      pygame.draw.circle(placeholder, (255, 0, 0), (32, 32), 20)
      frames.append(placeholder)

    return frames

  def update_animation(self):
    self.char_x += 3
    if self.char_x > self.width + 50:
      self.char_x = -100

    self.anim_timer += 1
    if self.anim_timer >= 10:
      self.anim_timer = 0
      self.anim_frame_index = (self.anim_frame_index + 1) % len(
          self.walk_frames
      )

  def draw_main_menu(self, surface):
    surface.blit(self.frontend.bg_map, (0, 0))  # Or self.bg_map depending on your setup
    self.update_animation()
    mouse_pos = pygame.mouse.get_pos()

    title_y = self.height // 3

    yellow_part = self.title_font.render("ONE NIGHT ", True, (255, 204, 0))
    red_part = self.title_font.render("BEFORE", True, (255, 69, 58))

    total_width = yellow_part.get_width() + red_part.get_width()
    title_x = (self.width - total_width) // 2

    surface.blit(yellow_part, (title_x, title_y))
    surface.blit(red_part, (title_x + yellow_part.get_width(), title_y))

    current_char_image = self.walk_frames[self.anim_frame_index]
    char_y = title_y - 50
    surface.blit(current_char_image, (self.char_x, char_y))

    sub_surface = self.menu_font.render(
        "The Ultimate Campus Heist", True, TEXT_COLOR
    )
    sub_rect = sub_surface.get_rect(center=(self.width // 2, title_y + 90))
    surface.blit(sub_surface, sub_rect)

    # --- CLEAN START OPTION ---
    start_surface = self.menu_font.render("START", True, (150, 150, 150))
    start_rect = start_surface.get_rect(
        center=(self.width // 2, self.height // 2 + 60)
    )

    if start_rect.collidepoint(mouse_pos):
      start_surface = self.menu_font.render("START", True, (255, 204, 0))

    surface.blit(start_surface, start_rect)

    # --- CLEAN QUIT OPTION ---
    quit_surface = self.menu_font.render("QUIT", True, (150, 150, 150))
    quit_rect = quit_surface.get_rect(
        center=(self.width // 2, self.height // 2 + 130)
    )

    if quit_rect.collidepoint(mouse_pos):
      quit_surface = self.menu_font.render("QUIT", True, (255, 69, 58))

    surface.blit(quit_surface, quit_rect)

  def reset_prologue(self):
    self.prologue_step = 0
    self.char_typed_len = 0

  def advance_prologue(self):
    if self.prologue_step < len(self.panels_data) - 1:
      self.prologue_step += 1
      self.char_typed_len = 0
      if self.panel_sound:
        self.panel_sound.play()
      return False
    return True  # Completed all comic panels, ready for gameplay loop

  def draw_prologue(self, surface):
    # 1. Draw Hostel Room Background
    surface.blit(self.hostel_room_bg, (0, 0))

    # Typewriter character reveal ticker
    current_target_text = self.panels_data[self.prologue_step]["text"]
    self.type_timer += 1
    if self.type_timer >= 2 and self.char_typed_len < len(
        current_target_text
    ):
      self.char_typed_len += 1
      self.type_timer = 0

    # 2. Render all visible comic boxes up to the current step
    for i in range(self.prologue_step + 1):
      panel = self.panels_data[i]
      px, py = panel["pos"]
      pw, ph = panel["size"]

      box_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
      box_surf.fill(PANEL_BG)
      surface.blit(box_surf, (px, py))
      pygame.draw.rect(
          surface, BORDER_COLOR, pygame.Rect(px, py, pw, ph), 2, border_radius=6
      )

      text_to_show = (
          panel["text"]
          if i < self.prologue_step
          else panel["text"][: self.char_typed_len]
      )

      # Word wrapping logic for comic box text
      words = text_to_show.split(" ")
      lines = []
      current_line = ""
      for word in words:
        test_line = current_line + word + " "
        if self.comic_font.size(test_line)[0] < pw - 30:
          current_line = test_line
        else:
          lines.append(current_line)
          current_line = word + " "
      lines.append(current_line)

      line_y = py + 15
      for line in lines:
        rendered_line = self.comic_font.render(line, True, TEXT_COLOR)
        surface.blit(rendered_line, (px + 15, line_y))
        line_y += 24

    # 3. Draw Interactive "NEXT ➔" Button
    btn_rect = pygame.Rect(self.width - 160, self.height - 80, 130, 45)
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = btn_rect.collidepoint(mouse_pos)

    btn_color = (255, 204, 0) if is_hovered else (40, 40, 60)
    text_color = (15, 15, 25) if is_hovered else (240, 240, 240)

    pygame.draw.rect(surface, btn_color, btn_rect, border_radius=8)
    pygame.draw.rect(surface, BORDER_COLOR, btn_rect, 2, border_radius=8)

    btn_text = self.menu_font.render("NEXT ➔", True, text_color)
    surface.blit(
        btn_text,
        btn_text.get_rect(
            center=(btn_rect.x + btn_rect.w // 2, btn_rect.y + btn_rect.h // 2)
        ),
    )

  def draw_pause_button(self, surface):
    # Draw a small clickable Pause button in the top-right corner during gameplay
    btn_rect = pygame.Rect(self.width - 90, 20, 70, 35)
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = btn_rect.collidepoint(mouse_pos)

    bg_color = (255, 204, 0) if is_hovered else (30, 30, 45)
    text_color = (15, 15, 25) if is_hovered else (240, 240, 240)

    pygame.draw.rect(surface, bg_color, btn_rect, border_radius=6)
    pygame.draw.rect(surface, (220, 220, 240), btn_rect, 2, border_radius=6)

    txt = self.menu_font.render("PAUSE", True, text_color)
    surface.blit(
        txt,
        txt.get_rect(
            center=(btn_rect.x + btn_rect.w // 2, btn_rect.y + btn_rect.h // 2)
        ),
    )
    return btn_rect

  def draw_pause_menu(self, surface):
    # Dark semi-transparent overlay
    overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
    overlay.fill((10, 10, 20, 200))
    surface.blit(overlay, (0, 0))

    # Pause Title
    title_surf = self.title_font.render("PAUSED", True, (255, 69, 58))
    title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 3))
    surface.blit(title_surf, title_rect)

    # Menu Box container
    box_w, box_h = 400, 220
    box_x = (self.width - box_w) // 2
    box_y = (self.height - box_h) // 2
    box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box_surf.fill((20, 20, 30, 230))
    surface.blit(box_surf, (box_x, box_y))
    pygame.draw.rect(
        surface, (220, 220, 240), pygame.Rect(box_x, box_y, box_w, box_h), 2, border_radius=8
    )

    # Options text / Clickable buttons representation
    resume_surf = self.menu_font.render("Press ESC to Resume", True, (255, 204, 0))
    resume_rect = resume_surf.get_rect(center=(self.width // 2, box_y + 70))
    surface.blit(resume_surf, resume_rect)

    quit_surf = self.menu_font.render("Press Q to Quit to Menu", True, (255, 69, 58))
    quit_rect = quit_surf.get_rect(center=(self.width // 2, box_y + 140))
    surface.blit(quit_surf, quit_rect)


# --- Standalone Test Execution ---
if __name__ == "__main__":
  WIDTH, HEIGHT = 1200, 800
  test_screen = pygame.display.set_mode((WIDTH, HEIGHT))
  pygame.display.set_caption("Comic Prologue - One Night Before")
  clock = pygame.time.Clock()

  ui = FrontendUI(WIDTH, HEIGHT)
  test_state = "MENU"

  running = True
  while running:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          running = False
        elif test_state == "MENU" and event.key == pygame.K_RETURN:
          if ui.select_sound:
            ui.select_sound.play()
          test_state = "PROLOGUE"
          ui.reset_prologue()
        elif test_state == "PROLOGUE":
          if event.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
            is_done = ui.advance_prologue()
            if is_done:
              test_state = "MENU"  # Loop back to menu for testing

      elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1 and test_state == "PROLOGUE":
          btn_rect = pygame.Rect(WIDTH - 160, HEIGHT - 80, 130, 45)
          if btn_rect.collidepoint(event.pos):
            is_done = ui.advance_prologue()
            if is_done:
              test_state = "MENU"

    if test_state == "MENU":
      ui.draw_main_menu(test_screen)
    elif test_state == "PROLOGUE":
      ui.draw_prologue(test_screen)

    pygame.display.flip()
    clock.tick(60)

  pygame.quit()
  sys.exit()