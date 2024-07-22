import config
from config import get_font
from game_manager import GameManager, SettingsKeys
from graphics.elements import BetterButtonElement, Element, TextFieldElement
from graphics.elements import ButtonElement
from graphics.graphics_manager import GraphicsManager
from graphics.outline_text import OutlineText
from menus.game_screens import BotGame, LocalClientGame, OfflineGame, OnlineClientGame
from menus.menus import OptionsMenu
from menus.screen import Screen
import pygame
from pygame.time import Clock
import ipaddress
import math

class LostConnection(Screen):

    @classmethod
    def start(cls, screen: pygame.Surface, clock: Clock):
        run = True

        lost_connection = OutlineText(
            text="LOST CONNECTION",
            font=get_font(100),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            position=(config.SCREEN.centerx, 200),
        )
        
        to_the_server = OutlineText(
            text="TO THE SERVER",
            font=get_font(100),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            position=(config.SCREEN.centerx, 300),
        )
        

        def back_click():
            nonlocal run
            run = False

        BACK_BUTTON = ButtonElement(
            position=(config.SCREEN.centerx, 650),
            text_input="BACK",
            font=get_font(50),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            outline_size=1,
            on_click=back_click,
        )

        buttons: list[ButtonElement] = [BACK_BUTTON]

        while run:
            GraphicsManager.render_background(screen)
            clock.tick(config.FRAMERATE)

            lost_connection.update(screen)
            to_the_server.update(screen)
            
            cls._render_elements(screen=screen, elements=buttons)
            pygame.mouse.set_cursor(cls._get_cursor(elements=buttons))
            
            for event in pygame.event.get():
                cls._check_quit(event=event, quit=GameManager.quit)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    cls._click_elements(elements=buttons)

            pygame.display.flip()


class JoinRoomScreen(Screen):

    @classmethod
    def start(cls, screen: pygame.Surface, clock: Clock):
        run = True

        ip_address = GameManager.get_setting(SettingsKeys.ip)

        def back_click():
            nonlocal run
            run = False

        def join_click():
            if not cls._is_valid_ip(ip_address):
                return
            OnlineClientGame.start(screen=screen, clock=clock, ip_address=ip_address)
            GameManager.set_setting(SettingsKeys.ip, ip_address)
            back_click()

        JOIN_BUTTON = BetterButtonElement(
            position=(config.SCREEN.centerx, 500),
            text_input="JOIN",
            font=get_font(70),
            text_color=pygame.Color("black"),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            on_click=join_click,
        )

        BACK_BUTTON = ButtonElement(
            image=None,
            position=(config.SCREEN.centerx, 650),
            text_input="BACK",
            font=get_font(50),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            outline_size=1,
            on_click=back_click,
        )
        
        def set_ip(ip: str):
            nonlocal ip_address
            ip_address = ip
        
        ip_field = TextFieldElement(
            font=get_font(60),
            anchor={"center": (config.SCREEN.centerx, 300)},
            width=500,
            default=ip_address,
            on_value_changed=set_ip,
            text_align="center",
            on_enter=join_click
        )

        menu_text = OutlineText(
            text="Enter IP Address",
            font=get_font(80),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            position=(config.SCREEN.centerx, 100),
        )
        
        elements: list[Element] = [BACK_BUTTON, JOIN_BUTTON, ip_field]

        while run:

            clock.tick(config.FRAMERATE)

            JOIN_BUTTON.toggle(disabled=not cls._is_valid_ip(ip_address))
            
            GraphicsManager.render_background(screen)
            
            menu_text.update(screen)
            
            events = pygame.event.get()
            
            cls._render_elements(screen=screen, elements=elements, events=events)
            pygame.mouse.set_cursor(cls._get_cursor(elements=elements))
            
            for event in events:
                cls._check_quit(event=event, quit=GameManager.quit)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    cls._click_elements(elements=elements)


            pygame.display.flip()
            
    @classmethod
    def _is_valid_ip(cls, address: str):
        try:
            return ipaddress.IPv4Address(address).is_private
        except:
            return False


class OnlineScreen(Screen):

    @classmethod
    def start(cls, screen: pygame.Surface, clock: Clock):
        run = True

        def back_click():
            nonlocal run
            run = False

        def join_room_click():
            JoinRoomScreen.start(screen=screen, clock=clock)
            back_click()

        def create_room_click():
            LocalClientGame.start(screen=screen, clock=clock)
            back_click()

        JOIN_ROOM_BUTTON = BetterButtonElement(
            position=(config.SCREEN.centerx, 270),
            text_input="JOIN ROOM",
            font=get_font(70),
            text_color=pygame.Color("black"),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            on_click=join_room_click,
        )

        CREATE_ROOM_BUTTON = BetterButtonElement(
            position=(config.SCREEN.centerx, 420),
            text_input="CREATE ROOM",
            font=get_font(70),
            text_color=pygame.Color("black"),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            on_click=create_room_click,
        )

        BACK_BUTTON = ButtonElement(
            image=None,
            position=(config.SCREEN.centerx, 650),
            text_input="BACK",
            font=get_font(50),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            outline_size=1,
            on_click=back_click,
        )

        buttons: list[ButtonElement] = [JOIN_ROOM_BUTTON, BACK_BUTTON, CREATE_ROOM_BUTTON]

        while run:

            clock.tick(config.FRAMERATE)
            screen.fill("black")

            GraphicsManager.render_background(screen)

            cls._render_elements(screen=screen, elements=buttons)
            pygame.mouse.set_cursor(cls._get_cursor(elements=buttons))

            for event in pygame.event.get():
                cls._check_quit(event=event, quit=GameManager.quit)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    cls._click_elements(elements=buttons)

            pygame.display.flip()


class PlayScreen(Screen):

    @classmethod
    def start(cls, screen: pygame.Surface, clock: Clock):
        run = True

        def back_button_click():
            nonlocal run
            run = False

        def offline_button_click():
            OfflineGame.start(screen=screen, clock=clock)
            nonlocal run
            run = False

        def bot_button_click():
            BotGame.start(screen=screen, clock=clock)
            nonlocal run
            run = False

        def online_button_click():
            OnlineScreen.start(screen, clock)

        ONLINE_BUTTON = ButtonElement(
            image=None,
            position=(config.SCREEN.centerx, 180),
            text_input="PLAY ON LAN",
            font=get_font(75),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            outline_size=1,
            on_click=online_button_click,
        )

        BOT_BUTTON = ButtonElement(
            image=None,
            position=(config.SCREEN.centerx, 330),
            text_input="PLAY AGAINST BOT",
            font=get_font(75),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            outline_size=1,
            on_click=bot_button_click,
        )

        OFFLINE_BUTTON = ButtonElement(
            image=None,
            position=(config.SCREEN.centerx, 480),
            text_input="PLAY 1v1",
            font=get_font(75),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            outline_size=1,
            on_click=offline_button_click,
        )

        BACK_BUTTON = ButtonElement(
            image=None,
            position=(config.SCREEN.centerx, 650),
            text_input="BACK",
            font=get_font(50),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            outline_color=pygame.Color("black"),
            outline_size=1,
            on_click=back_button_click,
        )

        buttons: list[ButtonElement] = [ONLINE_BUTTON, BOT_BUTTON, OFFLINE_BUTTON, BACK_BUTTON]

        while run:
            screen.fill("black")
            GraphicsManager.render_background(screen=screen)
            clock.tick(config.FRAMERATE)

            cls._render_elements(screen=screen, elements=buttons)
            pygame.mouse.set_cursor(cls._get_cursor(elements=buttons))

            for event in pygame.event.get():
                cls._check_quit(event=event, quit=GameManager.quit)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    cls._click_elements(elements=buttons)

            pygame.display.flip()


class OptionsScreen(Screen):
    
    @classmethod
    def start(cls, screen: pygame.Surface, clock: Clock):
        run = True
        
        def close():
            nonlocal run
            run = False
        
        while run:
            GraphicsManager.render_background(screen=screen)
            clock.tick(config.FRAMERATE)
            events = pygame.event.get()
            OptionsMenu.start(screen=screen, on_top=False, close=close, events=events)
            pygame.display.flip()


class MainScreen(Screen):

    @classmethod
    def start(cls, screen: pygame.Surface, clock: Clock):
        def play_button_click():
            PlayScreen.start(screen=screen, clock=clock)

        def options_button_click():
            OptionsScreen.start(screen=screen, clock=clock)

        def quit_button_click():
            GameManager.quit()

        main_menu = OutlineText(
            text="MAIN MANU",
            font=get_font(100),
            text_color=pygame.Color("white"),
            outline_color=pygame.Color("black"),
            position=(config.SCREEN.centerx, 100),
        )

        PLAY_BUTTON = BetterButtonElement(
            position=(config.SCREEN.centerx, 300),
            text_input="PLAY",
            font=get_font(75),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            on_click=play_button_click,
        )

        OPTIONS_BUTTON = BetterButtonElement(
            position=(config.SCREEN.centerx, 450),
            text_input="OPTIONS",
            font=get_font(75),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            on_click=options_button_click,
        )

        QUIT_BUTTON = ButtonElement(
            image=None,
            position=(config.SCREEN.centerx, 650),
            text_input="QUIT",
            font=get_font(50),
            base_color=config.BUTTON_COLOR,
            hovering_color=config.BUTTON_HOVER_COLOR,
            on_click=quit_button_click,
        )

        buttons: list[ButtonElement] = [PLAY_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]
        while True:
            clock.tick(config.FRAMERATE)

            screen.fill("black")

            GraphicsManager.render_background(screen=screen)

            main_menu.update(screen)

            cls._render_elements(screen=screen, elements=buttons)
            pygame.mouse.set_cursor(cls._get_cursor(elements=buttons))

            for event in pygame.event.get():
                cls._check_quit(event=event, quit=GameManager.quit)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    cls._click_elements(elements=buttons)

            pygame.display.flip()


