import collections
import math
import os
import random
import sys
import pygame
from frontend import FrontendUI

pygame.init()
pygame.mixer.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
FPS = 60

DEBUG_COLLISIONS = False

STATE_MENU = "MENU"
STATE_PROLOGUE = "PROLOGUE"
STATE_GAMEPLAY = "GAMEPLAY"


class Player:

  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.speed = 6

    self.direction = "Down"
    self.frame_index = 0
    self.animation_speed = 0.15
    self.is_moving = False
    self.is_hidden = False

    self.in_room_level = True
    self.radius = 20
    self.hearts = 3

    self.room_animations = self.load_animations(
        size=(64, 64), folder_name="Student 1"
    )
    self.hallway_animations = self.load_animations(
        size=(56, 56), folder_name="Student 1"
    )

  def set_level_state(self, in_hallway):
    self.in_room_level = not in_hallway
    self.radius = 18 if in_hallway else 20
    self.is_hidden = False

  def load_animations(self, size, folder_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_bases = [
        os.path.join(script_dir, "chars", folder_name),
        os.path.join(script_dir, folder_name),
        os.path.join(script_dir, "codebase", "chars", folder_name),
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
    if self.is_hidden:
      return

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
    if self.is_hidden:
      return

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


class SleepyGuard:

  def __init__(self, x, y, graph):
    self.x = x
    self.y = y
    self.speed = 1.6
    self.radius = 18
    self.graph = graph

    self.direction = "Down"
    self.frame_index = 0
    self.animation_speed = 0.05

    self.view_dist = 110
    self.fov = math.radians(35)
    self.angle = 0

    self.current_path = []
    self.target_x = x
    self.target_y = y
    self.is_investigating = False
    self.investigate_timer = 0

    self.set_random_patrol_path()
    self.animations = self.load_animations(
        size=(50, 50), folder_name="Sleepy Guard"
    )

  def load_animations(self, size, folder_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_bases = [
        os.path.join(script_dir, "chars", folder_name),
        os.path.join(script_dir, folder_name),
        os.path.join(script_dir, "codebase", "chars", folder_name),
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

  def find_nearest_node(self):
    return min(
        self.graph.keys(),
        key=lambda n: math.hypot(
            self.graph[n]["pos"][0] - self.x, self.graph[n]["pos"][1] - self.y
        ),
    )

  def bfs_path(self, start_node, target_node):
    queue = collections.deque([[start_node]])
    visited = {start_node}
    while queue:
      path = queue.popleft()
      node = path[-1]
      if node == target_node:
        return path
      for neighbor in self.graph[node]["neighbors"]:
        if neighbor not in visited:
          visited.add(neighbor)
          new_path = list(path)
          new_path.append(neighbor)
          queue.append(new_path)
    return [start_node]

  def set_random_patrol_path(self):
    nodes = list(self.graph.keys())
    start = self.find_nearest_node()
    target = random.choice(nodes)
    while target == start and len(nodes) > 1:
      target = random.choice(nodes)

    node_path = self.bfs_path(start, target)
    self.current_path = [self.graph[n]["pos"] for n in node_path]
    if self.current_path:
      self.target_x, self.target_y = self.current_path.pop(0)

  def investigate_camera(self, cam_x, cam_y):
    if (
        self.is_investigating
        and math.hypot(self.target_x - cam_x, self.target_y - cam_y) < 50
    ):
      return

    self.is_investigating = True
    self.investigate_timer = 300

    start_node = self.find_nearest_node()
    target_node = min(
        self.graph.keys(),
        key=lambda n: math.hypot(
            self.graph[n]["pos"][0] - cam_x, self.graph[n]["pos"][1] - cam_y
        ),
    )

    node_path = self.bfs_path(start_node, target_node)
    self.current_path = [self.graph[n]["pos"] for n in node_path]
    self.current_path.append((cam_x, cam_y))

    if self.current_path:
      self.target_x, self.target_y = self.current_path.pop(0)

  def update(self, player_x, player_y):
    if self.is_investigating:
      self.investigate_timer -= 1
      if self.investigate_timer <= 0:
        self.is_investigating = False

    dist = math.hypot(self.target_x - self.x, self.target_y - self.y)
    if dist < 12:
      if self.current_path:
        self.target_x, self.target_y = self.current_path.pop(0)
      elif not self.is_investigating:
        self.set_random_patrol_path()

    angle = math.atan2(self.target_y - self.y, self.target_x - self.x)
    self.angle = angle

    dx = math.cos(angle) * self.speed
    dy = math.sin(angle) * self.speed

    if abs(dx) > abs(dy):
      self.direction = "Right" if dx > 0 else "Left"
    else:
      self.direction = "Down" if dy > 0 else "Up"

    self.x += dx
    self.y += dy

    active_frames = self.animations.get(self.direction, [])
    if active_frames:
      self.frame_index += self.animation_speed
      if self.frame_index >= len(active_frames):
        self.frame_index = 0

  def get_rect(self):
    return pygame.Rect(
        self.x - self.radius,
        self.y - self.radius,
        self.radius * 2,
        self.radius * 2,
    )

  def detects_player(self, player):
    if player.is_hidden:
      return False

    px, py = player.x, player.y
    dist = math.hypot(px - self.x, py - self.y)
    if dist > self.view_dist:
      return False

    angle_to_player = math.atan2(py - self.y, px - self.x)
    diff = (angle_to_player - self.angle + math.pi) % (2 * math.pi) - math.pi
    return abs(diff) <= (self.fov / 2)

  def draw(self, surface, camera_x, camera_y):
    screen_x = int(self.x - camera_x)
    screen_y = int(self.y - camera_y)

    left_angle = self.angle - (self.fov / 2)
    right_angle = self.angle + (self.fov / 2)

    p1 = (screen_x, screen_y)
    p2 = (
        screen_x + math.cos(left_angle) * self.view_dist,
        screen_y + math.sin(left_angle) * self.view_dist,
    )
    p3 = (
        screen_x + math.cos(right_angle) * self.view_dist,
        screen_y + math.sin(right_angle) * self.view_dist,
    )

    cone_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(cone_surface, (100, 100, 255, 50), [p1, p2, p3])
    surface.blit(cone_surface, (0, 0))

    active_frames = self.animations.get(self.direction, [])
    if active_frames and int(self.frame_index) < len(active_frames):
      img = active_frames[int(self.frame_index)]
      rect = img.get_rect(center=(screen_x, screen_y))
      surface.blit(img, rect.topleft)
    else:
      pygame.draw.circle(
          surface, (100, 100, 200), (screen_x, screen_y), self.radius
      )
      pygame.draw.circle(surface, (255, 255, 255), (screen_x, screen_y), 4)


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
    if player.is_hidden:
      return False

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

    if not (
        -self.view_dist <= screen_x <= WIDTH + self.view_dist
        and -self.view_dist <= screen_y <= HEIGHT + self.view_dist
    ):
      return

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


def draw_floating_prompt(surface, text, x, y, font):
  txt_surf = font.render(text, True, (255, 204, 0))
  bg_rect = txt_surf.get_rect(center=(x, y))

  padding_surf = pygame.Surface(
      (bg_rect.width + 12, bg_rect.height + 6), pygame.SRCALPHA
  )
  padding_surf.fill((10, 10, 15, 200))
  pygame.draw.rect(padding_surf, (255, 204, 0), padding_surf.get_rect(), 1)

  surface.blit(padding_surf, (bg_rect.x - 6, bg_rect.y - 3))
  surface.blit(txt_surf, bg_rect)


def r_rect(ox, oy, w, h, rx, ry, rw, rh):
  return pygame.Rect(
      ox + int(rx * w), oy + int(ry * h), int(rw * w), int(rh * h)
  )


def load_font(filename, size):
  script_dir = os.path.dirname(os.path.abspath(__file__))
  possible_paths = [
      os.path.join(script_dir, "assets", "fonts", filename),
      os.path.join(script_dir, "fonts", filename),
      os.path.join(script_dir, filename),
  ]
  for path in possible_paths:
    if os.path.exists(path):
      try:
        return pygame.font.Font(path, size)
      except pygame.error:
        pass
  return pygame.font.SysFont("Courier", size, bold=True)


def load_sound(filenames):
  script_dir = os.path.dirname(os.path.abspath(__file__))
  search_subdirs = [
      "",
      "assets",
      os.path.join("assets", "audio"),
      os.path.join("assets", "audio", "sfx"),
  ]

  for sub in search_subdirs:
    for filename in filenames:
      full_path = os.path.join(script_dir, sub, filename)
      if os.path.exists(full_path):
        try:
          return pygame.mixer.Sound(full_path)
        except pygame.error:
          pass
  return None


def load_image_optional(filenames, target_w, target_h):
  script_dir = os.path.dirname(os.path.abspath(__file__))
  search_subdirs = ["", "codebase", "assets", os.path.join("assets", "images")]

  for sub in search_subdirs:
    for filename in filenames:
      full_path = os.path.join(script_dir, sub, filename)
      if os.path.exists(full_path):
        try:
          img = pygame.image.load(full_path).convert_alpha()
          return pygame.transform.scale(img, (target_w, target_h))
        except pygame.error:
          pass
  return None


def load_image(filenames, target_w, target_h):
  img = load_image_optional(filenames, target_w, target_h)
  if img:
    return img
  print(f"Could not find image assets {filenames}")
  sys.exit()


def draw_heart_hud(surface, hearts, full_img, no_img):
  start_x = 20
  start_y = 20
  spacing = 40
  for i in range(3):
    x = start_x + (i * spacing)
    y = start_y
    if i < hearts:
      if full_img:
        surface.blit(full_img, (x, y))
      else:
        pygame.draw.circle(surface, (255, 50, 50), (x + 16, y + 16), 14)
    else:
      if no_img:
        surface.blit(no_img, (x, y))
      else:
        pygame.draw.circle(surface, (80, 80, 80), (x + 16, y + 16), 14, 2)


def main():
  screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
  pygame.display.set_caption("ONE NIGHT BEFORE: The Ultimate VIT Campus Heist")
  clock = pygame.time.Clock()

  ui = FrontendUI(WIDTH, HEIGHT)
  current_state = STATE_MENU
  is_paused = False

  pixel_font = load_font("pixel_bod.ttf", 36)
  small_pixel_font = load_font("pixel_bod.ttf", 16)
  select_sound = load_sound(["select.wav", "click.wav"])
  cctv_sound = load_sound(["cctv_guard.wav"])

  full_heart_img = load_image_optional(
      ["full_heart.png", "full_heart.jpeg", "full_heart.jpg"], 32, 32
  )
  no_heart_img = load_image_optional(
      ["no_heart.png", "no_heart.jpeg", "no_heart.jpg"], 32, 32
  )

  last_cctv_sound_time = 0
  CCTV_SOUND_DELAY_MS = 1000

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

  HALLWAY_GRAPH = {
      "node_1": {
          "pos": (
              HALLWAY_OFFSET_X + int(HALLWAY_W * 0.2),
              HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.2),
          ),
          "neighbors": ["node_2", "node_4"],
      },
      "node_2": {
          "pos": (
              HALLWAY_OFFSET_X + int(HALLWAY_W * 0.5),
              HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.2),
          ),
          "neighbors": ["node_1", "node_3", "node_5"],
      },
      "node_3": {
          "pos": (
              HALLWAY_OFFSET_X + int(HALLWAY_W * 0.8),
              HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.2),
          ),
          "neighbors": ["node_2", "node_6"],
      },
      "node_4": {
          "pos": (
              HALLWAY_OFFSET_X + int(HALLWAY_W * 0.2),
              HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.5),
          ),
          "neighbors": ["node_1", "node_5", "node_7"],
      },
      "node_5": {
          "pos": (
              HALLWAY_OFFSET_X + int(HALLWAY_W * 0.5),
              HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.5),
          ),
          "neighbors": ["node_2", "node_4", "node_6", "node_8"],
      },
      "node_6": {
          "pos": (
              HALLWAY_OFFSET_X + int(HALLWAY_W * 0.8),
              HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.5),
          ),
          "neighbors": ["node_3", "node_5", "node_9"],
      },
      "node_7": {
          "pos": (
              HALLWAY_OFFSET_X + int(HALLWAY_W * 0.2),
              HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.8),
          ),
          "neighbors": ["node_4", "node_8"],
      },
      "node_8": {
          "pos": (
              HALLWAY_OFFSET_X + int(HALLWAY_W * 0.5),
              HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.8),
          ),
          "neighbors": ["node_5", "node_7", "node_9"],
      },
      "node_9": {
          "pos": (
              HALLWAY_OFFSET_X + int(HALLWAY_W * 0.8),
              HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.8),
          ),
          "neighbors": ["node_6", "node_8"],
      },
  }

  INITIAL_ROOM_SPAWN_X = ROOM_OFFSET_X + 850
  INITIAL_ROOM_SPAWN_Y = ROOM_OFFSET_Y + 230

  ROOM_DOOR_SPAWN_X = ROOM_OFFSET_X + 490
  ROOM_DOOR_SPAWN_Y = ROOM_OFFSET_Y + 700

  HALLWAY_SPAWN_X = HALLWAY_OFFSET_X + int(HALLWAY_W * 0.150)
  HALLWAY_SPAWN_Y = HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.185)

  player = Player(INITIAL_ROOM_SPAWN_X, INITIAL_ROOM_SPAWN_Y)
  in_hallway = False

  # Fade-to-black transition variables
  is_catching = False
  fade_alpha = 0
  fade_state = "NONE"  # "OUT", "HOLD", "IN"
  hold_timer = 0

  fog_overlay = create_fog_of_war_vignette(view_radius=340)

  cupboards = [
      {
          "rect": pygame.Rect(
              ROOM_OFFSET_X + 81, ROOM_OFFSET_Y + 47, 85, 200
          ),
          "name": "Top-Left Cupboard",
      },
      {
          "rect": pygame.Rect(
              ROOM_OFFSET_X + 588, ROOM_OFFSET_Y + 46, 85, 200
          ),
          "name": "Top-Right Cupboard",
      },
      {
          "rect": pygame.Rect(
              ROOM_OFFSET_X + -7, ROOM_OFFSET_Y + 507, 85, 250
          ),
          "name": "Bottom-Left Cupboard",
      },
      {
          "rect": pygame.Rect(
              ROOM_OFFSET_X + 931, ROOM_OFFSET_Y + 510, 85, 250
          ),
          "name": "Bottom-Right Cupboard",
      },
  ]
  active_cupboard = None

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

  sleepy_guards = [
      SleepyGuard(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.400),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.400),
          HALLWAY_GRAPH,
      ),
      SleepyGuard(
          HALLWAY_OFFSET_X + int(HALLWAY_W * 0.700),
          HALLWAY_OFFSET_Y + int(HALLWAY_H * 0.700),
          HALLWAY_GRAPH,
      ),
  ]

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

  while True:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()

      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          if current_state == STATE_GAMEPLAY:
            if is_paused:
              is_paused = False
            else:
              current_state = STATE_MENU
              is_paused = False
          else:
            pygame.quit()
            sys.exit()

        elif current_state == STATE_MENU and event.key == pygame.K_RETURN:
          if select_sound:
            select_sound.play()
          current_state = STATE_PROLOGUE

        elif current_state == STATE_PROLOGUE and event.key == pygame.K_SPACE:
          if select_sound:
            select_sound.play()
          current_state = STATE_GAMEPLAY

        elif current_state == STATE_GAMEPLAY and event.key == pygame.K_r:
          player.x, player.y = INITIAL_ROOM_SPAWN_X, INITIAL_ROOM_SPAWN_Y
          player.direction = "Down"
          in_hallway = False
          player.set_level_state(in_hallway)
          is_paused = False

        elif current_state == STATE_GAMEPLAY and event.key == pygame.K_p:
          is_paused = not is_paused

        elif (
            current_state == STATE_GAMEPLAY
            and not is_paused
            and event.key == pygame.K_e
        ):
          if not in_hallway:
            if player.is_hidden:
              player.is_hidden = False
              if active_cupboard:
                name = active_cupboard["name"]
                c_rect = active_cupboard["rect"]
                if "Top-Left" in name or "Top-Right" in name:
                  player.x = c_rect.centerx
                  player.y = c_rect.bottom + 30
                elif "Bottom-Left" in name:
                  player.x = c_rect.centerx
                  player.y = c_rect.top - 30
                elif "Bottom-Right" in name:
                  player.x = c_rect.left - 30
                  player.y = c_rect.centery
              active_cupboard = None
              if select_sound:
                select_sound.play()
            else:
              p_rect = player.get_rect()
              for cup in cupboards:
                if p_rect.colliderect(cup["rect"].inflate(40, 40)):
                  player.is_hidden = True
                  active_cupboard = cup
                  player.x = cup["rect"].centerx
                  player.y = cup["rect"].centery
                  if select_sound:
                    select_sound.play()
                  break

    if current_state == STATE_MENU:
      ui.draw_main_menu(screen)
    elif current_state == STATE_PROLOGUE:
      ui.draw_prologue(screen)
    elif current_state == STATE_GAMEPLAY:
      screen.fill((5, 5, 5))

      keys = pygame.key.get_pressed()
      player_rect = player.get_rect()

      if not is_paused and fade_state == "NONE":
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
          current_time = pygame.time.get_ticks()

          for cam in cameras:
            cam.update()
            if cam.detects_player(player):
              for s_guard in sleepy_guards:
                s_guard.investigate_camera(cam.x, cam.y)
              if (
                  cctv_sound
                  and (current_time - last_cctv_sound_time)
                  >= CCTV_SOUND_DELAY_MS
              ):
                cctv_sound.play()
                last_cctv_sound_time = current_time

          for s_guard in sleepy_guards:
            s_guard.update(player.x, player.y)
            if s_guard.detects_player(player):
              is_catching = True
              fade_state = "OUT"
              fade_alpha = 0
              if (
                  cctv_sound
                  and (current_time - last_cctv_sound_time)
                  >= CCTV_SOUND_DELAY_MS
              ):
                cctv_sound.play()
                last_cctv_sound_time = current_time
              break

      # Handle Fade-to-Black Transition with Extended Hold
      if fade_state == "OUT":
        fade_alpha += 4
        if fade_alpha >= 255:
          fade_alpha = 255
          player.hearts = max(0, player.hearts - 1)
          in_hallway = False
          player.set_level_state(in_hallway)
          player.x, player.y = INITIAL_ROOM_SPAWN_X, INITIAL_ROOM_SPAWN_Y
          player.direction = "Down"
          if player.hearts <= 0:
            player.hearts = 3
          hold_timer = 90  # Extended black screen hold duration
          fade_state = "HOLD"
      elif fade_state == "HOLD":
        hold_timer -= 1
        if hold_timer <= 0:
          fade_state = "IN"
      elif fade_state == "IN":
        fade_alpha -= 4
        if fade_alpha <= 0:
          fade_alpha = 0
          fade_state = "NONE"

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
        player.draw(screen, camera_x, camera_y)

        if not is_paused and fade_state == "NONE":
          if player.is_hidden and active_cupboard:
            draw_floating_prompt(
                screen,
                "[E] Exit Cupboard",
                active_cupboard["rect"].centerx,
                active_cupboard["rect"].top - 20,
                small_pixel_font,
            )
          else:
            p_rect = player.get_rect()
            for cup in cupboards:
              if p_rect.colliderect(cup["rect"].inflate(40, 40)):
                draw_floating_prompt(
                    screen,
                    "[E] Hide in Cupboard",
                    cup["rect"].centerx,
                    cup["rect"].top - 20,
                    small_pixel_font,
                )
                break
      else:
        screen.blit(
            hallway_img,
            (HALLWAY_OFFSET_X - camera_x, HALLWAY_OFFSET_Y - camera_y),
        )
        draw_gold_indicator(screen, hallway_room_door, camera_x, camera_y)

        for cam in cameras:
          cam.draw(screen, camera_x, camera_y)

        for s_guard in sleepy_guards:
          s_guard.draw(screen, camera_x, camera_y)

        player.draw(screen, camera_x, camera_y)
        screen.blit(fog_overlay, (0, 0))

      draw_heart_hud(screen, player.hearts, full_heart_img, no_heart_img)

      if fade_alpha > 0:
        fade_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fade_surf.fill((0, 0, 0, fade_alpha))
        screen.blit(fade_surf, (0, 0))

        # "CAUGHT!" text vanishes slightly early before fade-in starts
        if fade_alpha > 150 and (
            fade_state == "OUT"
            or (fade_state == "HOLD" and hold_timer > 30)
        ):
          caught_surf = pixel_font.render("CAUGHT!", True, (255, 30, 30))
          caught_rect = caught_surf.get_rect(
              center=(WIDTH // 2, HEIGHT // 2)
          )
          screen.blit(caught_surf, caught_rect)

      if is_paused:
        pause_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pause_overlay.fill((0, 0, 0, 160))
        screen.blit(pause_overlay, (0, 0))

        bar_w, bar_h, gap = 20, 80, 20
        cx, cy = WIDTH // 2, HEIGHT // 2
        pygame.draw.rect(
            screen,
            (240, 240, 240),
            pygame.Rect(cx - bar_w - gap // 2, cy - bar_h // 2, bar_w, bar_h),
        )
        pygame.draw.rect(
            screen,
            (240, 240, 240),
            pygame.Rect(cx + gap // 2, cy - bar_h // 2, bar_w, bar_h),
        )

    pygame.display.flip()
    clock.tick(FPS)


if __name__ == "__main__":
  main()