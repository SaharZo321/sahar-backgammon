from pygame import Surface
import pygame
from pygame.time import Clock
from backgammon import Backgammon
from backgammon import BackgammonAI
import config
from config import get_font
from game_manager import GameManager, SettingsKeys
from graphics.elements import ButtonElement
from graphics.graphics_manager import ColorConverter, GraphicsManager
from menus.menus import ConnectingMenu, LostConnectionMenu, UnfocusedMenu, WaitingMenu
from menus.screen import GameScreen, GameScreenButtonKeys
from menus.menus import OptionsMenu
from models import GameState, Move, MoveType, OnlineGameState, ScoredMoves, ServerFlags
from models import Player
from network import BGServer, NetworkClient


class BotGame(GameScreen):

    @classmethod
    def start(cls, screen: Surface, clock: Clock):
        run = True
        options = False
        time = pygame.time.get_ticks()
        ai_moves: list[Move] = []
        graphics = GraphicsManager(screen=screen)
        ai_got_moves = False
        backgammon = Backgammon()
        last_turn = Player.other(backgammon.get_current_turn())

        last_clicked_index = -1
        bot_player = Player.player2

        def play_dice():
            nonlocal last_turn
            if backgammon.get_current_turn() != last_turn:
                cls._play_dice_sound()
                last_turn = backgammon.get_current_turn()
        
        def is_bot_turn() -> bool:
            return bot_player == backgammon.get_current_turn()

        def is_screen_on_top():
            nonlocal options
            return options or not GameManager.is_window_focused()

        def bot_turn():
            def save_ai_moves(scored_moves: ScoredMoves):
                nonlocal ai_got_moves
                ai_got_moves = True
                nonlocal ai_moves
                ai_moves = scored_moves.moves
                print(ai_moves)

            BackgammonAI.get_best_move(game=backgammon, callback=save_ai_moves)

        highlighted_indexes = []

        if is_bot_turn():
            bot_turn()
        else:
            highlighted_indexes = backgammon.get_movable_pieces()

        def leave_button_click():
            nonlocal run
            run = False

        def done_button_click():
            if backgammon.is_game_over():
                winner = backgammon.get_winner()
                backgammon.new_game(winner)
                if is_bot_turn():
                    bot_turn()
                return

            backgammon.switch_turn()
            
            nonlocal time
            time = pygame.time.get_ticks()
            bot_turn()

        def undo_button_click():
            backgammon.undo()
            nonlocal highlighted_indexes
            highlighted_indexes = backgammon.get_movable_pieces()

        def open_options():
            nonlocal options
            options = True

        def close_options():
            nonlocal options
            options = False

        buttons_dict = cls._get_buttons(
            on_leave=leave_button_click,
            on_done=done_button_click,
            on_options=open_options,
            on_undo=undo_button_click,
            graphics=graphics,
        )

        all_buttons = [button for button in buttons_dict.values()]

        game_buttons = [
            buttons_dict[GameScreenButtonKeys.done],
            buttons_dict[GameScreenButtonKeys.undo],
        ]
        always_on_buttons = [
            buttons_dict[GameScreenButtonKeys.leave],
            buttons_dict[GameScreenButtonKeys.options],
        ]

        def on_random_click():
            nonlocal last_clicked_index
            last_clicked_index = -1

        def on_normal_move(clicked_index: int):
            backgammon.make_move(start=last_clicked_index, end=clicked_index)
            on_random_click()

        def on_leave_bar(clicked_index: int):
            backgammon.leave_bar(end=clicked_index)
            on_random_click()

        def on_bear_off(clicked_index: int):
            backgammon.bear_off(start=clicked_index)
            on_random_click()

        def on_choose_piece(clicked_index: int):
            nonlocal last_clicked_index
            last_clicked_index = clicked_index

            nonlocal highlighted_indexes
            highlighted_indexes = backgammon.get_possible_tracks(start=clicked_index)

        while run:
            clock.tick(config.FRAMERATE)
            screen.fill("black")
            cursor = pygame.SYSTEM_CURSOR_ARROW
            GraphicsManager.render_background(screen=screen)
            play_dice()
            player_colors = {
                Player.player1: GameManager.get_setting(SettingsKeys.piece_color),
                Player.player2: GameManager.get_setting(SettingsKeys.opponent_color),
            }
            graphics.render_board(
                game_state=backgammon.get_state(),
                is_online=True,
                player_colors=player_colors,
            )

            if is_bot_turn() and ai_got_moves and pygame.time.get_ticks() - time > 1000:
                time = pygame.time.get_ticks()
                if len(ai_moves) == 0:
                    ai_got_moves = False
                    print("bot played")     
                    if backgammon.is_game_over():
                        done_button_click()
                        continue
                    backgammon.switch_turn()
                else:
                    cls._play_piece_sound()
                    move = ai_moves.pop()
                    print("Handled Move: ", move)
                    backgammon.handle_move(move=move)

            if (
                last_clicked_index == -1
                and not is_bot_turn()
                and not is_screen_on_top()
            ):
                highlighted_indexes = cls._get_highlighted_tracks(
                    graphics=graphics, backgammon=backgammon
                )

            graphics.highlight_tracks(highlighted_indexes)

            buttons_dict[GameScreenButtonKeys.done].toggle(
                disabled=not backgammon.is_turn_done() or is_bot_turn()
            )
            buttons_dict[GameScreenButtonKeys.undo].toggle(
                disabled=not backgammon.has_history() or is_bot_turn()
            )
            
            cursor = cls.get_cursor(
                graphics=graphics,
                buttons=always_on_buttons,
                backgammon=backgammon,
                condition=not is_screen_on_top(),
            )
            
            cursor = cls.get_cursor(
                graphics=graphics,
                buttons=game_buttons,
                backgammon=backgammon,
                condition=not is_screen_on_top() and is_bot_turn(),
            )

            cls._render_elements(
                screen=screen, elements=all_buttons, condition=not is_screen_on_top()
            )
            events = pygame.event.get()
            for event in events:
                cls._check_quit(event=event, quit=GameManager.quit)
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and not is_screen_on_top()
                ):
                    cls._click_elements(elements=always_on_buttons)
                    
                    if not is_bot_turn():
                        cls._click_elements(elements=game_buttons)

                    cls._move_piece(
                        graphics=graphics,
                        backgammon=backgammon,
                        last_clicked_index=last_clicked_index,
                        on_random_click=on_random_click,
                        on_normal_move=on_normal_move,
                        on_leave_bar=on_leave_bar,
                        on_choose_piece=on_choose_piece,
                        on_bear_off=on_bear_off,
                    )

            if not GameManager.is_window_focused():
                UnfocusedMenu.start(screen=screen)
            elif options:
                OptionsMenu.start(screen=screen, close=close_options, events=events)
            else:
                pygame.mouse.set_cursor(cursor)

            pygame.display.flip()


class OfflineGame(GameScreen):

    @classmethod
    def start(cls, screen: Surface, clock: Clock):
        run = True
        options = False
        graphics = GraphicsManager(screen=screen)
        backgammon = Backgammon()
        last_turn = Player.other(backgammon.get_current_turn())
        last_clicked_index = -1

        def play_dice():
            nonlocal last_turn
            if backgammon.get_current_turn() != last_turn:
                cls._play_dice_sound()
                last_turn = backgammon.get_current_turn()
                
        def is_screen_on_top():
            nonlocal options
            return options or not GameManager.is_window_focused()

        def open_options():
            nonlocal options
            options = True

        def close_options():
            nonlocal options
            options = False

        def leave_button_click():
            nonlocal run
            run = False

        def done_button_click():
            if backgammon.is_game_over():
                winner = backgammon.get_winner()
                print(winner)
                backgammon.new_game(winner)
                return

            backgammon.switch_turn()
            buttons_dict[GameScreenButtonKeys.done].toggle()

        def undo_button_click():
            backgammon.undo()
            nonlocal highlighted_indexes
            highlighted_indexes = backgammon.get_movable_pieces()

        highlighted_indexes = backgammon.get_movable_pieces()

        buttons_dict = cls._get_buttons(
            on_leave=leave_button_click,
            on_done=done_button_click,
            on_options=open_options,
            on_undo=undo_button_click,
            graphics=graphics,
        )

        buttons = [button for button in buttons_dict.values()]

        def on_random_click():
            nonlocal last_clicked_index
            last_clicked_index = -1

        def on_normal_move(clicked_index: int):
            backgammon.make_move(start=last_clicked_index, end=clicked_index)
            on_random_click()

        def on_leave_bar(clicked_index: int):
            backgammon.leave_bar(end=clicked_index)
            on_random_click()

        def on_bear_off(clicked_index: int):
            backgammon.bear_off(start=clicked_index)
            on_random_click()

        def on_choose_piece(clicked_index: int):
            nonlocal last_clicked_index
            last_clicked_index = clicked_index

            nonlocal highlighted_indexes
            highlighted_indexes = backgammon.get_possible_tracks(start=clicked_index)

        while run:
            clock.tick(config.FRAMERATE)
            screen.fill("black")
            cursor = pygame.SYSTEM_CURSOR_ARROW
            play_dice()
            GraphicsManager.render_background(screen=screen)

            player_colors = {
                Player.player1: GameManager.get_setting(SettingsKeys.piece_color),
                Player.player2: GameManager.get_setting(SettingsKeys.opponent_color),
            }

            graphics.render_board(
                game_state=backgammon.get_state(), player_colors=player_colors
            )

            if last_clicked_index == -1:
                highlighted_indexes = cls._get_highlighted_tracks(
                    graphics=graphics, backgammon=backgammon
                )

            graphics.highlight_tracks(highlighted_indexes)

            cursor = cls.get_cursor(
                graphics=graphics,
                buttons=buttons,
                backgammon=backgammon,
                condition=not is_screen_on_top(),
            )

            buttons_dict[GameScreenButtonKeys.done].toggle(
                disabled=not backgammon.is_turn_done()
            )
            buttons_dict[GameScreenButtonKeys.undo].toggle(
                disabled=not backgammon.has_history()
            )

            cls._render_elements(
                screen=screen, elements=buttons, condition=not is_screen_on_top()
            )
            events = pygame.event.get()
            for event in events:
                cls._check_quit(event=event, quit=GameManager.quit)
                if event.type == pygame.MOUSEBUTTONDOWN and not is_screen_on_top():

                    cls._click_elements(elements=buttons)

                    cls._move_piece(
                        graphics=graphics,
                        backgammon=backgammon,
                        last_clicked_index=last_clicked_index,
                        on_random_click=on_random_click,
                        on_normal_move=on_normal_move,
                        on_leave_bar=on_leave_bar,
                        on_choose_piece=on_choose_piece,
                        on_bear_off=on_bear_off,
                    )

            if not GameManager.is_window_focused():
                UnfocusedMenu.start(screen=screen)
            elif options:
                OptionsMenu.start(screen=screen, close=close_options, events=events)
            else:
                pygame.mouse.set_cursor(cursor)

            pygame.display.flip()


class LocalClientGame(GameScreen):

    @classmethod
    def start(cls, screen: Surface, clock: Clock):
        run = True
        options = False
        graphics = GraphicsManager(screen=screen)

        def is_screen_on_top():
            nonlocal options
            return options or not GameManager.is_window_focused() or not server.connected

        server = BGServer(
            port=config.GAME_PORT,
            buffer_size=config.NETWORK_BUFFER,
            local_color=ColorConverter.pygame_to_pydantic(
                GameManager.get_setting(SettingsKeys.piece_color)
            ),
            online_color=ColorConverter.pygame_to_pydantic(
                GameManager.get_setting(SettingsKeys.opponent_color)
            ),
        )
        last_turn = Player.other(server.local_get_game_state().current_turn)
        
        def play_dice():
            nonlocal last_turn
            turn = server.local_get_game_state().current_turn
            if turn != last_turn:
                cls._play_dice_sound()
                last_turn = turn
                
        current_state = server.local_get_game_state()

        last_clicked_index = -1

        def quit():
            server.stop_server()
            GameManager.quit()

        def get_movable_pieces():
            return Backgammon([current_state]).get_movable_pieces()

        def leave_button_click():
            server.stop_server()
            nonlocal run
            run = False
        
        def save_state(state: OnlineGameState):
            nonlocal current_state
            current_state = state
            play_dice()

        def done_button_click():
            save_state(server.local_done())
            buttons_dict[GameScreenButtonKeys.done].toggle()
            backgammon = Backgammon([current_state])
            if backgammon.is_game_over():
                print(backgammon.get_winner())

        def undo_button_click():
            save_state(server.local_undo())
            nonlocal highlighted_indexes
            highlighted_indexes = get_movable_pieces()

        def open_options():
            nonlocal options
            options = True

        def close_options():
            nonlocal options
            options = False

        highlighted_indexes = []

        buttons_dict = cls._get_buttons(
            on_leave=leave_button_click,
            on_done=done_button_click,
            on_options=open_options,
            on_undo=undo_button_click,
            graphics=graphics,
        )

        all_buttons = [button for button in buttons_dict.values()]

        game_buttons = [
            buttons_dict[GameScreenButtonKeys.done],
            buttons_dict[GameScreenButtonKeys.undo],
        ]
        always_on_buttons = [
            buttons_dict[GameScreenButtonKeys.leave],
            buttons_dict[GameScreenButtonKeys.options],
        ]

        def is_my_turn() -> bool:
            backgammon = Backgammon([current_state])
            return backgammon.get_current_turn() == Player.player1

        def on_random_click():
            nonlocal last_clicked_index
            last_clicked_index = -1

        def on_normal_move(clicked_index: int):
            move = Move(
                move_type=MoveType.normal_move,
                start=last_clicked_index,
                end=clicked_index,
            )
            save_state(server.local_move(move=move))
            on_random_click()

        def on_leave_bar(clicked_index: int):
            move = Move(
                move_type=MoveType.leave_bar,
                start=backgammon.get_start_position(),
                end=clicked_index,
            )
            save_state(server.local_move(move=move))
            on_random_click()

        def on_bear_off(clicked_index: int):
            move = Move(
                move_type=MoveType.bear_off,
                start=clicked_index,
                end=24,
            )
            save_state(server.local_move(move=move))
            on_random_click()

        def on_choose_piece(clicked_index: int):
            nonlocal last_clicked_index
            last_clicked_index = clicked_index

            nonlocal highlighted_indexes
            highlighted_indexes = backgammon.get_possible_tracks(start=clicked_index)
            

        server.run_server()

        while run:
            clock.tick(config.FRAMERATE)
            screen.fill("black")
            cursor = pygame.SYSTEM_CURSOR_ARROW
            GraphicsManager.render_background(screen=screen)

            current_state = server.local_get_game_state()

            backgammon = Backgammon([current_state])
            
            player_colors = {
                Player.player1: GameManager.get_setting(SettingsKeys.piece_color),
                Player.player2: ColorConverter.pydantic_to_pygame(
                    current_state.online_color
                ),
            }
            graphics.render_board(
                game_state=current_state, is_online=True, player_colors=player_colors
            )

            if last_clicked_index == -1 and is_my_turn() and not is_screen_on_top():
                highlighted_indexes = cls._get_highlighted_tracks(
                    graphics=graphics, backgammon=backgammon
                )

            graphics.highlight_tracks(highlighted_indexes)

            cursor = cls.get_cursor(
                graphics=graphics,
                buttons=game_buttons,
                backgammon=backgammon,
                condition=not is_screen_on_top() and is_my_turn(),
            )
            
            cursor = cls.get_cursor(
                graphics=graphics,
                buttons=always_on_buttons,
                backgammon=backgammon,
                condition=not is_screen_on_top(),
            )

            buttons_dict[GameScreenButtonKeys.done].toggle(
                disabled=not is_my_turn() or not backgammon.is_turn_done()
            )
            buttons_dict[GameScreenButtonKeys.undo].toggle(
                disabled=current_state.history_length == 0 or not is_my_turn()
            )

            cls._render_elements(
                screen=screen, elements=all_buttons, condition=not is_screen_on_top()
            )
            events = pygame.event.get()
            for event in events:
                cls._check_quit(event=event, quit=quit)

                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and not is_screen_on_top()
                ):
                    cls._click_elements(elements=always_on_buttons)

                    if is_my_turn():
                        cls._click_elements(elements=game_buttons)

                    cls._move_piece(
                        graphics=graphics,
                        backgammon=backgammon,
                        last_clicked_index=last_clicked_index,
                        on_random_click=on_random_click,
                        on_normal_move=on_normal_move,
                        on_leave_bar=on_leave_bar,
                        on_choose_piece=on_choose_piece,
                        on_bear_off=on_bear_off,
                    )
            
            if not GameManager.is_window_focused():
                UnfocusedMenu.start(screen=screen)       
            elif not server.connected:
                close_options()
                WaitingMenu.start(screen=screen, close=leave_button_click, events=events)
            elif options:
                OptionsMenu.start(screen=screen, close=close_options, events=events)
            else:
                pygame.mouse.set_cursor(cursor)

            pygame.display.flip()


class OnlineClientGame(GameScreen):
    
    @classmethod
    def start(cls, screen: Surface, clock: Clock, ip_address: str):
        run = True
        options = False
        started = False
        timeout = 10

        graphics = GraphicsManager(screen=screen)
        
        def open_options():
            nonlocal options
            options = True

        def close_options():
            nonlocal options
            options = False

        refresh_frequency = 500  # in milliseconds

        piece_color = GameManager.get_setting(SettingsKeys.piece_color)
        
        current_state: OnlineGameState = OnlineGameState(
            **Backgammon().get_state().model_dump(),
            history_length=0,
            online_color=ColorConverter.pygame_to_pydantic(piece_color),
            local_color=ColorConverter.pygame_to_pydantic(piece_color),
        )

        network_client = NetworkClient(
            host_ip=ip_address,
            port=config.GAME_PORT,
            buffer_size=config.NETWORK_BUFFER,
            timeout=timeout
        )
        last_turn = Player.player1

        def is_reconnecting():
            return network_client.time_from_last_recieve() > timeout / 2
        
        def quit():
            leave_button_click()
            GameManager.quit()
        
        def play_dice():
            nonlocal last_turn
            turn = current_state.current_turn
            if turn != last_turn:
                cls._play_dice_sound()
                last_turn = turn
        
        def save_state(state: OnlineGameState):
            nonlocal current_state
            current_state = state
            
            nonlocal started
            
            if not started:
                cls._play_dice_sound()
            else:
                play_dice()
                
            started = True

        def send_color():
            network_client.send(
                data=ColorConverter.pygame_to_pydantic(piece_color),
                on_recieve=save_state,
            )

        network_client.connect()

        last_clicked_index = -1

        def leave_button_click():
            network_client.disconnect(data=ServerFlags.leave)
            nonlocal run
            run = False

        def done_button_click():
            network_client.send(data=ServerFlags.done, on_recieve=save_state)

        def undo_button_click():
            network_client.send(data=ServerFlags.undo, on_recieve=save_state)

        def is_screen_on_top():
            nonlocal options
            return options or not GameManager.is_window_focused() or is_reconnecting()
        
        highlighted_indexes = []

        buttons_dict = cls._get_buttons(
            on_leave=leave_button_click,
            on_done=done_button_click,
            on_options=open_options,
            on_undo=undo_button_click,
            graphics=graphics,
        )

        all_buttons = [button for button in buttons_dict.values()]

        game_buttons = [
            buttons_dict[GameScreenButtonKeys.done],
            buttons_dict[GameScreenButtonKeys.undo],
        ]
        always_on_buttons = [
            buttons_dict[GameScreenButtonKeys.leave],
            buttons_dict[GameScreenButtonKeys.options],
        ]

        def is_my_turn() -> bool:
            backgammon = Backgammon([current_state])
            return backgammon.get_current_turn() == Player.player1

        time = pygame.time.get_ticks()

        def on_random_click():
            nonlocal last_clicked_index
            last_clicked_index = -1

        def on_normal_move(clicked_index: int):
            move = Move(
                move_type=MoveType.normal_move,
                start=last_clicked_index,
                end=clicked_index,
            )
            network_client.send(data=move, on_recieve=save_state)
            on_random_click()

        def on_leave_bar(clicked_index: int):
            move = Move(
                move_type=MoveType.leave_bar,
                start=backgammon.get_start_position(),
                end=clicked_index,
            )
            network_client.send(data=move, on_recieve=save_state)
            on_random_click()

        def on_bear_off(clicked_index: int):
            move = Move(
                move_type=MoveType.bear_off, start=clicked_index, end=24
            )
            network_client.send(data=move, on_recieve=save_state)
            on_random_click()

        def on_choose_piece(clicked_index: int):
            nonlocal last_clicked_index
            last_clicked_index = clicked_index

            nonlocal highlighted_indexes
            highlighted_indexes = backgammon.get_possible_tracks(start=clicked_index)
            
        while run:
            clock.tick(config.FRAMERATE)
            screen.fill("black")
            cursor = pygame.SYSTEM_CURSOR_ARROW

            GraphicsManager.render_background(screen=screen)

            opponent_color = ColorConverter.pydantic_to_pygame(current_state.local_color)
            piece_color: pygame.Color = GameManager.get_setting(SettingsKeys.piece_color)
            while piece_color == opponent_color:
                piece_color = pygame.Color(
                    255 - opponent_color.r, 255 - opponent_color.g, 255 - opponent_color.b
                )
            player_colors = {
                Player.player1: piece_color,
                Player.player2: opponent_color,
            }
            graphics.render_board(
                game_state=current_state, is_online=True, player_colors=player_colors
            )

            if (
                pygame.time.get_ticks() - time > refresh_frequency
            ):
                time = pygame.time.get_ticks()
                send_color()

            backgammon = Backgammon([current_state])
            if last_clicked_index == -1 and is_my_turn() and not is_screen_on_top() and started:
                highlighted_indexes = cls._get_highlighted_tracks(
                    graphics=graphics, backgammon=backgammon
                )

            graphics.highlight_tracks(highlighted_indexes)

            cursor = cls.get_cursor(
                graphics=graphics,
                buttons=game_buttons,
                backgammon=backgammon,
                condition=not is_screen_on_top() and is_my_turn(),
            )
            
            cursor = cls.get_cursor(
                graphics=graphics,
                buttons=always_on_buttons,
                backgammon=backgammon,
                condition=not is_screen_on_top(),
            )

            buttons_dict[GameScreenButtonKeys.done].toggle(
                disabled=not is_my_turn() or not backgammon.is_turn_done()
            )
            buttons_dict[GameScreenButtonKeys.undo].toggle(
                disabled=current_state.history_length == 0 or not is_my_turn()
            )

            cls._render_elements(
                screen=screen, elements=all_buttons, condition=not is_screen_on_top()
            )
            events = pygame.event.get()
            for event in events:
                cls._check_quit(event=event, quit=quit)
                
                if event.type == pygame.MOUSEBUTTONDOWN and not is_screen_on_top():
                    cls._click_elements(elements=always_on_buttons)

                    if is_my_turn():
                        cls._click_elements(elements=game_buttons)

                    cls._move_piece(
                        graphics=graphics,
                        backgammon=backgammon,
                        last_clicked_index=last_clicked_index,
                        on_random_click=on_random_click,
                        on_normal_move=on_normal_move,
                        on_leave_bar=on_leave_bar,
                        on_choose_piece=on_choose_piece,
                        on_bear_off=on_bear_off,
                    )

            if not network_client.is_connected() and network_client.has_started():
                LostConnectionMenu.start(screen=screen, close=leave_button_click, events=events)
            elif not network_client.has_started() or is_reconnecting():
                ConnectingMenu.start(screen=screen)
                if not network_client.is_connected():
                    run = False
            elif not GameManager.is_window_focused():
                UnfocusedMenu.start(screen=screen)       
            elif options:
                OptionsMenu.start(screen=screen, close=close_options, events=events)
            else:
                pygame.mouse.set_cursor(cursor)

            pygame.display.flip()