import math
import pygame
from asset import asset
import os

DEFAULT_PLAYER1_COLOR = pygame.Color(100, 100, 100)
DEFAULT_PLAYER2_COLOR = pygame.Color(150, 100, 100)
NETWORK_BUFFER = 2048 * 2
GAME_PORT = 6324
RESOLUTION: tuple[int, int] = (1280, 720)
SCREEN = pygame.Rect(0, 0, 1280, 720)
FRAMERATE: int = 60
BUTTON_COLOR = pygame.Color(200, 0, 0)
BUTTON_HOVER_COLOR = pygame.Color(250, 250, 250)
BACKGROUND = pygame.transform.scale(
    pygame.image.load(asset(os.path.join("assets", "images", "background.jpg"))),
    (1280, 720),
)
OPTIONS_ICON = pygame.transform.scale(
    pygame.image.load(asset(os.path.join("assets", "images", "settings.png"))), (60, 60)
)
GAME_ICON = pygame.transform.scale(
    pygame.image.load(asset(os.path.join("assets", "images", "backgammon.png"))),
    (60, 60),
)
VOLUME_ICON = pygame.transform.scale(
    pygame.image.load(asset(os.path.join("assets", "images", "volume.png"))), (60, 60)
)
MUTE_ICON = pygame.transform.scale(
    pygame.image.load(asset(os.path.join("assets", "images", "mute.png"))), (60, 60)
)

BUTTON_SOUND_PATH = asset(os.path.join("assets", "sounds", "button.wav"))
DICE_SOUND_PATH = asset(os.path.join("assets", "sounds", "dice.wav"))
PIECE_SOUND_PATH = asset(os.path.join("assets", "sounds", "piece.mp3"))


def get_font(size: int, bold=False, italic=False) -> pygame.font.Font:
    return pygame.font.SysFont("Cooper Black", size, bold, italic)