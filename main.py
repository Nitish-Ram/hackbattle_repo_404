import math
import sys
import pygame

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60


class Player:

  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.radius = 10
    self.speed = 3  # Player is faster

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

  def check_collision(self, walls):
    rect = pygame.Rect(
        self.x - self.radius,
        self.y - self.radius,
        self.radius * 2,
        self.radius * 2,
    )
    return any(rect.colliderect(w) for w in walls)

  def draw(self, surface):
    pygame.draw.circle(
        surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius
    )


class Guard:

  def __init__(self, x, y, guard_type="normal"):
    self.x = x
    self.y = y
    self.guard_type = guard_type
    self.speed = 1.5  # Slower than player

    self.base_angle = 0.0
    self.angle = 0.0
    self.state = "PATROL"

    # Configure stats based on type
    if guard_type == "professor":
      self.fov_radius = 200
      self.fov_angle = math.radians(90)
    elif guard_type == "sleepy":
      self.fov_radius = 90
      self.fov_angle = math.radians(45)
      self.speed = 1.0  # Even slower
    else:  # normal guard
      self.fov_radius = 130
      self.fov_angle = math.radians(60)

  def update(self, player, walls):
    target_angle = math.atan2(player.y - self.y, player.x - self.x)
    dist = math.hypot(player.x - self.x, player.y - self.y)

    in_fov = False
    if dist < self.fov_radius:
      diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
      if abs(diff) <= self.fov_angle / 2:
        if not self.check_raycast(player.x, player.y, walls):
          in_fov = True

    if in_fov:
      self.state = "CHASE"
    elif self.state == "CHASE" and dist > self.fov_radius * 1.5:
      # Lose player if they get far enough away
      self.state = "PATROL"

    if self.state == "CHASE":
      # Follow the player slowly
      self.angle = target_angle
      if dist > 15:  # Stop right on top of player
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
    else:
      # Patrol: Look side to side smoothly using sine wave oscillation
      scan_offset = math.sin(pygame.time.get_ticks() * 0.002) * math.radians(45)
      self.angle = self.base_angle + scan_offset

  def check_raycast(self, tx, ty, walls):
    for i in range(1, 10):
      cx = self.x + (tx - self.x) * (i / 10)
      cy = self.y + (ty - self.y) * (i / 10)
      if any(w.collidepoint(cx, cy) for w in walls):
        return True
    return False

  def draw(self, surface):
    p1 = (self.x, self.y)
    p2 = (
        self.x + math.cos(self.angle - self.fov_angle / 2) * self.fov_radius,
        self.y + math.sin(self.angle - self.fov_angle / 2) * self.fov_radius,
    )
    p3 = (
        self.x + math.cos(self.angle + self.fov_angle / 2) * self.fov_radius,
        self.y + math.sin(self.angle + self.fov_angle / 2) * self.fov_radius,
    )

    # Color coding per guard type
    if self.guard_type == "professor":
      color = (255, 100, 100)
    elif self.guard_type == "sleepy":
      color = (150, 150, 255)
    else:
      color = (100, 200, 255)

    # Highlight cone red if chasing
    if self.state == "CHASE":
      color = (255, 50, 50)

    pygame.draw.polygon(surface, (*color, 40), [p1, p2, p3])
    pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 10)


def main():
  screen = pygame.display.set_mode((WIDTH, HEIGHT))
  clock = pygame.time.Clock()

  player = Player(100, 100)
  guards = [
      Guard(300, 200, guard_type="sleepy"),
      Guard(500, 300, guard_type="normal"),
      Guard(600, 150, guard_type="professor"),
  ]
  walls = [
      pygame.Rect(200, 150, 300, 30),
      pygame.Rect(200, 350, 30, 200),
      pygame.Rect(450, 400, 200, 30),
  ]

  while True:
    screen.fill((20, 20, 20))

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()

    keys = pygame.key.get_pressed()
    player.move(keys, walls)

    for g in guards:
      g.update(player, walls)

    for w in walls:
      pygame.draw.rect(screen, (80, 80, 80), w)

    player.draw(screen)
    for g in guards:
      g.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)


if __name__ == "__main__":
  main()