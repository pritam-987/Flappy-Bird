import json
import math
import os
import random
import sys

import pygame

SIZE = 520


def resource_path(path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, path)


# Save file should NOT use _MEIPASS
SAVE_PATH = os.path.join(os.getcwd(), "save.json")

pygame.mixer.init()
pygame.init()
window = pygame.display.set_mode((SIZE, SIZE))
pygame.display.set_caption("Flappy Bird")

clock = pygame.time.Clock()


wing_sound = pygame.mixer.Sound(resource_path("assets/sounds/wing.wav"))
hit_sound = pygame.mixer.Sound(resource_path("assets/sounds/hit.wav"))
die_sound = pygame.mixer.Sound(resource_path("assets/sounds/die.wav"))
point_sound = pygame.mixer.Sound(resource_path("assets/sounds/point.wav"))
swoosh_sound = pygame.mixer.Sound(resource_path("assets/sounds/swoosh.wav"))

for s in [wing_sound, hit_sound, die_sound, point_sound, swoosh_sound]:
    s.set_volume(0.5)

bg = pygame.transform.scale(
    pygame.image.load(resource_path("assets/Objects/bg.png")).convert_alpha(),
    (SIZE, SIZE),
)

base = pygame.image.load(resource_path("assets/Objects/base.png")).convert()

pipe_img = pygame.image.load(resource_path("assets/Objects/pipe.png")).convert_alpha()


# Bird Frames
bird_frames = [
    pygame.image.load(resource_path("assets/Objects/downflap.png")).convert_alpha(),
    pygame.image.load(resource_path("assets/Objects/midflap.png")).convert_alpha(),
    pygame.image.load(resource_path("assets/Objects/upflap.png")).convert_alpha(),
]

bird_frames = [pygame.transform.scale(frame, (40, 30)) for frame in bird_frames]


# Numbers
numbers_img = []
for i in range(10):
    img = pygame.image.load(resource_path(f"assets/UI/Numbers/{i}.png")).convert_alpha()
    numbers_img.append(img)


gameover_img = pygame.image.load(
    resource_path("assets/UI/gameover.png")
).convert_alpha()

gameover_rect = gameover_img.get_rect(center=(SIZE // 2, SIZE // 2 - 40))

message_img = pygame.transform.scale(
    pygame.image.load(resource_path("assets/UI/message.png")).convert_alpha(),
    (SIZE, SIZE),
)

message_rect = message_img.get_rect(center=(SIZE // 2, SIZE // 2))


base_tiles = math.ceil(SIZE / base.get_width()) + 2
base_scroll = 0

bg_tiles = math.ceil(SIZE / bg.get_width()) + 2
bg_scroll = 0


def scrolling_bg():
    global bg_scroll
    for i in range(bg_tiles):
        window.blit(bg, (i * bg.get_width() + bg_scroll, 0))
    bg_scroll -= 3
    if abs(bg_scroll) > bg.get_width():
        bg_scroll = 0


def scrolling_base():
    global base_scroll
    for i in range(base_tiles):
        window.blit(
            base,
            (i * base.get_width() + base_scroll, SIZE - base.get_height()),
        )
    base_scroll -= 5
    if abs(base_scroll) > base.get_width():
        base_scroll = 0


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

    return {
        "top_surface": top_pipe,
        "top_rect": top_rect,
        "bottom_surface": bottom_pipe,
        "bottom_rect": bottom_rect,
        "scored": False,
    }


def check_collision(pipes, bird_rect):
    for pipe in pipes:
        if bird_rect.colliderect(pipe["top_rect"]) or bird_rect.colliderect(
            pipe["bottom_rect"]
        ):
            return False

    if bird_rect.bottom >= SIZE - base.get_height():
        return False
    if bird_rect.top <= 0:
        return False

    return True


def load_data():
    if not os.path.exists(SAVE_PATH):
        default = {"high_score": 0}
        with open(SAVE_PATH, "w") as f:
            json.dump(default, f, indent=4)
        return default

    try:
        with open(SAVE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"high_score": 0}


def save_data(data):
    with open(SAVE_PATH, "w") as f:
        json.dump(data, f, indent=4)


def draw_score(score):
    score_str = str(score)
    total_width = sum(numbers_img[int(d)].get_width() for d in score_str)
    x = (SIZE - total_width) // 2
    y = 80

    for digit in score_str:
        img = numbers_img[int(digit)]
        window.blit(img, (x, y))
        x += img.get_width()


def main():
    bird_rect = bird_frames[0].get_rect(center=(100, SIZE // 2))
    bird_velocity = 0
    gravity = 1200
    strength = -400

    score = 0
    game_state = "start"
    swoosh_played = False

    font = pygame.font.Font(None, 40)
    pipes = []

    data = load_data()
    high_score = data["high_score"]

    run = True
    while run:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == SPAWNPIPE and game_state == "playing":
                pipes.append(create_pipes())

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if game_state == "start":
                    game_state = "playing"
                    bird_velocity = strength
                elif game_state == "playing":
                    bird_velocity = strength
                    wing_sound.play()
                elif game_state == "game_over":
                    pipes.clear()
                    bird_rect.center = (100, SIZE // 2)
                    bird_velocity = 0
                    score = 0
                    game_state = "playing"
                    swoosh_played = False

        if game_state == "playing":
            bird_velocity += gravity * dt
            bird_rect.y += bird_velocity * dt

            for pipe in pipes:
                pipe["top_rect"].x -= speed
                pipe["bottom_rect"].x -= speed

                if pipe["top_rect"].centerx < bird_rect.centerx and not pipe["scored"]:
                    score += 1
                    point_sound.play()
                    pipe["scored"] = True

            pipes = [p for p in pipes if p["top_rect"].x > -pipe_img.get_width()]

            if not check_collision(pipes, bird_rect):
                game_state = "game_over"
                hit_sound.play()
                die_sound.play()

                if score > high_score:
                    high_score = score
                    data["high_score"] = high_score
                    save_data(data)

        # Draw
        scrolling_bg()

        for pipe in pipes:
            window.blit(pipe["top_surface"], pipe["top_rect"])
            window.blit(pipe["bottom_surface"], pipe["bottom_rect"])

        scrolling_base()

        window.blit(bird_frames[0], bird_rect)

        if game_state == "start":
            window.blit(message_img, message_rect)

        if game_state == "playing":
            draw_score(score)
            best_surf = font.render(f"Best: {high_score}", True, (255, 255, 255))
            window.blit(best_surf, (20, 20))

        if game_state == "game_over":
            window.blit(gameover_img, gameover_rect)
            if not swoosh_played:
                swoosh_sound.play()
                swoosh_played = True

        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
