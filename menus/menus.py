import math
from typing import Callable

from pygame.time import Clock
import config
from config import get_font
from game_manager import GameManager, SettingsKeys
from graphics.elements import BetterButtonElement, Element
from graphics.graphics_manager import GraphicsManager, draw_border, gradient_surface
from graphics.outline_text import OutlineText
from graphics.elements import ButtonElement, SliderElement
from menus.screen import Screen
import pygame


class Menu(Screen):
    @classmethod
    def start(
        cls,
        screen: pygame.Surface,
        close: Callable[[], None],
        events: list[pygame.event.Event],
    ):
        pass
        raise NotImplementedError()


class OptionsMenu(Menu):
    @classmethod
    def start(
        cls,
        screen: pygame.Surface,
        close: Callable[[], None],
        events: list[pygame.event.Event],
        on_top=True,
    ) -> None:
        if on_top:
            menu_surface = pygame.Surface(
                size=config.RESOLUTION, flags=pygame.SRCALPHA, depth=32
            )
            menu_surface.convert_alpha()
            menu_surface.fill(pygame.Color(0, 0, 0, 200))
            screen.blit(source=menu_surface, dest=(0, 0))

        current_color: pygame.Color = GameManager.get_setting(
            key=SettingsKeys.piece_color
        )
        current_volume: float = GameManager.get_setting(key=SettingsKeys.volume)

        def set_volume(value: float, id: str = None):
            GameManager.set_setting(key=SettingsKeys.volume, value=value)

        def set_color(value: float, id: str):
            color = {
                "red": current_color.r,
                "green": current_color.g,
                "blue": current_color.b,
            }
            color[id] = math.floor(value)
            new_color = pygame.Color(color["red"], color["green"], color["blue"])
            GameManager.set_setting(key=SettingsKeys.piece_color, value=new_color)

        red_slider = SliderElement(
            min_value=0,
            max_value=255,
            label="RED",
            anchor={"center": (config.SCREEN.centerx, 190)},
            label_color=pygame.Color("red"),
            default_value=current_color.r,
            on_value_changed=set_color,
            label_position="top",
            id="red",
            slider_surface=draw_border(
                surface=gradient_surface(
                    left_colour=pygame.Color("black"),
                    right_colour=pygame.Color("red"),
                    size=(150, 30),
                ),
                width=2,
                color=pygame.Color("black"),
            ),
        )

        green_slider = SliderElement(
            min_value=0,
            max_value=255,
            label="GREEN",
            anchor={"center": (config.SCREEN.centerx, 270)},
            default_value=current_color.g,
            on_value_changed=set_color,
            id="green",
            label_position="top",
            label_color=pygame.Color("green"),
            slider_surface=draw_border(
                surface=gradient_surface(
                    left_colour=pygame.Color("black"),
                    right_colour=pygame.Color("green"),
                    size=(150, 30),
                ),
                width=2,
                color=pygame.Color("black"),
            ),
        )

        blue_slider = SliderElement(
            min_value=0,
            max_value=255,
            label="BLUE",
            anchor={"center": (config.SCREEN.centerx, 350)},
            default_value=current_color.b,
            on_value_changed=set_color,
            id="blue",
            label_color=pygame.Color("blue"),
            label_position="top",
            slider_surface=draw_border(
                surface=gradient_surface(
                    left_colour=pygame.Color("black"),
                    right_colour=pygame.Color("blue"),
                    size=(150, 30),
                ),
                width=2,
                color=pygame.Color("black"),
            ),
        )

        def toggle_mute():
            if current_volume > 0:
                GameManager.set_setting(SettingsKeys.mute_volume, current_volume)
                set_volume(0)
            else:
                set_volume(GameManager.get_setting(SettingsKeys.mute_volume))

        volume_button = BetterButtonElement(
            position=(50, 50),
            image=pygame.transform.scale(
                config.MUTE_ICON if current_volume == 0 else config.VOLUME_ICON,
                (30, 30),
            ),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            padding=15,
            on_click=toggle_mute,
        )

        GraphicsManager.render_piece(
            screen, center=(450, 290), color=current_color, radius=50
        )

        volume_slider = SliderElement(
            min_value=0,
            max_value=1,
            label=volume_button,
            anchor={"center": (config.SCREEN.centerx, 470)},
            default_value=current_volume,
            on_value_changed=set_volume,
            label_position="top",
            id="volume",
        )

        back_button = ButtonElement(
            position=(config.SCREEN.centerx, 650),
            text_input="BACK",
            font=get_font(50),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            outline_size=1,
            on_click=close,
        )

        OutlineText.render(
            text="OPTIONS",
            font=get_font(80),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            outline_width=3,
            surface=screen,
            position=(config.SCREEN.centerx, 70),
        )

        elements: list[Element] = [
            back_button,
            volume_button,
            green_slider,
            red_slider,
            blue_slider,
            volume_slider,
            volume_button,
        ]

        pygame.mouse.set_cursor(cls._get_cursor(elements=elements))
        cls._render_elements(screen=screen, elements=elements)

        for event in events:
            cls._check_quit(event, GameManager.quit)
            if event.type == pygame.MOUSEBUTTONDOWN:
                cls._click_elements(elements=elements)


class ConnectingMenu(Menu):

    @classmethod
    def start(cls, screen: pygame.Surface) -> None:
        menu_surface = pygame.Surface(
            size=config.RESOLUTION, flags=pygame.SRCALPHA, depth=32
        )
        menu_surface.convert_alpha()
        menu_surface.fill(pygame.Color(0, 0, 0, 180))
        screen.blit(source=menu_surface, dest=(0, 0))

        OutlineText.render(
            text="CONNECTING...",
            font=get_font(100),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            outline_width=3,
            surface=screen,
            position=(config.SCREEN.centerx, 300),
        )

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)


class UnfocusedMenu(Menu):

    @classmethod
    def start(cls, screen: pygame.Surface) -> None:
        menu_surface = pygame.Surface(
            size=config.RESOLUTION, flags=pygame.SRCALPHA, depth=32
        )
        menu_surface.convert_alpha()
        menu_surface.fill(pygame.Color(0, 0, 0, 180))
        screen.blit(source=menu_surface, dest=(0, 0))

        OutlineText.render(
            surface=screen,
            text="UNFOCUSED...",
            font=get_font(100),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            outline_width=3,
            position=(config.SCREEN.centerx, math.floor(config.RESOLUTION[1] / 2.5)),
        )

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)


class WaitingMenu(Menu):

    @classmethod
    def start(
        cls,
        screen: pygame.Surface,
        close: Callable[[], None],
        events: list[pygame.event.Event],
    ):
        menu_surface = pygame.Surface(
            size=config.RESOLUTION, flags=pygame.SRCALPHA, depth=32
        )
        menu_surface.convert_alpha()
        menu_surface.fill(pygame.Color(0, 0, 0, 180))
        screen.blit(source=menu_surface, dest=(0, 0))

        OutlineText.render(
            text="PLAYER 2 NOT CONNECTED",
            font=get_font(60),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            outline_width=3,
            position=(config.SCREEN.centerx, 200),
            surface=screen,
        )

        OutlineText.render(
            text="WATING",
            font=get_font(80),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            outline_width=3,
            position=(config.SCREEN.centerx, 400),
            surface=screen,
        )

        leave_button = BetterButtonElement(
            position=(config.SCREEN.centerx, 650),
            text_input="LEAVE",
            font=get_font(50),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            on_click=close,
        )

        cls._render_elements(screen=screen, elements=[leave_button])
        pygame.mouse.set_cursor(cls._get_cursor(elements=[leave_button]))

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                cls._click_elements([leave_button])


class LostConnectionMenu(Menu):

    @classmethod
    def start(
        cls,
        screen: pygame.Surface,
        close: Callable[[], None],
        events: list[pygame.event.Event],
    ):
        menu_surface = pygame.Surface(
            size=config.RESOLUTION, flags=pygame.SRCALPHA, depth=32
        )
        menu_surface.convert_alpha()
        menu_surface.fill(pygame.Color(0, 0, 0, 180))
        screen.blit(source=menu_surface, dest=(0, 0))

        OutlineText.render(
            text="LOST CONNECTION",
            font=get_font(80),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            outline_width=3,
            position=(config.SCREEN.centerx, 300),
            surface=screen,
        )

        OutlineText.render(
            text="TO THE SERVER",
            font=get_font(80),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            outline_width=3,
            position=(config.SCREEN.centerx, 400),
            surface=screen,
        )

        leave_button = BetterButtonElement(
            position=(config.SCREEN.centerx, 650),
            text_input="LEAVE",
            font=get_font(50),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            on_click=close,
        )

        cls._render_elements(screen=screen, elements=[leave_button])
        pygame.mouse.set_cursor(cls._get_cursor(elements=[leave_button]))

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                cls._click_elements([leave_button])
