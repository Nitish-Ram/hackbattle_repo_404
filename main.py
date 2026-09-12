import math
import os
import sys
import pygame

pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
FPS = 60

# Set to True if you need to debug collisions again
DEBUG_COLLISIONS = False


class Player:

  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.radius = 18
    self.speed = 6

    self.direction = "Right"
    self.frame_index = 0
    self.animation_speed = 0.15
    self.is_moving = False
    self.animations = self.load_animations()

  def load_animations(self):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    possible_bases = [
        os.path.join(script_dir, "chars", "Student 1"),
        os.path.join(script_dir, "Student 1"),
        os.path.join(script_dir, "codebase", "chars", "Student 1"),
    ]

    base_path = None
    for path in possible_bases:
      if os.path.exists(path):
        base_path = path
        break

    directions = ["Down", "Left", "Right", "Up"]
    animations = {}

    for d in directions:
      animations[d] = []
      for frame_num in range(1, 4):
        if base_path:
          file_path = os.path.join(base_path, d, f"{frame_num}.png")
          if os.path.exists(file_path):
            img = pygame.image.load(file_path).convert_alpha()
            img = pygame.transform.scale(img, (56, 56))
            animations[d].append(img)
            continue
        print(
            f"Warning: Sprite frame missing for {d}/{frame_num}.png in"
            f" {base_path}"
        )

    return animations

  def move(self, keys, walls):
    dx, dy = 0, 0
    self.is_moving = False

    if keys[pygame.K_w]:
      dy -= self.speed
      self.direction = "Up"
      self.is_moving = True
    if keys[pygame.K_s]:
      dy += self.speed
      self.direction = "Down"
      self.is_moving = True
    if keys[pygame.K_a]:
      dx -= self.speed
      self.direction = "Left"
      self.is_moving = True
    if keys[pygame.K_d]:
      dx += self.speed
      self.direction = "Right"
      self.is_moving = True

    self.x += dx
    if self.check_collision(walls):
      self.x -= dx

    self.y += dy
    if self.check_collision(walls):
      self.y -= dy

    if self.is_moving and self.animations.get(self.direction):
      self.frame_index += self.animation_speed
      if self.frame_index >= len(self.animations[self.direction]):
        self.frame_index = 0
    else:
      self.frame_index = 0

  def get_rect(self):
    return pygame.Rect(
        self.x - self.radius,
        self.y - self.radius,
        self.radius * 2,
        self.radius * 2,
    )

  def check_collision(self, walls):
    rect = self.get_rect()
    return any(rect.colliderect(w) for w in walls)

  def draw(self, surface, camera_x, camera_y):
    pos_x = int(self.x - camera_x)
    pos_y = int(self.y - camera_y)

    current_frames = self.animations.get(self.direction, [])
    if current_frames and int(self.frame_index) < len(current_frames):
      current_img = current_frames[int(self.frame_index)]
      rect = current_img.get_rect(center=(pos_x, pos_y))
      surface.blit(current_img, rect.topleft)
    else:
      pygame.draw.circle(surface, (255, 0, 0), (pos_x, pos_y), self.radius + 3)
      pygame.draw.circle(surface, (255, 255, 255), (pos_x, pos_y), self.radius)


def create_fog_of_war_vignette(view_radius=340):
  """Radial dark vignette centered on character."""
  vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
  vignette.fill((0, 0, 0, 245))

  center = (WIDTH // 2, HEIGHT // 2)
  for r in range(view_radius, 0, -6):
    alpha = int(245 * (r / view_radius) ** 2)
    pygame.draw.circle(vignette, (0, 0, 0, alpha), center, r)

  return vignette


def r_rect(ox, oy, w, h, rx, ry, rw, rh):
  return pygame.Rect(
      ox + int(rx * w), oy + int(ry * h), int(rw * w), int(rh * h)
  )


def load_floor_image(target_w, target_h):
  script_dir = os.path.dirname(os.path.abspath(__file__))
  search_subdirs = ["", "codebase", "assets"]
  possible_filenames = [
      "maze_plan.png",
      "maze_plan.jpg",
      "room_plan.jpeg",
      "room_plan.jpg",
      "room_plan.png",
  ]

  for sub in search_subdirs:
    for filename in possible_filenames:
      full_path = os.path.join(script_dir, sub, filename)
      if os.path.exists(full_path):
        try:
          img = pygame.image.load(full_path).convert()
          return pygame.transform.scale(img, (target_w, target_h))
        except pygame.error as e:
          print(f"Error loading image '{full_path}': {e}")
          sys.exit()

  print(f"Could not find floor map in: {script_dir}")
  sys.exit()


def main():
  screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
  pygame.display.set_caption("Maze Stealth Level")
  clock = pygame.time.Clock()

  MAP_W, MAP_H = 1600, 1600
  floor_img = load_floor_image(MAP_W, MAP_H)

  MAP_OFFSET_X = (WIDTH - MAP_W) // 2 if MAP_W < WIDTH else 0
  MAP_OFFSET_Y = (HEIGHT - MAP_H) // 2 if MAP_H < HEIGHT else 0

  # Player spawn positioned cleanly inside the left stairs entrance doorway
  SPAWN_X = MAP_OFFSET_X + int(MAP_W * 0.190)
  SPAWN_Y = MAP_OFFSET_Y + int(MAP_H * 0.500)

  # Goal elevator trigger on the right wall
  elevator_goal = r_rect(
      MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.850, 0.446, 0.047, 0.088
  )

  player = Player(SPAWN_X, SPAWN_Y)
  fog_overlay = create_fog_of_war_vignette(view_radius=340)

  # --- YOUR FULL 37 TUNED MAZE HITBOXES ---
  maze_walls = [
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.046, 0.033, 0.914, 0.076
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.048, 0.874, 0.902, 0.035
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.072, 0.080, 0.035, 0.380
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.070, 0.446, 0.035, 0.429
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.897, 0.080, 0.035, 0.367
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.897, 0.534, 0.035, 0.383
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.174, 0.169, 0.074, 0.189
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.217, 0.579, 0.093, 0.101
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.246, 0.167, 0.228, 0.073
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.302, 0.288, 0.081, 0.162
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.242, 0.723, 0.140, 0.098
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.424, 0.404, 0.099, 0.184
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.521, 0.165, 0.172, 0.085
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.440, 0.624, 0.231, 0.106
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.660, 0.323, 0.110, 0.156
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.707, 0.520, 0.084, 0.209
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.171, 0.632, 0.030, 0.229
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.380, 0.768, 0.144, 0.054
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.439, 0.236, 0.037, 0.054
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.382, 0.287, 0.217, 0.073
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.566, 0.359, 0.034, 0.019
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.568, 0.404, 0.083, 0.182
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.350, 0.496, 0.073, 0.092
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.350, 0.588, 0.037, 0.133
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.219, 0.355, 0.034, 0.174
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.254, 0.494, 0.094, 0.037
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.586, 0.730, 0.081, 0.037
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.586, 0.766, 0.217, 0.049
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.659, 0.251, 0.034, 0.071
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.743, 0.107, 0.056, 0.161
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.806, 0.165, 0.037, 0.383
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.843, 0.609, 0.037, 0.264
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.874, 0.539, 0.021, 0.026
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.871, 0.408, 0.026, 0.019
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.104, 0.519, 0.069, 0.037
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.106, 0.403, 0.068, 0.064
      ),
      r_rect(
          MAP_OFFSET_X, MAP_OFFSET_Y, MAP_W, MAP_H, 0.100, 0.551, 0.073, 0.037
      ),
  ]

  while True:
    screen.fill((5, 5, 5))

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()

    keys = pygame.key.get_pressed()

    if keys[pygame.K_ESCAPE]:
      pygame.quit()
      sys.exit()
    if keys[pygame.K_r]:
      player.x, player.y = SPAWN_X, SPAWN_Y
      player.direction = "Right"

    player.move(keys, maze_walls)

    # Reaching Elevator Goal
    if player.get_rect().colliderect(elevator_goal):
      print("Level Cleared! Reached the Elevator.")
      player.x, player.y = SPAWN_X, SPAWN_Y

    camera_x = player.x - WIDTH // 2
    camera_y = player.y - HEIGHT // 2

    # Draw Maze Background
    screen.blit(
        floor_img, (MAP_OFFSET_X - camera_x, MAP_OFFSET_Y - camera_y)
    )

    if DEBUG_COLLISIONS:
      for w in maze_walls:
        pygame.draw.rect(
            screen,
            (255, 0, 0),
            pygame.Rect(w.x - camera_x, w.y - camera_y, w.width, w.height),
            2,
        )

    player.draw(screen, camera_x, camera_y)

    # Blit Fog of War Overlay
    screen.blit(fog_overlay, (0, 0))

    pygame.display.flip()
    clock.tick(FPS)


if __name__ == "__main__":
  main()