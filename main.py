import button
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 7

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Platformer")

star_img = pygame.image.load("assets/Buttons/start.png").convert_alpha()
exit_img = pygame.image.load("assets/Buttons/exit.png").convert_alpha()

pygame.mixer.music.load("assets/Audio/Peaceful Town Theme.wav")
pygame.mixer.music.set_volume(0.20)
pygame.mixer.music.play(-1, 0.0, 5000)
click = pygame.mixer.Sound("assets/Audio/mixkit-negative-tone-interface-tap-2569.wav")
click.set_volume(0.75)

start_button = button.Button(200, 300, star_img, 0.2, click)
exit_button = button.Button(650, 300, exit_img, 0.2, click)

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 5

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))



class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0,))
        self.mask = pygame.mask.from_surface(self.image)


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for object in objects:
        object.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for object in objects:
        if pygame.sprite.collide_mask(player, object):
            if dy > 0:
                player.rect.bottom = object.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = object.rect.bottom
                player.hit_head()

            collided_objects.append(object)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for object in objects:
        if pygame.sprite.collide_mask(player, object):
            collided_object = object
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for object in to_check:
        if object and object.name == "fire":
            player.make_hit()
            dmg = pygame.mixer.Sound("assets/Audio/hurt_c_08-102842.mp3")
            dmg.play()
            dmg.set_volume(0.25)



def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Brown.png")

    block_size = 96

    player = Player(100, 100, 50, 50)
    fire1 = Fire(950, HEIGHT - block_size - 64, 16, 32)
    fire1.on()
    fire2 = Fire(1750, HEIGHT - block_size * 7 - 64, 16, 32)
    fire2.on()
    fire3 = Fire(1750, HEIGHT - block_size * 3 - 64, 16, 32)
    fire3.on()
    fire4 = Fire(1475, HEIGHT - block_size - 64, 16, 32)
    fire4.on()
    fire5 = Fire(2950, HEIGHT - block_size - 64, 16, 32)
    fire5.on()
    fire6 = Fire(2125, HEIGHT - block_size * 4 - 64, 16, 32)
    fire6.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in
             range(-WIDTH // block_size, WIDTH * 6 // block_size)]
    objects = [*floor, Block(block_size * -11, HEIGHT - block_size * 2, block_size),
               Block(block_size * -11, HEIGHT - block_size * 2, block_size),
               Block(block_size * -11, HEIGHT - block_size * 3, block_size),
               Block(block_size * -11, HEIGHT - block_size * 4, block_size),
               Block(block_size * -11, HEIGHT - block_size * 5, block_size),
               Block(block_size * -11, HEIGHT - block_size * 6, block_size),
               Block(block_size * -11, HEIGHT - block_size * 7, block_size),
               Block(block_size * -8, HEIGHT - block_size * 3, block_size),
               Block(block_size * 0, HEIGHT - block_size * 3, block_size),
               Block(block_size * -4, HEIGHT - block_size * 4, block_size),
               Block(block_size * 5, HEIGHT - block_size * 4, block_size), fire1,
               Block(block_size * 6, HEIGHT - block_size * 4, block_size),
               Block(block_size * 7, HEIGHT - block_size * 4, block_size),
               Block(block_size * 12, HEIGHT - block_size * 0, block_size),
               Block(block_size * 13, HEIGHT - block_size * 0, block_size),
               Block(block_size * 14, HEIGHT - block_size * 0, block_size), fire2,
               Block(block_size * 18, HEIGHT - block_size * 3, block_size),
               Block(block_size * 9, HEIGHT - block_size * 0, block_size),
               Block(block_size * 10, HEIGHT - block_size * 0, block_size),
               Block(block_size * 11, HEIGHT - block_size * 0, block_size),
               Block(block_size * 12, HEIGHT - block_size * 3, block_size), fire3,
               Block(block_size * 13, HEIGHT - block_size * 3, block_size),
               Block(block_size * 14, HEIGHT - block_size * 4, block_size),
               Block(block_size * 15, HEIGHT - block_size * 4, block_size),
               Block(block_size * 16, HEIGHT - block_size * 4, block_size),
               Block(block_size * 17, HEIGHT - block_size * 3, block_size), fire4,
               Block(block_size * 18, HEIGHT - block_size * 7, block_size),
               Block(block_size * 19, HEIGHT - block_size * 5, block_size),
               Block(block_size * 22, HEIGHT - block_size * 4, block_size),
               Block(block_size * 23, HEIGHT - block_size * 4, block_size),
               Block(block_size * 24, HEIGHT - block_size * 3, block_size),
               Block(block_size * 27, HEIGHT - block_size * 4, block_size), fire5,
               Block(block_size * 28, HEIGHT - block_size * 4, block_size),
               Block(block_size * 29, HEIGHT - block_size * 5, block_size),
               Block(block_size * 29, HEIGHT - block_size * 5, block_size),
               Block(block_size * 30, HEIGHT - block_size * 6, block_size),
               Block(block_size * 31, HEIGHT - block_size * 7, block_size),
               Block(block_size * 32, HEIGHT - block_size * 7, block_size),
               Block(block_size * 33, HEIGHT - block_size * 7, block_size),
               Block(block_size * 34, HEIGHT - block_size * 2, block_size),
               Block(block_size * 37, HEIGHT - block_size * 4, block_size), fire6,
               Block(block_size * 38, HEIGHT - block_size * 4, block_size),
               Block(block_size * 39, HEIGHT - block_size * 5, block_size),
               Block(block_size * 40, HEIGHT - block_size * 5, block_size),
               Block(block_size * 43, HEIGHT - block_size * 6, block_size),
               Block(block_size * 44, HEIGHT - block_size * 7, block_size),
               Block(block_size * 47, HEIGHT - block_size * 2, block_size),
               Block(block_size * 49, HEIGHT - block_size * 4, block_size),
               Block(block_size * 50, HEIGHT - block_size * 4, block_size),
               Block(block_size * 51, HEIGHT - block_size * 5, block_size),
               Block(block_size * 52, HEIGHT - block_size * 5, block_size),
               Block(block_size * 56, HEIGHT - block_size * 6, block_size),
               Block(block_size * 61, HEIGHT - block_size * 9, block_size),
               Block(block_size * 61, HEIGHT - block_size * 8, block_size),
               Block(block_size * 61, HEIGHT - block_size * 7, block_size),
               Block(block_size * 61, HEIGHT - block_size * 6, block_size),
               Block(block_size * 61, HEIGHT - block_size * 5, block_size),
               Block(block_size * 61, HEIGHT - block_size * 4, block_size),
               Block(block_size * 61, HEIGHT - block_size * 3, block_size),
               Block(block_size * 61, HEIGHT - block_size * 2, block_size),
               Block(block_size * 61, HEIGHT - block_size * 1, block_size),
               Block(block_size * 61, HEIGHT - block_size * 0, block_size),
               ]

    offset_x = 0
    scroll_area_width = 300

    run = True
    game_started = False

    start_screen_img = pygame.image.load("assets/HomeScreen/Theme1.png")
    start_button.draw(start_screen_img)
    exit_button.draw(start_screen_img)
    pygame.display.update()

    while run:
        window.blit(start_screen_img, (0, 0))
        if game_started:
            window.fill((255, 255, 255))
            player.loop(FPS)
            fire1.loop()
            fire2.loop()
            fire3.loop()
            fire4.loop()
            fire5.loop()
            fire6.loop()
            handle_move(player, objects)
            draw(window, background, bg_image, player, objects, offset_x)

            if (player.rect.right - offset_x >= WIDTH - scroll_area_width and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if not game_started:
                if start_button.draw(window):
                    game_started = True

                if exit_button.draw(window):
                    run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    pygame.mixer.Sound("assets/Audio/fast-simple-chop-5-6270.mp3").play()
                    player.jump()

        pygame.display.update()

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
