import math
import random

import pygame

SIZE = 520


pygame.mixer.init()
pygame.init()
window = pygame.display.set_mode((SIZE, SIZE))

# audio assets
wing_sound = pygame.mixer.Sound("assets/sounds/wing.wav")
hit_sound = pygame.mixer.Sound("assets/sounds/hit.wav")
die_sound = pygame.mixer.Sound("assets/sounds/die.wav")
point_sound = pygame.mixer.Sound("assets/sounds/point.wav")
swoosh_sound = pygame.mixer.Sound("assets/sounds/swoosh.wav")

for s in [wing_sound, hit_sound, die_sound, point_sound, swoosh_sound]:
    s.set_volume(0.5)

# Game Assets
bg = pygame.transform.scale(
    pygame.image.load("assets/Objects/bg.png").convert_alpha(), (SIZE, SIZE)
)
base = pygame.image.load("assets/Objects/base.png").convert()
pipe_img = pygame.image.load("assets/Objects/pipe.png").convert_alpha()

# base and background scrolling logic
base_tiles = math.ceil(SIZE / base.get_width()) + 2
base_scroll = 0

bg_tiles = math.ceil(SIZE / bg.get_width()) + 2
bg_scroll = 0


# bird frames
bird_frames = [
    pygame.image.load("assets/Objects/downflap.png").convert_alpha(),
    pygame.image.load("assets/Objects/midflap.png").convert_alpha(),
    pygame.image.load("assets/Objects/upflap.png").convert_alpha(),
]
bird_frames = [pygame.transform.scale(frame, (40, 30)) for frame in bird_frames]

# socres assets
numbers_img = []

for i in range(10):
    img = pygame.image.load(f"assets/UI/Numbers/{i}.png").convert_alpha()
    numbers_img.append(img)

gameover_img = pygame.image.load("assets/UI/gameover.png").convert_alpha()
gameover_rect = gameover_img.get_rect(center=(SIZE // 2, SIZE // 2 - 40))

message_img = pygame.transform.scale(
    pygame.image.load("assets/UI/message.png"), (SIZE, SIZE)
)
message_rect = message_img.get_rect(center=(SIZE // 2, SIZE // 2))


def draw_score(score):
    score_str = str(score)

    total_width = 0
    for digit in score_str:
        total_width += numbers_img[int(digit)].get_width()
    x = (SIZE - total_width) // 2
    y = 80

    for digit in score_str:
        img = numbers_img[int(digit)]
        window.blit(img, (x, y))
        x += img.get_width()


def scrolling_bg():
    global bg_scroll
    for i in range(0, bg_tiles):
        window.blit(bg, (i * bg.get_width() + bg_scroll, 0))
    bg_scroll -= 3
    if abs(bg_scroll) > bg.get_width():
        bg_scroll = 0


def scrolling_base():
    global base_scroll
    for i in range(0, base_tiles):
        window.blit(
            base, (i * base.get_width() + base_scroll, SIZE - base.get_height())
        )
    base_scroll -= 5
    if abs(base_scroll) > base.get_width():
        base_scroll = 0


# pipe creating logic


gap = 150
speed = 4
SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, 1500)


def create_pipes():
    min_height = 50
    max_height = SIZE - gap - base.get_height() - 50
    top_height = random.randint(min_height, max_height)
    bottom_height = SIZE - top_height - gap - base.get_height()
    top_pipe = pygame.transform.scale(pipe_img, (pipe_img.get_width(), top_height))
    bottom_pipe = pygame.transform.scale(
        pipe_img, (pipe_img.get_width(), bottom_height)
    )
    top_pipe = pygame.transform.flip(top_pipe, False, True)
    top_rect = top_pipe.get_rect(midbottom=(SIZE + 50, top_height))
    bottom_rect = bottom_pipe.get_rect(midtop=(SIZE + 50, top_height + gap))

    # masks
    top_mask = pygame.mask.from_surface(top_pipe)
    bottom_mask = pygame.mask.from_surface(bottom_pipe)

    return {
        "top_surface": top_pipe,
        "top_rect": top_rect,
        "top_mask": top_mask,
        "bottom_surface": bottom_pipe,
        "bottom_rect": bottom_rect,
        "bottom_mask": bottom_mask,
        "scored": False,
    }


def check_collision(pipes, bird_mask, rotated_rect):
    for pipe in pipes:
        top_offset = (
            pipe["top_rect"].x - rotated_rect.x,
            pipe["top_rect"].y - rotated_rect.y,
        )
        bottom_offset = (
            pipe["bottom_rect"].x - rotated_rect.x,
            pipe["bottom_rect"].y - rotated_rect.y,
        )

        if bird_mask.overlap(pipe["top_mask"], top_offset):
            return False
        if bird_mask.overlap(pipe["bottom_mask"], bottom_offset):
            return False
    if rotated_rect.bottom >= SIZE - base.get_height():
        return False
    if rotated_rect.top <= 0:
        return False

    return True


BIRDFLAP = pygame.USEREVENT + 1
pygame.time.set_timer(BIRDFLAP, 200)


def main():
    index = 0
    surface = bird_frames[index]
    bird_rect = surface.get_rect(center=(100, SIZE // 2))
    gravity = 1200
    strength = -400
    bird_velocity = 0
    score = 0
    game_state = "start"

    pygame.display.set_caption("Flappy Bird")
    clock = pygame.time.Clock()
    run = True
    pipes = []

    while run:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == SPAWNPIPE and game_state == "playing":
                pipes.append(create_pipes())
            if event.type == BIRDFLAP:
                index += 1
                if index >= len(bird_frames):
                    index = 0
                surface = bird_frames[index]
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_state == "start":
                        game_state = "playing"
                        bird_velocity = strength
                    if game_state == "playing":
                        bird_velocity = strength
                        wing_sound.play()
                    elif game_state == "game_over":
                        pipes.clear()
                        bird_rect.center = (100, SIZE // 2)
                        bird_velocity = 0
                        score = 0
                        game_state = "playing"

        if game_state == "playing":
            bird_velocity += gravity * dt
            bird_rect.y += bird_velocity * dt

            for pipe in pipes:
                pipe["top_rect"].x -= speed
                pipe["bottom_rect"].x -= speed
            pipes = [p for p in pipes if p["top_rect"].x > -pipe_img.get_width()]
        if game_state == "playing":
            for pipe in pipes:
                if pipe["top_rect"].centerx < bird_rect.centerx and not pipe["scored"]:
                    score += 1
                    pipe["scored"] = True

        scrolling_bg()
        scrolling_base()
        if game_state == "start":
            window.blit(message_img, message_rect)
        for pipe in pipes:
            window.blit(pipe["top_surface"], pipe["top_rect"])
            window.blit(pipe["bottom_surface"], pipe["bottom_rect"])
        angle = -bird_velocity * 0.05
        angle = max(min(angle, 25), -90)
        rotated_bird = pygame.transform.rotate(surface, angle)
        rotated_rect = rotated_bird.get_rect(center=bird_rect.center)
        bird_mask = pygame.mask.from_surface(rotated_bird)
        if game_state == "playing":
            if not check_collision(pipes, bird_mask, rotated_rect):
                game_state = "game_over"
                hit_sound.play()
                die_sound.play()
            window.blit(rotated_bird, rotated_rect)
            draw_score(score)
        if game_state == "game_over":
            window.blit(gameover_img, gameover_rect)
            swoosh_sound.play()

        pygame.display.update()
    pygame.quit()


if __name__ == "__main__":
    main()
