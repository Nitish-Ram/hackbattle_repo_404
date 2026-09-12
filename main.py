import math
import os
import sys
import pygame

pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
FPS = 60

DEBUG_COLLISIONS = False


class Player:

  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.speed = 6

    self.direction = "Down"
    self.frame_index = 0
    self.animation_speed = 0.15
    self.is_moving = False

    self.in_room_level = True
    self.radius = 20

    self.room_animations = self.load_animations(size=(64, 64))
    self.hallway_animations = self.load_animations(size=(56, 56))

  def set_level_state(self, in_hallway):
    self.in_room_level = not in_hallway
    self.radius = 18 if in_hallway else 20

  def load_animations(self, size):
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
            img = pygame.transform.scale(img, size)
            animations[d].append(img)
            continue

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

    active_anims = (
        self.room_animations if self.in_room_level else self.hallway_animations
    )
    if self.is_moving and active_anims.get(self.direction):
      self.frame_index += self.animation_speed
      if self.frame_index >= len(active_anims[self.direction]):
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

    active_anims = (
        self.room_animations if self.in_room_level else self.hallway_animations
    )
    current_frames = active_anims.get(self.direction, [])

    if current_frames and int(self.frame_index) < len(current_frames):
      current_img = current_frames[int(self.frame_index)]
      rect = current_img.get_rect(center=(pos_x, pos_y))
      surface.blit(current_img, rect.topleft)
    else:
      pygame.draw.circle(surface, (255, 0, 0), (pos_x, pos_y), self.radius + 3)
      pygame.draw.circle(surface, (255, 255, 255), (pos_x, pos_y), self.radius)


class SecurityCamera:

  def __init__(
      self,
      x,
      y,
      base_angle_deg=90,
      sweep_range_deg=180,
      sweep_speed=0.006,
      view_dist=160,
      fov_deg=24,
  ):
    self.x = x
    self.y = y
    self.base_angle = math.radians(base_angle_deg)
    self.sweep_range = math.radians(sweep_range_deg / 2)
    self.sweep_speed = sweep_speed
    self.view_dist = view_dist
    self.fov = math.radians(fov_deg)

    self.time = 0
    self.current_angle = self.base_angle

  def update(self):
    self.time += self.sweep_speed
    self.current_angle = (
        self.base_angle + math.sin(self.time) * self.sweep_range
    )

  def detects_player(self, player):
    px, py = player.x, player.y
    dist = math.hypot(px - self.x, py - self.y)
    if dist > self.view_dist:
      return False

    angle_to_player = math.atan2(py - self.y, px - self.x)
    diff = (angle_to_player - self.current_angle + math.pi) % (
        2 * math.pi
    ) - math.pi
    return abs(diff) <= (self.fov / 2)

  def draw(self, surface, camera_x, camera_y):
    screen_x = int(self.x - camera_x)
    screen_y = int(self.y - camera_y)

    # Offscreen Culling (saves rendering performance)
    if not (
        -self.view_dist <= screen_x <= WIDTH + self.view_dist
        and -self.view_dist <= screen_y <= HEIGHT + self.view_dist
    ):
      return

    # Fast Local Surface Blitting (Fixes 24 FPS Lag -> 60 FPS)
    size = int(self.view_dist * 2)
    local_center = (self.view_dist, self.view_dist)

    left_angle = self.current_angle - (self.fov / 2)
    right_angle = self.current_angle + (self.fov / 2)

    p1 = local_center
    p2 = (
        local_center[0] + math.cos(left_angle) * self.view_dist,
        local_center[1] + math.sin(left_angle) * self.view_dist,
    )
    p3 = (
        local_center[0] + math.cos(right_angle) * self.view_dist,
        local_center[1] + math.sin(right_angle) * self.view_dist,
    )

    cone_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.polygon(cone_surface, (255, 30, 30, 85), [p1, p2, p3])
    pygame.draw.line(cone_surface, (255, 80, 80, 200), p1, p2, 2)
    pygame.draw.line(cone_surface, (255, 80, 80, 200), p1, p3, 2)

    surface.blit(
        cone_surface, (screen_x - self.view_dist, screen_y - self.view_dist)
    )

    pygame.draw.circle(surface, (40, 40, 40), (screen_x, screen_y), 9)
    pygame.draw.circle(surface, (255, 50, 50), (screen_x, screen_y), 4)


def create_fog_of_war_vignette(view_radius=340):
  vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
  vignette.fill((0, 0, 0, 245))

  center = (WIDTH // 2, HEIGHT // 2)
  for r in range(view_radius, 0, -6):
    alpha = int(245 * (r / view_radius) ** 2)
    pygame.draw.circle(vignette, (0, 0, 0, alpha), center, r)

  return vignette


def draw_gold_indicator(surface, rect, camera_x, camera_y):
  indicator_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
  indicator_surf.fill((255, 215, 0, 60))
  pygame.draw.rect(
      indicator_surf, (255, 223, 0, 160), (0, 0, rect.width, rect.height), 2
  )
  surface.blit(indicator_surf, (rect.x - camera_x, rect.y - camera_y))


def r_rect(ox, oy, w, h, rx, ry, rw, rh):
  return pygame.Rect(
      ox + int(rx * w), oy + int(ry * h), int(rw * w), int(rh * h)
  )


def load_image(filenames, target_w, target_h):
  script_dir = os.path.dirname(os.path.abspath(__file__))
  search_subdirs = ["", "codebase", "assets"]

  for sub in search_subdirs:
    for filename in filenames:
      full_path = os.path.join(script_dir, sub, filename)
      if os.path.exists(full_path):
        try:
          img = pygame.image.load(full_path).convert()
          return pygame.transform.scale(img, (target_w, target_h))
        except pygame.error as e:
          print(f"Error loading image '{full_path}': {e}")
          sys.exit()

  print(f"Could not find image assets {filenames} in {script_dir}")
  sys.exit()


def main():
  screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
  pygame.display.set_caption("Office Stealth Game")
  clock = pygame.time.Clock()

  ROOM_W, ROOM_H = 1000, 850
  ROOM_OFFSET_X = (WIDTH - ROOM_W) // 2
  ROOM_OFFSET_Y = (HEIGHT - ROOM_H) // 2
  room_img = load_image(
      ["room_plan.png", "room_plan.jpeg", "room_plan.jpg"], ROOM_W, ROOM_H
  )

  HALLWAY_W, HALLWAY_H = 1600, 1600
  HALLWAY_OFFSET_X = (WIDTH - HALLWAY_W) // 2 if HALLWAY_W < WIDTH else 0
  HALLWAY_OFFSET_Y = (HEIGHT - HALLWAY_H) // 2 if HALLWAY_H < HEIGHT else 0
  hallway_img = load_image(
      ["maze_plan.png", "maze_plan.jpeg", "maze_plan.jpg"],
      HALLWAY_W,
      HALLWAY_H,
  )

  INITIAL_ROOM_SPAWN_X = ROOM_OFFSET_X + 850
  INITIAL_ROOM_SPAWN_Y = ROOM_OFFSET_Y + 230

  ROOM_DOOR_SPAWN_X = ROOM_OFFSET_X + 490
  ROOM_DOOR_SPAWN_Y = ROOM_OFFSET_Y + 700

  HALLWAY_SPAWN_X = HALLWAY_OFFSET_X + int(HALLWAY_W * 0.150)
  HALLWAY_SPAWN_Y = HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.185)

  player = Player(INITIAL_ROOM_SPAWN_X, INITIAL_ROOM_SPAWN_Y)
  in_hallway = False

  fog_overlay = create_fog_of_war_vignette(view_radius=340)

  cameras = [
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.429),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.102),
          base_angle_deg=58,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.679),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.354),
          base_angle_deg=180,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.383),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.767),
          base_angle_deg=300,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.534),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.855),
          base_angle_deg=294,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.584),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.728),
          base_angle_deg=90,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.709),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.535),
          base_angle_deg=178,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.517),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.573),
          base_angle_deg=68,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.429),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.412),
          base_angle_deg=182,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.307),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.440),
          base_angle_deg=90,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.608),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.122),
          base_angle_deg=90,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.799),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.779),
          base_angle_deg=136,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.848),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.611),
          base_angle_deg=168,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.694),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.320),
          base_angle_deg=274,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.598),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.295),
          base_angle_deg=246,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.270),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.672),
          base_angle_deg=78,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.217),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.581),
          base_angle_deg=172,
          sweep_range_deg=180,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
      SecurityCamera(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.176),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.351),
          base_angle_deg=90,
          sweep_range_deg=140,
          sweep_speed=0.006,
          view_dist=160,
          fov_deg=24,
      ),
  ]

  room_walls = [
      pygame.Rect(ROOM_OFFSET_X + 1, ROOM_OFFSET_Y + 0, 10, 848),
      pygame.Rect(ROOM_OFFSET_X + 931, ROOM_OFFSET_Y + 510, 72, 252),
      pygame.Rect(ROOM_OFFSET_X + 81, ROOM_OFFSET_Y + 47, 81, 198),
      pygame.Rect(ROOM_OFFSET_X + 243, ROOM_OFFSET_Y + 163, 144, 150),
      pygame.Rect(ROOM_OFFSET_X + 380, ROOM_OFFSET_Y + 77, 102, 237),
      pygame.Rect(ROOM_OFFSET_X + 663, ROOM_OFFSET_Y + 446, 151, 153),
      pygame.Rect(ROOM_OFFSET_X + 82, ROOM_OFFSET_Y + 604, 211, 157),
      pygame.Rect(ROOM_OFFSET_X + 579, ROOM_OFFSET_Y + 452, 92, 315),
      pygame.Rect(ROOM_OFFSET_X + 6, ROOM_OFFSET_Y + 168, 996, 32),
      pygame.Rect(ROOM_OFFSET_X + 668, ROOM_OFFSET_Y + 166, 142, 142),
      pygame.Rect(ROOM_OFFSET_X + 588, ROOM_OFFSET_Y + 46, 80, 196),
      pygame.Rect(ROOM_OFFSET_X + 8, ROOM_OFFSET_Y + 750, 426, 18),
      pygame.Rect(ROOM_OFFSET_X + 562, ROOM_OFFSET_Y + 751, 436, 14),
      pygame.Rect(ROOM_OFFSET_X + 984, ROOM_OFFSET_Y + -1, 16, 546),
      pygame.Rect(ROOM_OFFSET_X + -7, ROOM_OFFSET_Y + 507, 80, 250),
  ]

  room_exit_door = pygame.Rect(
      ROOM_OFFSET_X + 434, ROOM_OFFSET_Y + 752, 128, 40
  )

  hallway_room_door = r_rect(
      HALLWAY_OFFSET_X,
      HALLWAY_OFFSET_Y,
      HALLWAY_W,
      HALLWAY_H,
      0.059,
      0.151,
      0.058,
      0.068,
  )

  hallway_walls = [
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.046,
          0.033,
          0.914,
          0.076,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.048,
          0.874,
          0.902,
          0.035,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.072,
          0.080,
          0.035,
          0.380,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.070,
          0.446,
          0.035,
          0.429,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.897,
          0.080,
          0.035,
          0.367,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.897,
          0.534,
          0.035,
          0.383,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.174,
          0.169,
          0.074,
          0.189,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.217,
          0.579,
          0.093,
          0.101,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.246,
          0.167,
          0.228,
          0.073,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.302,
          0.288,
          0.081,
          0.162,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.242,
          0.723,
          0.140,
          0.098,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.424,
          0.404,
          0.099,
          0.184,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.521,
          0.165,
          0.172,
          0.085,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.440,
          0.624,
          0.231,
          0.106,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.660,
          0.323,
          0.110,
          0.156,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.707,
          0.520,
          0.084,
          0.209,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.171,
          0.632,
          0.030,
          0.229,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.380,
          0.768,
          0.144,
          0.054,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.439,
          0.236,
          0.037,
          0.054,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.382,
          0.287,
          0.217,
          0.073,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.566,
          0.359,
          0.034,
          0.019,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.568,
          0.404,
          0.083,
          0.182,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.350,
          0.496,
          0.073,
          0.092,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.350,
          0.588,
          0.037,
          0.133,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.219,
          0.355,
          0.034,
          0.174,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.254,
          0.494,
          0.094,
          0.037,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.586,
          0.730,
          0.081,
          0.037,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.586,
          0.766,
          0.217,
          0.049,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.659,
          0.251,
          0.034,
          0.071,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.743,
          0.107,
          0.056,
          0.161,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.806,
          0.165,
          0.037,
          0.383,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.843,
          0.609,
          0.037,
          0.264,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.874,
          0.539,
          0.021,
          0.026,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.871,
          0.408,
          0.026,
          0.019,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.104,
          0.519,
          0.069,
          0.037,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.106,
          0.403,
          0.068,
          0.064,
      ),
      r_rect(
          HALLWAY_OFFSET_X,
          HALLWAY_OFFSET_Y,
          HALLWAY_W,
          HALLWAY_H,
          0.100,
          0.551,
          0.073,
          0.037,
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
      player.x, player.y = INITIAL_ROOM_SPAWN_X, INITIAL_ROOM_SPAWN_Y
      player.direction = "Down"
      in_hallway = False
      player.set_level_state(in_hallway)

    player_rect = player.get_rect()

    if not in_hallway and player_rect.colliderect(room_exit_door):
      in_hallway = True
      player.set_level_state(in_hallway)
      player.x, player.y = HALLWAY_SPAWN_X, HALLWAY_SPAWN_Y
      player.direction = "Right"
    elif in_hallway and player_rect.colliderect(hallway_room_door):
      in_hallway = False
      player.set_level_state(in_hallway)
      player.x, player.y = ROOM_DOOR_SPAWN_X, ROOM_DOOR_SPAWN_Y
      player.direction = "Up"

    active_walls = hallway_walls if in_hallway else room_walls
    player.move(keys, active_walls)

    if in_hallway:
      for cam in cameras:
        cam.update()

    if not in_hallway:
      camera_x, camera_y = 0, 0
    else:
      camera_x = player.x - WIDTH // 2
      camera_y = player.y - HEIGHT // 2

    if not in_hallway:
      screen.blit(
          room_img, (ROOM_OFFSET_X - camera_x, ROOM_OFFSET_Y - camera_y)
      )

      draw_gold_indicator(screen, room_exit_door, camera_x, camera_y)

      if DEBUG_COLLISIONS:
        for w in room_walls:
          pygame.draw.rect(
              screen,
              (255, 0, 0),
              pygame.Rect(w.x - camera_x, w.y - camera_y, w.width, w.height),
              2,
          )

      player.draw(screen, camera_x, camera_y)

    else:
      screen.blit(
          hallway_img,
          (HALLWAY_OFFSET_X - camera_x, HALLWAY_OFFSET_Y - camera_y),
      )

      draw_gold_indicator(screen, hallway_room_door, camera_x, camera_y)

      if DEBUG_COLLISIONS:
        for w in hallway_walls:
          pygame.draw.rect(
              screen,
              (255, 0, 0),
              pygame.Rect(w.x - camera_x, w.y - camera_y, w.width, w.height),
              2,
          )

      for cam in cameras:
        cam.draw(screen, camera_x, camera_y)

      player.draw(screen, camera_x, camera_y)
      screen.blit(fog_overlay, (0, 0))

    pygame.display.flip()
    clock.tick(FPS)


if __name__ == "__main__":
  main()