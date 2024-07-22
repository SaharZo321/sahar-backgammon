import random
from threading import Thread
from models import GameState, MoveType, OnlineGameState, ScoredMoves
from models import Player
import copy
from models import Move
from typing import Callable, Self

type Dice = tuple[int, int]


class Backgammon:
    history: list[GameState]

    
    def deepcopy(self):
        bg = Backgammon(state_list=[state.model_copy() for state in self.history])
        return bg
    
    def __init__(self, state_list: list[GameState] | None = None) -> None:
        if state_list is None:
            self.new_game()
            self.score = {
                Player.player1: 0,
                Player.player2: 0,
            }
        else:
            self.history = state_list

    def new_game(self, winner: Player | None = None):
        dice = self.roll_dice()
        if winner is None:
            while dice[0] == dice[1]:
                dice = self.roll_dice()
        moves_left = self.get_moves_from_dice(dice=dice)
        first_turn = (
            winner
            if winner is not None
            else (Player.player1 if dice[0] > dice[1] else Player.player2)
        )
        score = (
            {Player.player1: 0, Player.player2: 0}
            if winner is None
            else self.get_winning_score(winner=winner)
        )
        new_state = GameState(
            board=self.create_board(),
            bar={
                Player.player1: 0,
                Player.player2: 0,
            },
            home={
                Player.player1: 0,
                Player.player2: 0,
            },
            dice=dice,
            current_turn=first_turn,
            moves_left=moves_left,
            score=score,
        )
        self.history = [new_state]

    def create_board(self) -> None:
        # Initialize board with pieces in starting positions
        board = [0] * 24
        board[0] = 2  # Two black pieces on position 0
        board[5] = -5  # Five white pieces on position 5
        board[7] = -3  # Three white pieces on position 7
        board[11] = 5  # Five black pieces on position 11
        board[12] = -5  # Five white pieces on position 12
        board[16] = 3  # Three black pieces on position 16
        board[18] = 5  # Five black pieces on position 18
        board[23] = -2  # Two white pieces on position 23
        return board

    def create_board_check(self) -> None:
        # Initialize board with pieces in starting positions
        board = [0] * 24
        board[0] = -2
        board[1] = -2
        board[2] = -2
        board[3] = -3
        board[4] = -3
        board[5] = -3
        board[23] = 1
        return board

    def get_board(self):
        return self.history[-1].board

    def set_board(self, board):
        self.history[-1].board = board

    def get_bar(self):
        return self.history[-1].bar

    def set_bar(self, bar: dict[Player, int]):
        self.history[-1].bar = bar

    def get_home(self):
        return self.history[-1].home

    def set_home(self, home: dict[Player, int]):
        self.history[-1].home = home

    def get_dice(self):
        return self.history[-1].dice

    def set_dice(self, dice: tuple[int, int]):
        self.history[-1].dice = dice

    def get_moves_left(self):
        return self.history[-1].moves_left

    def set_moves_left(self, moves_left: list[int]):
        self.history[-1].moves_left = moves_left

    def get_score(self):
        return self.history[-1].score

    def set_score(self, score: dict[Player, int]):
        self.history[-1].score = score

    def get_current_turn(self):
        return self.history[-1].current_turn

    def set_current_turn(self, current_turn: Player):
        self.history[-1].current_turn = current_turn

    def get_state(self):
        return self.history[-1].model_copy(deep=True)

    @classmethod
    def get_piece_type(cls, player: Player):
        return 1 if player == Player.player1 else -1  # 1 for player1, -1 for player2

    def get_player(self, type: int) -> Player:
        return (
            Player.player1 if type > 0 else Player.player2
        )  # 1 for player1, -1 for player2

    def save_state(self, state: GameState) -> None:
        self.history.append(state)

    def undo(self):
        if len(self.history) > 1:
            self.history.pop()
            return True
        return False

    def roll_dice(self) -> Dice:
        dice = (random.randint(1, 6), random.randint(1, 6))
        return dice

    def get_moves_from_dice(self, dice: tuple[int, int]):
        if dice[0] == dice[1]:  # Double roll
            return [dice[0]] * 4
        return [dice[0], dice[1]]

    def is_valid_move(self, start: int, end: int) -> bool:
        piece_type = self.get_piece_type(self.get_current_turn())
        board_range = range(24)
        board = self.get_board()
        if start not in board_range or end not in board_range:
            return False
        if (start - end) * piece_type > 0:
            return False
        if board[start] * piece_type <= 0:
            return False
        if board[end] * piece_type < -1:
            return False
        die = abs(end - start)
        if die not in self.get_moves_left():
            return False
        return True

    def make_move(self, start: int, end: int) -> bool:
        if not self.is_valid_move(start, end):
            return False

        new_state = self.get_state()  # Save state before making a move
        piece_type = self.get_piece_type(new_state.current_turn)
        new_state.board[start] -= piece_type

        if new_state.board[end] * piece_type == -1:  # Hit opponent's single piece
            new_state.board[end] = piece_type
            new_state.bar[Player.other(new_state.current_turn)] += 1
        else:
            new_state.board[end] += piece_type

        die = abs(end - start)
        new_state.moves_left.remove(die)

        self.save_state(new_state)
        return True

    def get_start_position(self) -> int:
        return -1 if self.get_current_turn() == Player.player1 else 24

    def can_leave_bar(self, end: int) -> bool:
        piece_type = self.get_piece_type(self.get_current_turn())
        return self.get_board()[end] * piece_type > -2

    def leave_bar(self, end: int) -> bool:
        if not self.can_leave_bar(end):
            return False

        new_state = self.get_state()
        piece_type = self.get_piece_type(new_state.current_turn)

        new_state.bar[self.get_current_turn()] -= 1

        if new_state.board[end] * piece_type == -1:  # Hit opponent's single piece
            new_state.board[end] = piece_type
            new_state.bar[Player.other(new_state.current_turn)] += 1
        else:
            new_state.board[end] += piece_type

        die = abs(self.get_start_position() - end)
        new_state.moves_left.remove(die)

        self.save_state(new_state)
        return True

    def get_bar_leaving_positions(self) -> list[int]:
        positions: list[int] = []

        if self.get_captured_pieces() == 0:
            return positions

        start = self.get_start_position()

        for die in self.get_moves_left():
            target_position = start + die * self.get_piece_type(self.get_current_turn())
            if target_position not in positions and self.can_leave_bar(target_position):
                positions.append(target_position)

        return positions

    def switch_turn(self) -> Dice:
        print("switched turn")
        self.history = [self.history[-1]]
        self.set_current_turn(Player.other(self.get_current_turn()))
        dice = self.roll_dice()
        self.set_dice(dice)
        self.set_moves_left(self.get_moves_from_dice(dice))

    def is_bearing_off(self) -> bool:
        home_range = self.get_home_range(self.get_current_turn())
        piece_type = self.get_piece_type(self.get_current_turn())
        return not any(
            (pieces * piece_type > 0 and position not in home_range)
            for position, pieces in enumerate(self.get_board())
        )

    def can_bear_off(self, position: int, die: int) -> bool:
        home_range = self.get_home_range(self.get_current_turn())
        if not ((position in home_range) and self.is_bearing_off()):
            return False

        piece_type = self.get_piece_type(self.get_current_turn())
        occupied_positions = [
            position
            for position in home_range
            if self.get_board()[position] * piece_type > 0
        ]
        if len(occupied_positions) == 0:
            return False

        die_to_bear_off = (
            24 - position if Player.player1 == self.get_current_turn() else position + 1
        )
        if die_to_bear_off == die:
            return True

        # Allow bearing off from the highest position if the die roll is higher

        farthest_position = (
            max(occupied_positions)
            if self.get_current_turn() == Player.player2
            else min(occupied_positions)
        )

        return (
            position == farthest_position
            and die * piece_type + position not in home_range
        )

    def bear_off(self, start: int) -> bool:

        if not any(self.can_bear_off(start, die) for die in self.get_moves_left()):
            return False

        new_state = self.get_state()

        min_die = 24 - start if Player.player1 == new_state.current_turn else start + 1

        higher_dice = [die for die in new_state.moves_left if die >= min_die]

        die_to_remove = min(higher_dice)
        new_state.moves_left.remove(die_to_remove)

        new_state.board[start] -= 1 if self.get_current_turn() == Player.player1 else -1
        new_state.home[self.get_current_turn()] += 1

        self.save_state(new_state)
        return True

    def is_game_over(self) -> bool:
        return self.get_winner() is not None

    def get_winner(self) -> Player | None:
        if self.get_home()[Player.player2] == 15:
            return Player.player2
        elif self.get_home()[Player.player1] == 15:
            return Player.player1
        return None

    def get_winning_score(self, winner: Player):
        loser = Player.other(player=winner)
        current_score: dict[Player, int] = self.get_score()
        if self.get_bar()[loser] > 0 or any(
            self.get_board()[index] * self.get_piece_type(loser) > 0
            for index in self.get_home_range(winner)
        ):
            current_score[winner] += 3
        elif self.get_home()[loser] > 0:
            current_score[winner] += 1
        else:
            current_score[winner] += 2
        return current_score

    def get_movable_pieces(self) -> list[int]:
        if self.get_bar()[self.get_current_turn()] > 0:
            return []
        placements: list[int] = []
        piece_type = self.get_piece_type(self.get_current_turn())
        for position, placement in enumerate(self.get_board()):
            if (
                placement * piece_type > 0
                and len(self.get_possible_tracks(position)) > 0
            ):
                placements.append(position)
        return placements

    def is_start_valid(self, start: int):

        return (
            start in range(0, 24)
            and self.get_board()[start] * self.get_piece_type(self.get_current_turn())
            > 0
        )

    def get_possible_tracks(self, start: int) -> list[int]:
        if not self.is_start_valid(start=start):
            return []

        possible_tracks: list[int] = []

        piece_type = self.get_piece_type(self.get_current_turn())
        for die in self.get_moves_left():
            end = start + die * piece_type
            if (
                self.is_valid_move(start, end) or self.can_bear_off(start, die)
            ) and end not in possible_tracks:
                possible_tracks.append(end)
        return possible_tracks

    def is_turn_done(self) -> bool:
        if len(self.get_moves_left()) == 0:
            return True
        if (
            len(self.get_movable_pieces()) == 0
            and len(self.get_bar_leaving_positions()) == 0
        ):
            return True
        return False

    def get_home_range(self, player: Player) -> range:
        return range(0, 6) if player == Player.player2 else range(18, 24)

    def get_captured_pieces(self) -> int:
        return self.get_bar()[self.get_current_turn()]

    def has_history(self) -> bool:
        return len(self.history) > 1

    def handle_move(self, move: Move):
        match move.move_type:
            case MoveType.normal_move:
                print(self.make_move(start=move.start, end=move.end))
            case MoveType.bear_off:
                print(self.bear_off(move.start))
            case MoveType.leave_bar:
                print(self.leave_bar(move.end))


from pydantic_extra_types.color import Color


class OnlineBackgammon:
    game: Backgammon
    started: bool
    is_player2_connected: bool
    local_color: Color
    online_color: Color

    def __init__(self, online_color: Color, local_color: Color) -> None:
        self.game = Backgammon()
        self.started = False
        self.is_player2_connected = False
        self.online_color = online_color
        self.local_color = local_color

    def new_game(self) -> None:
        winner = self.game.get_winner()
        self.game.new_game(winner=winner)

    def manipulate_board(self) -> OnlineGameState:
        board = self.game.get_board()
        new_board = [0] * len(board)

        for index, track in enumerate(board):
            oposite_index = len(board) - index - 1
            new_board[oposite_index] = track * -1

        bar = self.game.get_bar()
        new_bar = {
            Player.player1: bar[Player.player2],
            Player.player2: bar[Player.player1],
        }

        home = self.game.get_home()
        new_home = {
            Player.player1: home[Player.player2],
            Player.player2: home[Player.player1],
        }

        current_turn = self.game.get_current_turn()
        new_current_turn = Player.other(current_turn)

        state = self.game.get_state()
        state.board = new_board
        state.bar = new_bar
        state.home = new_home
        state.current_turn = new_current_turn

        return self.get_online_game_state(state)

    def manipulate_move(self, move: Move) -> Move:
        board_length = len(self.game.get_board())
        return Move(
            move_type=move.move_type,
            start=board_length - move.start - 1,
            end=board_length - move.end - 1,
        )

    def get_online_game_state(self, state: GameState | None = None) -> OnlineGameState:
        if state is None:
            state = self.game.get_state()

        return state.to_online_game_state(
            online_color=self.online_color,
            local_color=self.local_color,
            history_length=len(self.game.history) - 1
        )


class BackgammonAI:
    PIECE_SAFETY = 1
    PRIME_BUILDING = 1
    PIECE_MOBILITY = 1
    PIECE_BEARING_OFF = 1
    BAR = 1

    @classmethod
    def _evaluate_game_state(cls, state: GameState):
        score = 0

        # Factor 1: Piece Safety
        score += cls.PIECE_SAFETY * cls._evaluate_piece_safety(state=state)

        # Factor 2: Prime Building
        score += cls.PRIME_BUILDING * cls._evaluate_prime_building(state=state)

        # Factor 3: Mobility
        score += cls.PIECE_MOBILITY * cls._evaluate_mobility(state=state)

        # Factor 4: Bearing Off
        score += cls.PIECE_BEARING_OFF * cls._evaluate_bearing_off(state=state)

        # Factor 5: Opponent's Bar
        score += cls.BAR * cls._evaluate_bar(state=state)

        return score

    @staticmethod
    def _evaluate_piece_safety(state: GameState):
        piece_type = Backgammon.get_piece_type(state.current_turn)

        score = 0
        for pos in range(len(state.board)):
            if state.board[pos] * piece_type == 1:
                score -= 5  # Penalize blots
            elif state.board[pos] * piece_type > 1:
                score += 2  # Reward anchors
        return score

    @staticmethod
    def _evaluate_prime_building(state: GameState):
        score = 0
        current_streak = 0
        piece_type = Backgammon.get_piece_type(state.current_turn)
        for pos in range(24):
            if state.board[pos] * piece_type > 1:
                current_streak += 1
            else:
                if current_streak > 1:
                    score += current_streak * 10  # Reward longer primes
                current_streak = 0
        if current_streak > 1:
            score += current_streak * 10  # Reward primes at the end of the board
        return score

    @staticmethod
    def _evaluate_mobility(state: GameState):
        score = 0
        piece_type = Backgammon.get_piece_type(state.current_turn)
        for pos in range(24):
            if state.board[pos] * piece_type > 0:
                for die in range(1, 7):  # Consider all possible die rolls
                    end_pos = pos + die * piece_type
                    if 0 <= end_pos < 24:
                        if state.board[end_pos] * piece_type >= 0:
                            score += 1  # Reward possible legal moves
        return score

    @staticmethod
    def _evaluate_bearing_off(state: GameState):
        score = 0
        piece_type = Backgammon.get_piece_type(state.current_turn)
        home_range = range(18, 24) if piece_type == 1 else range(0, 6)
        for pos in home_range:
            if state.board[pos] * piece_type > 1:
                score += 30  # Reward closer pieces to bearing off
            if state.board[pos] * piece_type == 1:
                score -= 10
        score += state.home[state.current_turn] * 50  # High reward for borne off pieces
        return score

    @staticmethod
    def _evaluate_bar(state: GameState):
        score = 0
        score += (
            state.bar[Player.other(state.current_turn)] * 20
        )  # Reward for opponent's pieces on the bar
        score -= (
            state.bar[state.current_turn] * 20
        )  # Penalize for bot's pieces on the bar
        return score

    @classmethod
    def _get_all_possible_moves(cls, game: Backgammon):
        movable_pieces = game.get_movable_pieces()
        possible_moves: list[Move] = []

        for start in movable_pieces:
            possible_end_pos = game.get_possible_tracks(start=start)

            def to_move(end: int) -> Move:
                move_type: MoveType = (
                    MoveType.bear_off
                    if end not in range(0, 24)
                    else MoveType.normal_move
                )
                return Move(start=start, end=end, move_type=move_type)

            possible_moves += map(to_move, possible_end_pos)

        return possible_moves

    @classmethod
    def _threaded_get_best_move(cls, game: Backgammon) -> ScoredMoves:

        number_of_moves = len(game.get_moves_left())

        if number_of_moves == 0:
            return ScoredMoves(
                score=cls._evaluate_game_state(game.get_state()),
                moves=[],
            )

        if game.get_captured_pieces() > 0:  # AI has captured pieces
            best_scored_moves = ScoredMoves(moves=[], score=-1000)
            bar_leaveing_positions = game.get_bar_leaving_positions()
            print("Bar Leaving positions: ", bar_leaveing_positions)
            for end in bar_leaveing_positions:
                game.leave_bar(end)
                scored_moves = cls._threaded_get_best_move(game=game)
                if scored_moves.score >= best_scored_moves.score:
                    best_scored_moves = scored_moves
                    best_scored_moves.moves.append(
                        Move(
                            move_type=MoveType.leave_bar,
                            start=game.get_start_position(),
                            end=end,
                        )
                    )
                game.undo()
            return best_scored_moves

        current_possible_moves = cls._get_all_possible_moves(game)
        if len(current_possible_moves) == 0:
            return ScoredMoves(
                score=cls._evaluate_game_state(game.get_state()), moves=[]
            )

        best_scored_moves = ScoredMoves(moves=[], score=-1000)

        for move in current_possible_moves:
            move_type = MoveType.normal_move
            if move.end not in range(0, 24):
                move_type = MoveType.bear_off
                game.bear_off(move.start)
            else:
                game.make_move(move.start, move.end)
            scored_moves = cls._threaded_get_best_move(game=game)
            if scored_moves.score >= best_scored_moves.score:
                best_scored_moves = scored_moves
                best_scored_moves.moves.append(
                    Move(
                        move_type=move_type,
                        start=move.start,
                        end=move.end,
                    )
                )
            game.undo()

        return best_scored_moves

    @classmethod
    def get_best_move(
        cls, game: Backgammon, callback: Callable[[ScoredMoves], None] = lambda x: None
    ) -> None:

        game_copy = game.deepcopy()

        def get_best_move():
            moves = cls._threaded_get_best_move(game_copy)
            callback(moves)

        thread = Thread(target=get_best_move)
        thread.start()
