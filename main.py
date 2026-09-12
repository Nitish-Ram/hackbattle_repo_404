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
    self.radius = 16
    self.speed = 7

  def move(self, keys, walls):
    dx, dy = 0, 0
    if keys[pygame.K_w]:
      dy -= self.speed
    if keys[pygame.K_s]:
      dy += self.speed
    if keys[pygame.K_a]:
      dx -= self.speed
    if keys[pygame.K_d]:
      dx += self.speed

    self.x += dx
    if self.check_collision(walls):
      self.x -= dx

    self.y += dy
    if self.check_collision(walls):
      self.y -= dy

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
    pygame.draw.circle(surface, (255, 0, 0), (pos_x, pos_y), self.radius + 3)
    pygame.draw.circle(surface, (255, 255, 255), (pos_x, pos_y), self.radius)


class SecurityCamera:

  def __init__(
      self,
      x,
      y,
      base_angle_deg,
      sweep_range_deg=90,
      sweep_speed=0.02,
      view_dist=400,
      fov_deg=50,
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

  def draw(self, surface, camera_x, camera_y):
    screen_x = self.x - camera_x
    screen_y = self.y - camera_y

    left_angle = self.current_angle - (self.fov / 2)
    right_angle = self.current_angle + (self.fov / 2)

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
    pygame.draw.polygon(cone_surface, (255, 0, 0, 70), [p1, p2, p3])
    pygame.draw.line(cone_surface, (255, 50, 50, 180), p1, p2, 2)
    pygame.draw.line(cone_surface, (255, 50, 50, 180), p1, p3, 2)
    surface.blit(cone_surface, (0, 0))

    pygame.draw.circle(
        surface, (30, 30, 30), (int(screen_x), int(screen_y)), 12
    )
    pygame.draw.circle(
        surface, (220, 20, 20), (int(screen_x), int(screen_y)), 6
    )


def load_room_image(target_w, target_h):
  script_dir = os.path.dirname(os.path.abspath(__file__))
  possible_filenames = ["room_plan.jpeg", "room_plan.jpg", "room_plan.png"]

  for filename in possible_filenames:
    full_path = os.path.join(script_dir, filename)
    if os.path.exists(full_path):
      try:
        img = pygame.image.load(full_path).convert()
        return pygame.transform.scale(img, (target_w, target_h))
      except pygame.error as e:
        print(f"Error loading image '{full_path}': {e}")
        sys.exit()

  print(f"Could not find room image in: {script_dir}")
  sys.exit()


def main():
  screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
  pygame.display.set_caption("Top-Down Office Stealth")
  clock = pygame.time.Clock()

  IMG_W, IMG_H = 1000, 850
  room_img = load_room_image(IMG_W, IMG_H)

  ROOM_OFFSET_X = 500
  ROOM_OFFSET_Y = 0

  # Guaranteed open space spawn point in central corridor
  SPAWN_X = ROOM_OFFSET_X + 370
  SPAWN_Y = ROOM_OFFSET_Y + 450

  player = Player(SPAWN_X, SPAWN_Y)
  in_hallway = False

  # --- TUNED ROOM BOUNDARIES ---
  room_walls = [
      pygame.Rect(ROOM_OFFSET_X + 181, ROOM_OFFSET_Y + 28, 720, 20),
      pygame.Rect(ROOM_OFFSET_X + 1, ROOM_OFFSET_Y + 0, 10, 848),
      pygame.Rect(ROOM_OFFSET_X + 967, ROOM_OFFSET_Y + 0, 32, 850),
      pygame.Rect(ROOM_OFFSET_X + 11, ROOM_OFFSET_Y + 826, 318, 22),
      pygame.Rect(ROOM_OFFSET_X + 492, ROOM_OFFSET_Y + 822, 475, 26),
  ]

  # --- TUNED FURNITURE BARRIERS ---
  furniture_barriers = [
      pygame.Rect(ROOM_OFFSET_X + 119, ROOM_OFFSET_Y + 85, 195, 266),
      pygame.Rect(ROOM_OFFSET_X + 315, ROOM_OFFSET_Y + 69, 240, 220),
      pygame.Rect(ROOM_OFFSET_X + 558, ROOM_OFFSET_Y + 35, 406, 127),
      pygame.Rect(ROOM_OFFSET_X + 407, ROOM_OFFSET_Y + 354, 559, 169),
      pygame.Rect(ROOM_OFFSET_X + 12, ROOM_OFFSET_Y + 380, 317, 145),
      pygame.Rect(ROOM_OFFSET_X + 495, ROOM_OFFSET_Y + 550, 380, 135),
  ]

  # Exit Door Trigger (Bottom wall gap)
  room_exit_door = pygame.Rect(
      ROOM_OFFSET_X + 329, ROOM_OFFSET_Y + 824, 163, 24
  )

  # Campus Level Setup
  FLOOR_X, FLOOR_Y = -600, 2000
  FLOOR_W, FLOOR_H = 3000, 2000

  campus_walls = [
      pygame.Rect(FLOOR_X, FLOOR_Y, FLOOR_W, 30),
      pygame.Rect(FLOOR_X, FLOOR_Y + FLOOR_H - 30, FLOOR_W, 30),
      pygame.Rect(FLOOR_X, FLOOR_Y, 30, FLOOR_H),
      pygame.Rect(FLOOR_X + FLOOR_W - 30, FLOOR_Y, 30, FLOOR_H),
  ]

  hallway_room_door = pygame.Rect(FLOOR_X + 1400, FLOOR_Y, 180, 35)

  cameras = [
      SecurityCamera(FLOOR_X + 150, FLOOR_Y + 150, base_angle_deg=45),
      SecurityCamera(
          FLOOR_X + FLOOR_W - 150, FLOOR_Y + 150, base_angle_deg=135
      ),
      SecurityCamera(
          FLOOR_X + 800, FLOOR_Y + 1100, base_angle_deg=270, sweep_range_deg=120
      ),
      SecurityCamera(
          FLOOR_X + FLOOR_W - 600, FLOOR_Y + 1500, base_angle_deg=180
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
      in_hallway = False

    player_rect = player.get_rect()

    # Teleportation
    if not in_hallway and player_rect.colliderect(room_exit_door):
      in_hallway = True
      player.x, player.y = FLOOR_X + 1490, FLOOR_Y + 100
    elif in_hallway and player_rect.colliderect(hallway_room_door):
      in_hallway = False
      player.x, player.y = SPAWN_X, SPAWN_Y

    active_walls = (
        campus_walls if in_hallway else room_walls + furniture_barriers
    )
    player.move(keys, active_walls)

    if in_hallway:
      for cam in cameras:
        cam.update()

    camera_x = player.x - WIDTH // 2
    camera_y = player.y - HEIGHT // 2

    # Render Stack
    if not in_hallway:
      screen.blit(
          room_img, (ROOM_OFFSET_X - camera_x, ROOM_OFFSET_Y - camera_y)
      )

      # Orange Door Trigger
      pygame.draw.rect(
          screen,
          (255, 165, 0),
          pygame.Rect(
              room_exit_door.x - camera_x,
              room_exit_door.y - camera_y,
              room_exit_door.width,
              room_exit_door.height,
          ),
      )

      if DEBUG_COLLISIONS:
        for w in room_walls + furniture_barriers:
          pygame.draw.rect(
              screen,
              (255, 0, 0),
              pygame.Rect(w.x - camera_x, w.y - camera_y, w.width, w.height),
              2,
          )

    else:
      pygame.draw.rect(
          screen,
          (25, 25, 28),
          pygame.Rect(
              FLOOR_X - camera_x, FLOOR_Y - camera_y, FLOOR_W, FLOOR_H
          ),
      )

      for w in campus_walls:
        pygame.draw.rect(
            screen,
            (80, 80, 85),
            pygame.Rect(w.x - camera_x, w.y - camera_y, w.width, w.height),
        )

      pygame.draw.rect(
          screen,
          (255, 165, 0),
          pygame.Rect(
              hallway_room_door.x - camera_x,
              hallway_room_door.y - camera_y,
              hallway_room_door.width,
              hallway_room_door.height,
          ),
      )

      if DEBUG_COLLISIONS:
        for w in campus_walls:
          pygame.draw.rect(
              screen,
              (255, 0, 0),
              pygame.Rect(w.x - camera_x, w.y - camera_y, w.width, w.height),
              2,
          )

      for cam in cameras:
        cam.draw(screen, camera_x, camera_y)

    player.draw(screen, camera_x, camera_y)

    pygame.display.flip()
    clock.tick(FPS)


if __name__ == "__main__":
  main()