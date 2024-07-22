from pydantic_extra_types.color import Color as PydanticColor
import pygame
import pygame.gfxdraw
import math
import config
from config import get_font
from graphics.elements import TrackButtonElement
from models import Player
from models import GameState
from graphics.outline_text import OutlineText


class GraphicsManager:
    screen: pygame.Surface
    surface: pygame.Surface
    top_tracks_rect: list[pygame.Rect]
    bottom_tracks_rect: list[pygame.Rect]
    tracks: list[TrackButtonElement]
    home_tracks: dict[Player, TrackButtonElement]

    RECT: pygame.Rect

    def __init__(
        self,
        screen: pygame.Surface,
    ) -> None:
        self.screen = screen

        # postiion relative to screen
        home_width = self.screen.get_height() * 0.1

        self.RECT = pygame.Rect(
            math.floor(
                (self.screen.get_width() - (self.screen.get_height() + home_width)) / 2
            ),
            0,
            math.floor(screen.get_height() + home_width),
            screen.get_height(),
        )

        self.surface = pygame.Surface(self.RECT.size)

        # position relative to self.surface
        self._HOME_RECT = pygame.Rect(
            0,
            0,
            home_width,
            self.RECT.height,
        )

        self._BOARD_RECT = pygame.Rect(
            self._HOME_RECT.right,
            0,
            self.RECT.height,
            self.RECT.height,
        )

        self._PADDING = math.floor(self.RECT.height / 28)

        self._SIDE_DIMENSIONS = (
            math.floor(self.RECT.height / 2 - 2 * self._PADDING),
            self.RECT.height - 2 * self._PADDING,
        )

        self._LEFT_SIDE_RECT = pygame.Rect(
            (self._PADDING + self._BOARD_RECT.left, self._PADDING)
            + self._SIDE_DIMENSIONS
        )

        self._RIGHT_SIDE_RECT = pygame.Rect(
            (
                self._BOARD_RECT.right - self._SIDE_DIMENSIONS[0] - self._PADDING,
                self._PADDING,
            )
            + self._SIDE_DIMENSIONS
        )

        self._TRIANGLE_HEIGHT = math.floor(self.RECT.height * 0.4)
        self._MINI_RECT = pygame.Rect(
            0, 0, math.floor(self._LEFT_SIDE_RECT.width / 6), self._TRIANGLE_HEIGHT
        )

        self._HOME_TRACK_TOP_RECT = pygame.Rect(
            (
                math.floor(self._HOME_RECT.left + self._PADDING / 2),
                self._HOME_RECT.top + self._PADDING,
            )
            + self._MINI_RECT.size
        )
        self._HOME_TRACK_BOTTOM_RECT = pygame.Rect(
            (
                math.floor(self._HOME_RECT.left + self._PADDING / 2),
                self._HOME_RECT.bottom - self._PADDING - self._MINI_RECT.height,
            )
            + self._MINI_RECT.size
        )

        self._piece_radius = math.floor(self._MINI_RECT.width / 2 - 2)
        self.top_tracks_rect = []
        self.bottom_tracks_rect = []
        self.tracks = []

        self.create_tracks_rects()
        self.create_home_tracks()

    def create_home_tracks(self) -> None:
        self.home_tracks = {
            Player.player2: TrackButtonElement(
                rect=self._HOME_TRACK_TOP_RECT,
                is_top=True,
                surface=self.surface,
                surface_rect=self.RECT,
            ),
            Player.player1: TrackButtonElement(
                rect=self._HOME_TRACK_BOTTOM_RECT,
                is_top=False,
                surface=self.surface,
                surface_rect=self.RECT,
            ),
        }

    def toggle_home_track_button(self, player: Player, highlight: bool = True) -> None:
        self.home_tracks[player].highlighted = highlight

    def toggle_track_button(self, index: int, highlight: bool = True) -> None:
        self.tracks[index].highlighted = highlight

    def highlight_tracks(self, highlighted_indexes: list[int]) -> None:
        self.home_tracks[Player.player1].highlighted = any(
            index > 23 for index in highlighted_indexes
        )
        self.home_tracks[Player.player2].highlighted = any(
            index < 0 for index in highlighted_indexes
        )

        for index, button in enumerate(self.tracks):

            if index in highlighted_indexes:
                button.highlighted = True
            else:
                button.highlighted = False

    def check_track_input(self) -> int:
        """
        Returns the index of hoverd track.
        If no track was clicked, -1 is returned
        """
        for index, button in enumerate(self.tracks):
            if button.is_input_recieved() and button.highlighted:
                return index
        return -1

    def check_home_track_input(self, player: Player) -> bool:
        button = self.home_tracks[player]
        return button.is_input_recieved() and button.highlighted

    def create_tracks_rects(self) -> None:

        # top left RECT
        for i in range(6):
            NEW_RECT_POS = (
                self._LEFT_SIDE_RECT.left + i * self._MINI_RECT.width,
                self._LEFT_SIDE_RECT.top,
            )
            rect = pygame.Rect(NEW_RECT_POS, self._MINI_RECT.size)
            self.top_tracks_rect.append(rect)
            self.tracks.append(
                TrackButtonElement(
                    rect=rect, is_top=True, surface=self.surface, surface_rect=self.RECT
                )
            )

        # top right RECT
        for i in range(6):
            NEW_RECT_POS = (
                self._RIGHT_SIDE_RECT.left + i * self._MINI_RECT.width,
                self._RIGHT_SIDE_RECT.top,
            )
            rect = pygame.Rect(NEW_RECT_POS, self._MINI_RECT.size)
            self.top_tracks_rect.append(rect)
            self.tracks.append(
                TrackButtonElement(
                    rect=rect, is_top=True, surface=self.surface, surface_rect=self.RECT
                )
            )

        # bottom right RECT
        for i in range(6):
            NEW_RECT_POS = (
                self._RIGHT_SIDE_RECT.right - (i + 1) * self._MINI_RECT.width,
                self._RIGHT_SIDE_RECT.bottom - self._MINI_RECT.height,
            )
            rect = pygame.Rect(NEW_RECT_POS, self._MINI_RECT.size)
            self.bottom_tracks_rect.append(rect)
            self.tracks.append(
                TrackButtonElement(
                    rect=rect,
                    is_top=False,
                    surface=self.surface,
                    surface_rect=self.RECT,
                )
            )

        # bottom left RECT
        for i in range(6):
            NEW_RECT_POS = (
                self._LEFT_SIDE_RECT.right - (i + 1) * self._MINI_RECT.width,
                self._LEFT_SIDE_RECT.bottom - self._MINI_RECT.height,
            )
            rect = pygame.Rect(NEW_RECT_POS, self._MINI_RECT.size)
            self.bottom_tracks_rect.append(rect)
            self.tracks.append(
                TrackButtonElement(
                    rect=rect,
                    is_top=False,
                    surface=self.surface,
                    surface_rect=self.RECT,
                )
            )

    def render_board(
        self,
        game_state: GameState,
        player_colors: dict[Player, pygame.Color],
        is_online: bool = False,
    ):

        board = game_state.board
        bar = game_state.bar
        home = game_state.home
        score = game_state.score
        dice = game_state.dice
        current_turn = game_state.current_turn

        # whole board + home
        self.surface.fill("brown")
        side_color = pygame.Color(246, 224, 135)
        pygame.draw.rect(self.surface, "black", (0, 0) + self.RECT.size, 2)

        # left side
        pygame.draw.rect(self.surface, side_color, self._LEFT_SIDE_RECT)
        pygame.draw.rect(self.surface, "black", self._LEFT_SIDE_RECT, 2)

        # right side
        pygame.draw.rect(self.surface, side_color, self._RIGHT_SIDE_RECT)
        pygame.draw.rect(
            self.surface,
            "black",
            self._RIGHT_SIDE_RECT,
            2,
        )

        for button in self.tracks:
            button.render()

        self.render_tracks()

        self.render_pieces(board=board, player_colors=player_colors)

        self.render_bar_pieces(bar=bar, player_colors=player_colors)

        self.render_home(home=home, player_colors=player_colors)

        self.render_dice(dice=dice)

        self.render_score(score=score, player_colors=player_colors)

        self.render_turn(current_turn=current_turn, is_online=is_online)

        self.screen.blit(source=self.surface, dest=self.RECT.topleft)

    def render_pieces(self, board: list[int], player_colors: pygame.Color):
        all_rect = self.top_tracks_rect + self.bottom_tracks_rect

        for index, pieces in enumerate(board):
            player = Player.player1 if pieces > 0 else Player.player2
            color = player_colors[player]
            self.render_track_pieces(
                all_rect[index], color, abs(pieces), index < 12, self._piece_radius
            )

    def render_turn(self, current_turn: Player, is_online: bool):
        text = "Player1" if current_turn == Player.player1 else "Player2"
        if is_online:
            text = "YOU" if current_turn == Player.player1 else "OPPONENT"
        TURN_TEXT = OutlineText.get_surface(
            text=text,
            font=get_font(30),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
        )
        turn_center = (math.floor(self.RECT.left / 2), 130)
        TURN_TEXT_RECT = TURN_TEXT.get_rect(center=turn_center)
        self.screen.blit(TURN_TEXT, TURN_TEXT_RECT)

    def render_dice(self, dice: tuple[int, int]):
        DICE_TEXT = OutlineText.get_surface(
            text=str(dice[0]) + " " + str(dice[1]),
            font=get_font(70),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
        )
        buttons_center = (
            math.floor((self.RECT.right + self.screen.get_width()) / 2),
            560,
        )
        DICE_TEXT_RECT = DICE_TEXT.get_rect(center=buttons_center)
        self.screen.blit(DICE_TEXT, DICE_TEXT_RECT)

    def render_score(
        self, score: dict[Player, int], player_colors: dict[Player, pygame.Color]
    ):
        COLON_SCORE_TEXT = OutlineText.get_surface(
            text=":",
            font=get_font(70),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
        )
        score_center = math.floor(self.RECT.left / 2), 60
        COLON_SCORE_TEXT_RECT = COLON_SCORE_TEXT.get_rect(center=score_center)
        self.screen.blit(COLON_SCORE_TEXT, COLON_SCORE_TEXT_RECT)
        PLAYER1_SCORE_TEXT = OutlineText.get_surface(
            text=str(score[Player.player1]),
            font=get_font(70),
            text_color=player_colors[Player.player1],
            outline_color=pygame.Color("black"),
        )
        player1_midleft = math.floor(COLON_SCORE_TEXT_RECT.right + 10), 60
        PLAYER1_SCORE_TEXT_RECT = PLAYER1_SCORE_TEXT.get_rect(midleft=player1_midleft)
        self.screen.blit(PLAYER1_SCORE_TEXT, PLAYER1_SCORE_TEXT_RECT)

        PLAYER2_SCORE_TEXT = OutlineText.get_surface(
            text=str(score[Player.player2]),
            font=get_font(70),
            text_color=player_colors[Player.player2],
            outline_color=pygame.Color("black"),
        )
        player2_midright = math.floor(COLON_SCORE_TEXT_RECT.left - 10), 60
        PLAYER2_SCORE_TEXT_RECT = PLAYER2_SCORE_TEXT.get_rect(midright=player2_midright)
        self.screen.blit(PLAYER2_SCORE_TEXT, PLAYER2_SCORE_TEXT_RECT)

    def render_tracks(self) -> None:
        for index, rect in enumerate(self.top_tracks_rect):
            first = rect.topleft
            second = rect.topright
            third = (math.floor((rect.right + rect.left) / 2), rect.bottom)
            color = (0, 0, 0) if index % 2 == 0 else (150, 0, 0)
            pygame.gfxdraw.filled_polygon(self.surface, (first, second, third), color)
            pygame.gfxdraw.aapolygon(self.surface, (first, second, third), (0, 0, 0))

        for index, rect in enumerate(self.bottom_tracks_rect):
            first = rect.bottomleft
            second = rect.bottomright
            third = (math.floor((rect.right + rect.left) / 2), rect.top)
            color = (0, 0, 0) if index % 2 == 0 else (150, 0, 0)
            pygame.gfxdraw.filled_polygon(self.surface, (first, second, third), color)
            pygame.gfxdraw.aapolygon(self.surface, (first, second, third), (0, 0, 0))

    def render_track_pieces(
        self,
        rect: pygame.Rect,
        color: pygame.Color,
        number: int,
        is_top: bool,
        radius: int,
    ):
        for i in range(number):
            new_y = (
                (rect.top + radius * (2 * i + 1))
                if is_top
                else (rect.bottom - radius * (2 * i + 1))
            )
            center = (rect.centerx, new_y)
            self.render_piece(
                surface=self.surface, center=center, color=color, radius=radius
            )

    @staticmethod
    def render_piece(
        surface: pygame.Surface,
        center: tuple[int, int],
        color: pygame.Color,
        radius: int,
    ):
        pygame.gfxdraw.filled_circle(surface, center[0], center[1], radius, color)
        pygame.gfxdraw.aacircle(surface, center[0], center[1], radius, (0, 0, 0))
        pygame.gfxdraw.aacircle(
            surface, center[0], center[1], math.floor(radius / 2), (0, 0, 0)
        )

    def render_bar_pieces(self, bar: dict[Player, int], player_colors: pygame.Color):
        # player1
        color = player_colors[Player.player1]
        radius = self._piece_radius
        number = bar[Player.player1]
        centery = math.floor(
            (self._LEFT_SIDE_RECT.right + self._RIGHT_SIDE_RECT.left) / 2
        )
        for counter in range(number):
            counter_center = (
                centery,
                math.floor(
                    (self.RECT.height / 4 - radius * number)
                    + (counter * 2 + 1) * radius
                ),
            )
            self.render_piece(
                surface=self.surface, center=counter_center, color=color, radius=radius
            )

        # player2
        color = player_colors[Player.player2]
        number = bar[Player.player2]
        for counter in range(number):
            counter_center = (
                centery,
                math.floor(
                    (self.RECT.height / 4 * 3 - radius * number)
                    + (counter * 2 + 1) * radius
                ),
            )
            self.render_piece(
                surface=self.surface, center=counter_center, color=color, radius=radius
            )

    def render_home(self, home: dict[Player, int], player_colors: pygame.Color) -> None:

        pygame.draw.rect(
            surface=self.surface, color="black", rect=self._HOME_RECT, width=2
        )

        # top home rect player 2
        pygame.draw.rect(
            surface=self.surface,
            color="black",
            rect=self._HOME_TRACK_TOP_RECT,
            width=0,
            border_radius=3,
        )

        # bottom home rect player 1
        pygame.draw.rect(
            surface=self.surface,
            color="black",
            rect=self._HOME_TRACK_BOTTOM_RECT,
            width=0,
            border_radius=3,
        )

        piece_height = self._HOME_TRACK_TOP_RECT.height / 15
        piece_width = self._HOME_TRACK_TOP_RECT.width
        # render top pieces
        player = Player.player2
        self.home_tracks[player].render()
        for piece in range(home[player]):
            color = player_colors[player]
            top = self._HOME_TRACK_TOP_RECT.top + piece * piece_height
            left = self._HOME_TRACK_TOP_RECT.left
            rect = pygame.Rect(left, top, piece_width, piece_height)
            pygame.draw.rect(
                surface=self.surface, color=color, rect=rect, width=0, border_radius=2
            )
            pygame.draw.rect(
                surface=self.surface, color="black", rect=rect, width=1, border_radius=2
            )

        # render bottom pieces
        player = Player.player1
        self.home_tracks[player].render()
        for piece in range(home[player]):
            color = player_colors[player]
            top = self._HOME_TRACK_BOTTOM_RECT.bottom - (piece + 1) * piece_height
            left = self._HOME_TRACK_BOTTOM_RECT.left
            rect = pygame.Rect(left, top, piece_width, piece_height)
            pygame.draw.rect(
                surface=self.surface, color=color, rect=rect, width=0, border_radius=2
            )
            pygame.draw.rect(
                surface=self.surface, color="black", rect=rect, width=1, border_radius=2
            )

    @staticmethod
    def render_background(screen: pygame.Surface):
        screen.blit(config.BACKGROUND, (0, 0))


class ColorConverter:
    @staticmethod
    def pydantic_to_pygame(pydantic_color: PydanticColor) -> pygame.Color:
        rgb = pydantic_color.as_rgb_tuple()
        return pygame.Color(*rgb)

    @staticmethod
    def pygame_to_pydantic(pygame_color: pygame.Color) -> PydanticColor:
        rgb = pygame_color.r, pygame_color.g, pygame_color.b
        return PydanticColor(value=rgb)

def gradient_surface(left_colour: pygame.Color, right_colour: pygame.Color, size: tuple[int,int]):
    """ Draw a horizontal-gradient filled rectangle covering <target_rect> """
    surface = pygame.Surface( ( 2, 2 ) )                                   # tiny! 2x2 bitmap
    pygame.draw.line( surface, left_colour,  ( 0,0 ), ( 0,1 ) )            # left colour line
    pygame.draw.line( surface, right_colour, ( 1,0 ), ( 1,1 ) )            # right colour line
    surface = pygame.transform.smoothscale(surface, size)  # stretch!
    return surface

def draw_border(surface: pygame.Surface, width: int, color: pygame.Color):
    pygame.draw.rect(surface, color, (0,0) + surface.get_size(), width)
    return surface