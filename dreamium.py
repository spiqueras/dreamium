#!/usr/bin/python3
# Copyright (c) 2017 Santiago Piqueras

import curses
import random
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum

VERSION = "0.1.1"


class Color(IntEnum):
    RED = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4


class CardType(IntEnum):
    SUN = 1
    MOON = 2
    KEY = 3
    DOOR = 4
    NIGHTMARE = 5
    BACK = 6


_ASCII_ = {
    CardType.SUN: """\
╭─┐
│☀│
└─╯""".splitlines(),
    CardType.MOON: """\
╭─┐
│☽│
└─╯""".splitlines(),
    CardType.KEY: """\
╭─┐
│⚷│
└─╯""".splitlines(),
    CardType.DOOR: """\
╭─┐
│╶│
└─╯""".splitlines(),
    CardType.NIGHTMARE: """\
╭─┐
│☠│
└─╯""".splitlines(),
    CardType.BACK: """\
╭╥┐
╞╬╡
└╨╯""".splitlines(),
}

_ASCII_REDUCED_ = {
    CardType.SUN: """\
╭
☀
└""".splitlines(),
    CardType.MOON: """\
╭
│
☽""".splitlines(),
    CardType.KEY: """\
⚷
│
└""".splitlines(),
}

_CURSES_COLORS_ = {
    Color.GREEN: 3,
    Color.RED: 2,
    Color.BLUE: 5,
    Color.YELLOW: 4
}


class Card:
    def __init__(self, card_type, color=None):
        self.color = color
        self.card_type = card_type

    def draw(self, window, x_offset, y_offset=0, options=0):
        if self.card_type is CardType.NIGHTMARE:
            for j in range(3):
                window.addstr(y_offset + j, x_offset, _ASCII_[self.card_type][j],
                              curses.color_pair(6) | options)
            return
        for j in range(3):
            window.addstr(y_offset + j, x_offset, _ASCII_[self.card_type][j],
                          curses.color_pair(_CURSES_COLORS_[self.color]) | options)

    def draw_reduced(self, window, x_offset, y_offset=0, options=0):
        for j in range(3):
            window.addstr(y_offset + j, x_offset, _ASCII_REDUCED_[self.card_type][j],
                          curses.color_pair(_CURSES_COLORS_[self.color]) | options)


class Doors:
    doors_counter = {}
    doors = {}
    doors_per_color = 2

    def __init__(self):
        for color in Color:
            self.doors[color] = Card(CardType.DOOR, color)
        self.reset()

    def reset(self):
        for color in Color:
            self.doors_counter[color] = 0
        self.doors_per_color = 2

    def can_open(self, color):
        return self.doors_counter[color] - self.doors_per_color

    def open_door(self, color):
        self.doors_counter[color] += 1

    def close_door(self, color):
        if not self.doors_counter[color]:
            return False
        self.doors_counter[color] -= 1
        return True

    def check_all_open(self):
        for c in self.doors_counter.values():
            if c != 2:
                return False
        return True

    def draw(self, window):
        for j, color in enumerate(Color):
            self.doors[color].draw(window, j * 4)
            window.addstr(1, j * 4 + 1, str(self.doors_counter[color]),
                          curses.color_pair(_CURSES_COLORS_[color]))


class Deck:
    STANDARD = [(CardType.SUN, Color.RED, 9),
                (CardType.MOON, Color.RED, 4),
                (CardType.KEY, Color.RED, 3),
                (CardType.DOOR, Color.RED, 2),
                (CardType.SUN, Color.BLUE, 8),
                (CardType.MOON, Color.BLUE, 4),
                (CardType.KEY, Color.BLUE, 3),
                (CardType.DOOR, Color.BLUE, 2),
                (CardType.SUN, Color.GREEN, 7),
                (CardType.MOON, Color.GREEN, 4),
                (CardType.KEY, Color.GREEN, 3),
                (CardType.DOOR, Color.GREEN, 2),
                (CardType.SUN, Color.YELLOW, 6),
                (CardType.MOON, Color.YELLOW, 4),
                (CardType.KEY, Color.YELLOW, 3),
                (CardType.DOOR, Color.YELLOW, 2),
                (CardType.NIGHTMARE, None, 10)]

    cards = []
    num_nightmares = 0

    def __init__(self, card_list=None):
        self.reset(card_list)

    def reset(self, card_list=None):
        cards = self.STANDARD
        self.cards = []
        if card_list:
            cards = card_list
        for card_type, color, quantity in cards:
            if card_type is CardType.NIGHTMARE:
                self.num_nightmares = quantity
            self.cards += [Card(card_type, color) for _ in range(quantity)]

    def add_card(self, card):
        if card.card_type is CardType.NIGHTMARE:
            self.num_nightmares += 1
        self.cards.append(card)

    def next(self):
        card = self.cards.pop(-1)
        if card.card_type is CardType.NIGHTMARE:
            self.num_nightmares -= 1
        return card

    def shuffle(self):
        random.shuffle(self.cards)

    def num_cards(self):
        return len(self.cards)

    def remove_door(self, color):
        for card in self.cards:
            if card.card_type is CardType.DOOR and card.color == color:
                self.cards.remove(card)
                break

    def draw(self, window):
        for j in range(3):
            window.addstr(j, 0, _ASCII_[CardType.BACK][j],
                          curses.color_pair(6))
        window.addstr(1, 4, str(self.num_cards()).rjust(2, " ") + " ╬")
        window.addstr(2, 4, str(self.num_nightmares).rjust(2, " ") + " ☠")


class Path:
    MAX_COMBO = 3
    cards = []
    combo = 0

    def __init__(self):
        self.reset()

    def reset(self):
        self.cards = []
        self.combo = 0

    def add_card(self, card):
        if self.cards and self.cards[-1].card_type == card.card_type:
            return False
        if self.cards and self.cards[-1].color != card.color or \
                self.combo == self.MAX_COMBO:
            self.combo = 0
        self.combo += 1
        self.cards.append(card)
        return True

    def get_card(self, index):
        return self.cards[index]

    def has_combo(self):
        return self.combo >= self.MAX_COMBO

    def draw(self, window):
        x = 0
        for i, card in enumerate(self.cards):
            if len(self.cards) - i >= 5:
                card.draw_reduced(window, x)
                x += 1
            else:
                card.draw(window, x)
                x += 2


class Discard:
    cards_counter = {}
    cards = {}
    last_card = None
    draw_full = False

    def __init__(self):
        self.reset()

    def reset(self):
        self.draw_full = False
        for card_type in (CardType.SUN, CardType.MOON, CardType.KEY):
            for color in Color:
                self.cards_counter[(card_type, color)] = 0
                self.cards[(card_type, color)] = Card(card_type, color)
        self.cards_counter[(CardType.NIGHTMARE, None)] = 0
        self.cards[(CardType.NIGHTMARE, None)] = Card(CardType.NIGHTMARE, None)
        self.last_card = None

    def add_card(self, card):
        self.cards_counter[(card.card_type, card.color)] += 1
        self.last_card = card

    def draw(self, window):
        window.addstr(0, 1, "Discard pile")
        if not self.draw_full:
            window.addstr(2, 0, "9  Show/hide")
            return

        r, c = 0, 0
        for color in Color:
            for i, card_type in enumerate((CardType.SUN, CardType.MOON, CardType.KEY)):
                self.cards[(card_type, color)].draw(window, i * 2 + 7 * r, 1 + c * 4)
                window.addstr(4 + c * 4, i * 2 + 7 * r + 1,
                              str(self.cards_counter[(card_type, color)]))
            c += 1 if r == 1 else 0
            r = 0 if r == 1 else r + 1


@dataclass
class KeyDiscard:
    MAX_CARDS: typing.ClassVar[int] = 5
    cards: list[Card] = field(default_factory=list)
    selected: typing.Optional[int] = None
    highlight_keys: bool = False

    def reset(self):
        self.cards = []
        self.selected = None
        self.highlight_keys = False

    def add_card(self, card):
        self.cards.append(card)

    def get_card(self, index=None):
        if index is None:
            index = self.selected
        return self.cards[index]

    def remove_card(self):
        return self.cards.pop()

    def move_card_to(self, index):
        card = self.cards.pop(self.selected)
        self.cards.insert(index, card)

    def all_doors(self):
        for card in self.cards:
            if card.card_type is not CardType.DOOR:
                return False
        return True

    def num_cards(self):
        return len(self.cards)

    def draw(self, window):
        if not self.cards:
            return
        x_offset = 0
        for i, card in enumerate(self.cards):
            if card is None:
                continue
            if i == len(self.cards) - 1:
                x_offset += 3
            if self.selected == i:
                card.draw(window, x_offset + i * 3, 0)
            else:
                card.draw(window, x_offset + i * 3, 1)
            if self.selected != i:
                window.addstr(4, x_offset + i * 3 + 1, str(i + 1))


class Hand:
    MAX_CARDS = 5
    cards = []
    selected = None
    highlight_keys = False

    def __init__(self):
        self.reset()

    def reset(self):
        self.cards = [None for _ in range(self.MAX_CARDS)]
        self.selected = None
        self.highlight_keys = False

    def add_card(self, card):
        index = self.cards.index(None)
        self.cards[index] = card
        return index

    def get_card(self, index=None):
        if index is None:
            index = self.selected
        return self.cards[index]

    def remove_card(self, index=None):
        if index is None:
            index = self.selected
            self.selected = None
        card = self.cards[index]
        self.cards[index] = None
        return card

    def discard_hand(self):
        cards = (card for card in self.cards if card is not None)
        self.cards = [None for _ in range(self.MAX_CARDS)]
        return cards

    def remove_key_and_door(self):
        # Assume that the door is selected
        color = self.cards[self.selected].color
        key_index = -1
        for i, card in enumerate(self.cards):
            if card is not None and card.card_type is CardType.KEY and card.color == color:
                key_index = i
                break
        self.remove_card()
        return self.remove_card(key_index)

    def num_cards(self):
        return self.MAX_CARDS - self.cards.count(None)

    def has_key(self, color):
        for card in self.cards:
            if card and card.card_type is CardType.KEY and card.color == color:
                return True
        return False

    def has_keys(self):
        for card in self.cards:
            if card and card.card_type is CardType.KEY:
                return True
        return False

    def draw(self, window):
        for i, card in enumerate(self.cards):
            if card is None:
                continue
            if self.selected == i or (self.highlight_keys and card.card_type is CardType.KEY):
                card.draw(window, i * 3, 0)
            else:
                card.draw(window, i * 3, 1)
            if self.selected is None or (self.highlight_keys and card.card_type is CardType.KEY):
                window.addstr(4, i * 3 + 1, str(i + 1))


class GameStateEnum(IntEnum):
    NONE = 0
    MAIN1 = 1
    MAIN2 = 2
    DOOR_DRAWN = 3
    NIGHTMARE = 4
    NIGHTMARE_KEY = 5
    NIGHTMARE_DOOR = 6
    KEY_DISCARD1 = 7
    KEY_DISCARD2 = 8
    WON = 9
    LOST1 = 10
    LOST2 = 11


class GameState(ABC):
    state = GameStateEnum.NONE
    message = ""

    @staticmethod
    @abstractmethod
    def process(game, key):
        pass


class Main1State(GameState):
    state = GameStateEnum.MAIN1
    message = \
        """Choose an option 
        1-5 Select a card""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt in range(1, 6):
            game.hand.selected = opt - 1
            return Main2State
        return Main1State


class Main2State(GameState):
    state = GameStateEnum.MAIN2
    message = \
        """Card selected
        1   Add card to the path
        2   Discard card
        6   Select another card""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt == 1:  # Add card to the path
            card = game.hand.get_card()
            success = game.path.add_card(card)
            if success:
                # Put card in the path
                game.hand.remove_card()
                if game.path.has_combo() and game.doors.can_open(card.color):
                    # Open door though combo
                    game.doors.open_door(card.color)
                    game.deck.remove_door(card.color)
                    game.deck.shuffle()
                    game.info = GameInfo.SHUFFLED
                return game.fill_hand()
            else:
                game.hand.selected = None
                game.error = GameError.PATH_SAME_SYMBOL
                return Main1State
        elif opt == 2:  # Discard card
            card = game.hand.remove_card()
            game.discard.add_card(card)
            if card.card_type is CardType.KEY:
                for _ in range(min(game.keydiscard.MAX_CARDS, game.deck.num_cards())):
                    card = game.deck.next()
                    game.keydiscard.add_card(card)
                if game.keydiscard.all_doors():
                    return Lost2State
                game.hand.selected = -1
                return KeyDiscard1State
            else:
                return game.fill_hand()
        elif opt == 6:  # Select another card
            game.hand.selected = None
            return Main1State
        return Main2State


class DoorDrawnState(GameState):
    state = GameStateEnum.DOOR_DRAWN
    message = \
        """You have drawn a DOOR
        1   Use key to open the door
        2   Return door to the deck""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt == 1:
            # Open door through key
            card = game.hand.remove_key_and_door()
            game.discard.add_card(card)
            game.doors.open_door(card.color)
            return game.fill_hand()
        elif opt == 2:
            # Discard the door
            card = game.hand.remove_card()
            game.deck.add_card(card)
            game.deck.shuffle()
            game.info = GameInfo.SHUFFLED
            return game.fill_hand()
        return DoorDrawnState


class NightmareState(GameState):
    state = GameStateEnum.NIGHTMARE
    message = \
        """You have drawn a NIGHTMARE
        1   Discard a key in hand
        2   Discard an open door
        3   Discard your hand
        4   Discard top 5 cards from the deck""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt == 1:
            if game.hand.has_keys():
                game.hand.highlight_keys = True
                return NightmareKeyState
            else:
                game.error = GameError.NO_KEYS
        elif opt == 2:
            return NightmareDoorState
        elif opt == 3:
            game.hand.remove_card()
            cards = game.hand.discard_hand()
            for card in cards:
                game.discard.add_card(card)
            return game.refill_hand()
        elif opt == 4:
            if game.deck.num_cards() >= 5:
                shuffle_cards = []
                for _ in range(5):
                    card = game.deck.next()
                    if card.card_type is not CardType.NIGHTMARE and \
                            card.card_type is not CardType.DOOR:
                        game.discard.add_card(card)
                    else:
                        shuffle_cards.append(card)
                game.shuffle_cards(shuffle_cards)
                game.hand.remove_card()
                return game.fill_hand()
            else:
                game.error = GameError.NO_CARDS
                return NightmareState
        return NightmareState


class NightmareKeyState(GameState):
    state = GameStateEnum.NIGHTMARE_KEY
    message = \
        """Discard a key
        1-5 Choose the key to discard
        6   Select another option""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt in range(1, 6):
            index = opt - 1
            if game.hand.cards[index] and game.hand.cards[index].card_type is CardType.KEY:
                card = game.hand.remove_card(index)
                game.hand.remove_card()
                game.discard.add_card(card)
                game.hand.highlight_keys = False
                return game.fill_hand()
        elif opt == 6:
            game.hand.highlight_keys = False
            return NightmareState
        return NightmareKeyState


class NightmareDoorState(GameState):
    state = GameStateEnum.NIGHTMARE_DOOR
    message = \
        """Discard a door
        1   Discard red door
        2   Discard blue door
        3   Discard green door
        4   Discard yellow door
        6   Select another option""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt in range(1, 5):
            color = Color(opt)
            success = game.doors.close_door(color)
            if success:
                game.hand.remove_card()
                game.deck.add_card(Card(CardType.DOOR, color))
                game.deck.shuffle()
                game.info = GameInfo.SHUFFLED
                return game.fill_hand()
            else:
                game.error = GameError.NO_DOORS
        elif opt == 6:
            return NightmareState
        return NightmareDoorState


class KeyDiscard1State(GameState):
    state = GameStateEnum.KEY_DISCARD1
    message = \
        """You have discarded a key
        1-5 Select a card
        6   Confirm""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt in range(1, 6):
            index = opt - 1
            if index < game.keydiscard.num_cards():
                game.keydiscard.selected = index
                return KeyDiscard2State
        elif opt == 6:
            card = game.keydiscard.remove_card()
            if card.card_type is CardType.DOOR:
                game.keydiscard.add_card(card)
                game.error = GameError.DISCARD_DOOR
            else:
                if card.card_type is not CardType.NIGHTMARE:
                    game.discard.add_card(card)
                while game.keydiscard.num_cards() > 0:
                    card = game.keydiscard.remove_card()
                    game.deck.add_card(card)
                game.hand.selected = None
                return game.fill_hand()
        return KeyDiscard1State


class KeyDiscard2State(GameState):
    state = GameStateEnum.KEY_DISCARD2
    message = \
        """Card selected
        1-5 Choose its new position
        6   Back""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt in range(1, 6):
            index = opt - 1
            if index < game.keydiscard.num_cards():
                game.keydiscard.move_card_to(index)
                game.keydiscard.selected = None
                return KeyDiscard1State
        elif opt == 6:
            game.keydiscard.selected = None
            return KeyDiscard1State
        return KeyDiscard2State


class WonState(GameState):
    state = GameStateEnum.WON
    message = \
        """Congratulations! All doors opened
        1   Play again
        2   Quit""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt == 1:
            game.reset()
            return Main1State
        elif opt == 2:
            exit()
        return WonState


class Lost1State(GameState):
    state = GameStateEnum.LOST1
    message = \
        """Oh no. You've run out of cards!
        1   Play again
        2   Quit""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt == 1:
            game.reset()
            return Main1State
        elif opt == 2:
            exit()
        return Lost1State


class Lost2State(GameState):
    state = GameStateEnum.LOST2
    message = \
        """Oh no. All drawn cards are doors!
        1   Play again
        2   Quit""".splitlines()

    @staticmethod
    def process(game, opt):
        if opt == 1:
            game.reset()
            return Main1State
        elif opt == 2:
            exit()
        return Lost2State


class GameInfo(IntEnum):
    NOTHING = 1
    SHUFFLED = 2


class GameError(IntEnum):
    NOTHING = 1
    PATH_SAME_SYMBOL = 2
    DISCARD_DOOR = 3
    NO_KEYS = 4
    NO_DOORS = 5
    NO_CARDS = 6


@dataclass
class Game:
    n_turn: int = 0
    hand: Hand = field(default_factory=Hand)
    path: Path = field(default_factory=Path)
    deck: Deck = field(default_factory=Deck)
    discard: Discard = field(default_factory=Discard)
    doors: Doors = field(default_factory=Doors)
    keydiscard: KeyDiscard = field(default_factory=KeyDiscard)
    selected: int = -1
    state: typing.Type[GameState] = Main1State
    draw_discard: bool = False
    info: GameInfo = GameInfo.NOTHING
    error: GameError = GameError.NOTHING
    seed: int = field(init=False)

    def __post_init__(self):
        self.seed = random.randrange(16**8)

    def start(self):
        random.seed(self.seed)
        self.deck.shuffle()
        self.refill_hand()
        self.state = Main1State

    def reset(self):
        self.deck.reset()
        self.hand.reset()
        self.path.reset()
        self.discard.reset()
        self.doors.reset()
        self.keydiscard.reset()
        self.seed = random.randrange(16**8)
        self.start()

    def shuffle_cards(self, cards, update_info=True):
        if cards:
            for card in cards:
                self.deck.add_card(card)
            self.deck.shuffle()
            if update_info:
                self.info = GameInfo.SHUFFLED

    def refill_hand(self):
        shuffle_cards = []
        while self.hand.num_cards() != self.hand.MAX_CARDS:
            if not self.deck.num_cards():
                return Lost1State
            card = self.deck.next()
            if card.card_type != CardType.NIGHTMARE and \
                    card.card_type != CardType.DOOR:
                self.hand.add_card(card)
            else:
                shuffle_cards.append(card)

        self.shuffle_cards(shuffle_cards, False)
        return Main1State

    def fill_hand(self):
        shuffle_cards = []
        while self.hand.num_cards() != self.hand.MAX_CARDS:
            if not self.deck.num_cards():
                return Lost1State
            card = self.deck.next()
            index = self.hand.add_card(card)
            if card.card_type is CardType.NIGHTMARE:
                self.shuffle_cards(shuffle_cards)
                self.hand.selected = index
                return NightmareState
            if card.card_type is CardType.DOOR:
                self.hand.selected = index
                if self.hand.has_key(card.color):
                    self.shuffle_cards(shuffle_cards)
                    return DoorDrawnState
                else:
                    card = self.hand.remove_card()
                    shuffle_cards.append(card)

        self.shuffle_cards(shuffle_cards)
        return Main1State

    def check_won(self):
        return self.doors.check_all_open()

    def process(self, key):
        opt = -1
        if key.isdigit():
            opt = int(key)
        elif key == "q":
            exit(0)

        if opt == 9:
            self.discard.draw_full = not self.discard.draw_full

        self.state = self.state.process(self, opt)

        if self.check_won():
            self.state = WonState

        self.n_turn = 0


class UIMessage:
    game = None
    info = {}
    error = {}

    def __init__(self, game):
        self.game = game
        self.populate()

    def populate(self):
        self.info[GameInfo.SHUFFLED] = \
            """Deck has been shuffled"""

        self.error[GameError.PATH_SAME_SYMBOL] = \
            """Repeated symbol"""

        self.error[GameError.DISCARD_DOOR] = \
            """Can't discard a door"""

        self.error[GameError.NO_KEYS] = \
            """You don't have any keys"""

        self.error[GameError.NO_DOORS] = \
            """Not enough doors of that color"""

        self.error[GameError.NO_CARDS] = \
            """There are less than 5 cards in the deck"""

    def draw(self, window):
        message = self.game.state.message
        message_len = len(message)
        for j in range(message_len):
            window.addstr(j, 0, message[j])
        if self.game.info != GameInfo.NOTHING:
            window.addstr(message_len, 0, self.info[self.game.info], curses.color_pair(6))
            self.game.info = GameInfo.NOTHING
        if self.game.error != GameError.NOTHING:
            window.addstr(message_len, 0, self.error[self.game.error], curses.color_pair(2))
            self.game.error = GameError.NOTHING


class UI:
    MIN_X = 70
    MIN_Y = 20
    game = None
    stdscr = None
    ui_message = None
    error = False
    wins = {}

    def __init__(self, game, stdscr):
        self.game = game
        self.stdscr = stdscr
        self.ui_message = UIMessage(game)
        self.set_windows()

    def set_windows(self):
        """

         +-----------------+               +-------------------+
         |     DOORS       |               |                   |
         +-----------------+               |     KEYDISCARD    |
     +-------------------------------------|                   |
     |               PATH                  +-------------------+
     +---------------------------------------------->
         +-----------------+                 +---------------+
         |                 |  +-------+      |               |
         |      HAND       |  | DECK  |      |               |
         |                 |  +-------+      |               |
         +-----------------+                 |    DISCARD    |
                                             |               |
     +---------------------------------------|               |
     |                                       |               |
     |                                       +---------------+
     |              MESSAGE
     |
     |
     +---------------------------------------------->
        """
        try:
            self.wins = [self.stdscr.subwin(3, 65, 4, 2),  # Path
                         self.stdscr.subwin(3, 16, 1, 5),  # Doors
                         self.stdscr.subwin(5, 15, 7, 5),  # Hand
                         self.stdscr.subwin(3, 9, 8, 22),  # Deck
                         self.stdscr.subwin(9, 14, 8, 38),  # Discard
                         self.stdscr.subwin(5, 20, 1, 36),  # Key discard
                         self.stdscr.subwin(7, 60, 13, 1)]  # Message
            self.error = False
        except curses.error:
            self.error = True

    def draw(self):
        def write_error():
            self.stdscr.addstr("This game requires a minimum window size "
                               "of {}x{}\n".format(self.MIN_X, self.MIN_Y))
            self.stdscr.addstr("Please resize the terminal\n")
            self.stdscr.addstr("Or press Control+C to exit")

        self.stdscr.clear()

        if self.error:
            y, x = self.stdscr.getmaxyx()

            if y >= self.MIN_Y and x >= self.MIN_X:
                self.set_windows()

            if self.error:
                write_error()
                return

        for win in self.wins:
            win.clear()

        try:
            self.game.path.draw(self.wins[0])
            self.game.doors.draw(self.wins[1])
            self.game.hand.draw(self.wins[2])
            self.game.deck.draw(self.wins[3])
            self.game.keydiscard.draw(self.wins[5])
            self.ui_message.draw(self.wins[6])
            self.game.discard.draw(self.wins[4])

            self.stdscr.addstr(19, 49, f"Dreamium V{VERSION}", curses.color_pair(6))
            self.stdscr.addstr(19, 1, f"Seed {self.game.seed:#08x}", curses.color_pair(6))
            for win in self.wins:
                win.refresh()
            self.stdscr.refresh()
        except curses.error:
            # Try to recover from an error above
            # This won't always help, but they can just control+c
            for win in self.wins:
                win.clear()
            write_error()


def main(stdscr):
    stdscr.clear()
    stdscr.refresh()
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(False)

    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)

    for i in range(0, curses.COLORS):
        curses.init_pair(i + curses.COLORS + 1, i, 5)

    game = Game()
    game.start()
    ui = UI(game, stdscr)

    while True:
        ui.draw()
        key = stdscr.getkey()
        game.process(key)


curses.wrapper(main)
