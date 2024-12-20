from abc import ABC, abstractmethod
import math
import time
from typing import Callable, Literal
import pygame
from pygame.event import Event
from config import get_font
from graphics.outline_text import OutlineText
from models import Position

type RelativePosition = Literal["top", "bottom", "left", "right"]


class Element(ABC):
    rect: pygame.Rect
    disabled: bool
    _position: Position
    surface: pygame.Surface
    on_click: Callable[[], None]

    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        pass

    @abstractmethod
    def update(self, events: list[pygame.event.Event]) -> None:
        """
        Updates the element properties. Ususally implemented with is_input_recieved.
        """
        pass

    def click(self, events: list[pygame.event.Event]) -> bool:
        return False

    def is_input_recieved(self) -> bool:
        mouse_position = pygame.mouse.get_pos()
        return not self.disabled and self.rect.collidepoint(mouse_position)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos: Position):
        self._position = pos
        self.rect = self.surface.get_rect(**pos.dump())


class ButtonElement(Element):
    def __init__(
        self,
        font: pygame.font.Font | None = None,
        position: Position = Position(coords=(0, 0)),
        text_input: str = "BUTTON",
        image: pygame.Surface | None = None,
        base_color: pygame.Color = pygame.Color("red"),
        hovering_color: pygame.Color = pygame.Color("white"),
        outline_size: int = 2,
        outline_color: pygame.Color = pygame.Color("black"),
        on_click: Callable[[], None] = lambda: None,
        sound: pygame.mixer.Sound | None = None,
    ) -> None:

        if image is None and font is None:
            raise Exception("Either image or font must be not None")

        self.disabled = False
        self._font = font
        self._base_color = base_color
        self._hovering_color = hovering_color
        self.text_input = text_input
        self._outline_size = outline_size
        self._outline_color = outline_color
        if font is not None:
            self._toggle_text_color(self._base_color)
        self.image = image
        self.surface = image if image is not None else self.surface
        self.position = position
        self.on_click = on_click
        self.sound = sound

    def click(self, events: list[pygame.event.Event]):
        if (
            not any(
                event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                for event in events
            )
            or not self.is_input_recieved()
        ):
            return False

        if self.sound:
            self.sound.play()
        self.on_click()
        return True

    def render(self, screen: pygame.Surface) -> None:
        screen.blit(self.surface, self.rect)

    def _toggle_text_color(self, color: pygame.Color):

        disabled_color = self._base_color // pygame.Color(2, 2, 2)
        color = color if not self.disabled else disabled_color

        if self._outline_size > 0:
            self.surface = OutlineText.get_surface(
                text=self.text_input,
                font=self._font,
                text_color=color,
                outline_color=self._outline_color,
                outline_width=self._outline_size,
            )
        else:
            self.surface = self._font.render(self.text_input, True, color)

    def update(self, events: list[pygame.event.Event]) -> None:
        color = self._hovering_color if self.is_input_recieved() else self._base_color
        if self._font is not None:
            self._toggle_text_color(color)


class BetterButtonElement(ButtonElement):
    def __init__(
        self,
        position: Position = Position(coords=(0, 0)),
        font: pygame.font.Font | None = None,
        text_input: str = "BUTTON",
        image: pygame.Surface | None = None,
        text_color: pygame.Color = pygame.Color("black"),
        text_outline_size: int = 0,
        text_outline_color: pygame.Color = pygame.Color("white"),
        base_color: pygame.Color = pygame.Color("red"),
        hovering_color: pygame.Color = pygame.Color("white"),
        outline_size: int = 3,
        outline_color: pygame.Color = pygame.Color("black"),
        border_radius: int | None = None,
        padding: int = 10,
        on_click: Callable[[], None] = lambda: None,
        sound: pygame.mixer.Sound | None = None,
    ) -> None:

        if image is None and font is None:
            raise Exception("Either image or font must be not None")

        self._border_radius = border_radius
        self.disabled = False
        self.text_color = text_color
        self.text_outline_color = text_outline_color
        self.text_outline_size = text_outline_size
        self._font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.text_input = text_input
        self._outline_size = outline_size
        self.outline_color = outline_color
        self.image = image
        self.sound = sound

        if image is None:
            self._toggle_color(False)
            text_rect = self._text.get_rect(center=(0, 0))
            size = (
                (text_rect.width + padding + font.get_height() / 3),
                text_rect.height + padding,
            )
            self.surface = pygame.Surface(size, flags=pygame.SRCALPHA, depth=32)
        else:
            image_rect = image.get_rect(center=(0, 0))
            size = (image_rect.width + padding), (image_rect.height + padding)
            self.surface = pygame.Surface(size, flags=pygame.SRCALPHA, depth=32)

        self.surface.convert_alpha()
        self.position = position
        self._surface_rect = self.surface.get_rect(topleft=(0, 0))

        if image is None:
            self._text_rect = self._text.get_rect(center=self._surface_rect.center)
        else:
            self._image_rect = image.get_rect(center=self._surface_rect.center)

        self.on_click = on_click

    def render(self, screen: pygame.Surface) -> None:
        br = (
            self._border_radius
            if self._border_radius is not None
            else math.floor(self.rect.height / 4)
        )
        pygame.draw.rect(
            surface=self.surface,
            color=self._displayed_color,
            rect=self._surface_rect,
            border_radius=br,
        )
        pygame.draw.rect(
            surface=self.surface,
            color=self._displayed_outline_color,
            rect=self._surface_rect,
            width=self._outline_size,
            border_radius=br,
        )
        if self.image is None:
            self.surface.blit(self._text, self._text_rect)
        else:
            self.surface.blit(self.image, self._image_rect)

        screen.blit(self.surface, self.rect)

    def _toggle_color(self, is_hovering: bool):
        disabled_color = self.base_color // pygame.Color(2, 2, 2, 1)
        disabled_outline_color = self.outline_color // pygame.Color(2, 2, 2, 1)
        disabled_text_color = self.text_color // pygame.Color(2, 2, 2, 1)
        disabled_text_outline_color = self.text_outline_color // pygame.Color(
            2, 2, 2, 1
        )

        color = self.hovering_color if is_hovering else self.base_color
        self._displayed_color = color if not self.disabled else disabled_color
        self._displayed_outline_color = (
            self.outline_color if not self.disabled else disabled_outline_color
        )

        if self._font is None:
            return

        text_color = self.text_color if not self.disabled else disabled_text_color
        text_outline_color = (
            self.text_outline_color
            if not self.disabled
            else disabled_text_outline_color
        )
        if self.text_outline_size > 0:
            self._text = OutlineText.get_surface(
                text=self.text_input,
                font=self._font,
                text_color=text_color,
                outline_color=text_outline_color,
                outline_width=self.text_outline_size,
            )
        else:
            self._text = self._font.render(self.text_input, True, text_color)

    def update(self, events: list[pygame.event.Event]) -> None:
        self._toggle_color(self.is_input_recieved())


class TrackButtonElement(Element):
    rect: pygame.Rect
    highlighted: bool
    is_top: bool
    surface: pygame.Surface
    surface_rect: pygame.Rect

    def __init__(
        self,
        rect: pygame.Rect,
        is_top: bool,
        surface: pygame.Surface,
        surface_rect: pygame.Rect,
        on_click: Callable[[], None] = lambda: None,
    ) -> None:
        self.rect = rect
        self.is_top = is_top
        self.highlighted = False
        self.surface = surface
        self.surface_rect = surface_rect
        self.disabled = False
        self.on_click = on_click

    def render(self) -> None:

        if self.highlighted:
            padding = 3
            height = 10
            width = self.rect.width - padding * 2
            top = (
                self.rect.top - height - padding
                if self.is_top
                else self.rect.bottom + padding
            )
            active_rect = pygame.Rect(self.rect.left + padding, top, width, height)
            pygame.draw.rect(
                surface=self.surface,
                color=(0, 150, 250),
                rect=active_rect,
                width=0,
                border_radius=2,
            )

    def update(self, events: list[Event]) -> None:
        return super().update(events)

    def is_input_recieved(self) -> bool:
        mouse_position = pygame.mouse.get_pos()

        return mouse_position[0] - self.surface_rect.left in range(
            self.rect.left, self.rect.right
        ) and mouse_position[1] + self.surface_rect.top in range(
            self.rect.top, self.rect.bottom
        )


class SliderElement(Element):
    def __init__(
        self,
        min_value: float,
        max_value: float,
        position: Position = Position(coords=(0, 0)),
        default_value: float | None = None,
        slider_size: tuple[int, int] = (150, 15),
        knob_size: tuple[int, int] = (10, 30),
        slider_surface: pygame.Surface | None = None,
        slider_color: pygame.Color = pygame.Color("white"),
        knob_color: pygame.Color = pygame.Color("white"),
        label: pygame.Surface | ButtonElement = pygame.Surface((0,0)),
        label_position: RelativePosition = "right",
        label_padding: int = 10,
        on_value_changed: Callable[[float, str], None] = lambda x, y: None,
        id: str = "",
        show_value: bool = False,
        step: float = 0,
        sound: pygame.mixer.Sound | None = None,
    ) -> None:
        self.step = step
        self.id: str = id
        self.on_value_change: Callable[[float, str], None] = on_value_changed
        self.min: float = min_value
        self.max: float = max_value
        self.sound = sound
        self._value: float = default_value if default_value is not None else min_value
        self.knob_size = knob_size
        self.slider_height = max(knob_size[1], slider_size[1])
        self.knob_color = knob_color
        self.slider_size = slider_size
        self.disabled = False
        self.show_value = show_value
        self.drag = False
        self.time_hovering = 0
        self._label_position = label_position
        self._position = position
        
        if type(slider_surface) is pygame.Surface:
            self.slider_surface = pygame.transform.scale(slider_surface, slider_size)
        else:
            self.slider_surface = pygame.Surface(slider_size)
            self.slider_surface.fill(slider_color)
            pygame.draw.rect(self.slider_surface, "black", (0, 0) + (slider_size), 2)

        self.label = label
        
        if isinstance(label, ButtonElement):
            self.label = pygame.Surface(
                label.surface.get_size(), flags=pygame.SRCALPHA, depth=32
            )
            self.label.convert_alpha()

        self.label_padding = label_padding if self.label.get_size()[0] else 0
        self.label_position = label_position

        if isinstance(label, ButtonElement):
            label.rect = self._label_rect

        self.slider_color = slider_color
    
    def render(self, surface: pygame.Surface) -> None:
        if self.show_value:
            self._render_value()
        surface.blit(self.slider_surface, self._slider_rect)
        surface.blit(self.label, self._label_rect)
        # render knob based on value
        knob_surface = pygame.Surface(size=self.knob_size)
        knob_center = self._value_to_position(self._value)
        knob_rect = knob_surface.get_rect(center=knob_center)
        pygame.draw.rect(surface, self.knob_color, knob_rect)
        pygame.draw.rect(surface, pygame.Color("black"), knob_rect, width=2)

    def is_input_recieved(self) -> bool:
        mouse_position = pygame.mouse.get_pos()
        return not self.disabled and self._slider_rect.collidepoint(mouse_position)

    def click(self, events: list[pygame.event.Event]):
        if not self.is_input_recieved() or not any(
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            for event in events
        ):
            return False

        mouse_position = pygame.mouse.get_pos()
        self.value = self._position_to_value(mouse_position)
        self.drag = True
        if self.sound:
            self.sound.play()
        return True

    def update(self, events: list[pygame.event.Event]) -> None:
        if not self.is_input_recieved():
            if any(event.type == pygame.MOUSEBUTTONUP for event in events):
                self.drag = False
            return

        if (
            pygame.mouse.get_pressed()[0]
            and self.drag
            and any(event.type == pygame.MOUSEMOTION for event in events)
        ):
            mouse_position = pygame.mouse.get_pos()
            self.value = self._position_to_value(mouse_position)
            return

        mwevents = [event for event in events if event.type == pygame.MOUSEWHEEL]
        for event in mwevents:
            self.value = (
                self.value
                + (self.step if self.step else ((self.max - self.min) / 100)) * event.y
            )

    def render_tooltip(self):
        pass

    def _value_to_position(self, value: float):
        ratio = (value - self.min) / (self.max - self.min)
        centerx = ratio * self._slider_rect.width + self._slider_rect.left
        return (centerx, self._slider_rect.centery)

    def _position_to_value(self, mouse_position: tuple[int, int]):
        ratio = (mouse_position[0] - self._slider_rect.left) / self._slider_rect.width
        return ratio * (self.max - self.min) + self.min

    def _render_value(self):
        value_surface = get_font(self.slider_size[1] - 3).render(
            f"{round(self.value)}", True, "white"
        )
        value_rect = value_surface.get_rect(topleft=(4, 0))
        self.slider_surface.blit(value_surface, value_rect)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value: float):
        new_value = (
            max(new_value, self.min)
            if new_value < self.min
            else min(new_value, self.max)
        )
        if self.step:
            new_value = round(new_value / self.step) * self.step
        self.on_value_change(new_value, self.id)
        self._value = new_value

    @property
    def label_position(self):
        return self._label_position

    @label_position.setter
    def label_position(self, label_position: RelativePosition):
        self._label_position = label_position
        
        label_size = self.label.get_size()
        match label_position:
            case "left" | "right":
                width = self.slider_size[0] + self.label_padding + label_size[0]
                height = max(self.slider_size[1], label_size[1])
                self.rect = pygame.Surface((width, height)).get_rect(**self.position.dump())
            case "top" | "bottom":
                width = max(self.slider_size[0], label_size[0])
                height = self.slider_size[1] + self.label_padding + label_size[1]
                self.rect = pygame.Surface((width, height)).get_rect(**self.position.dump())
        
        match label_position:
            case "left":
                self._label_rect = self.label.get_rect(midleft=self.rect.midleft)
                self._slider_rect = self.slider_surface.get_rect(
                    midright=self.rect.midright
                )
            case "right":
                self._label_rect = self.label.get_rect(midright=self.rect.midright)
                self._slider_rect = self.slider_surface.get_rect(
                    midleft=self.rect.midleft
                )
            case "top":
                self._label_rect = self.label.get_rect(midtop=self.rect.midtop)
                self._slider_rect = self.slider_surface.get_rect(
                    midbottom=self.rect.midbottom
                )
            case "bottom":
                self._label_rect = self.label.get_rect(midbottom=self.rect.midbottom)
                self._slider_rect = self.slider_surface.get_rect(
                    midtop=self.rect.midtop
                )


class TextFieldElement(Element):
    def __init__(
        self,
        font: pygame.font.Font,
        position: Position = Position(coords=(0, 0)),
        width: int = 0,
        default: str = "",
        disabled: bool = True,
        text_align: Literal["right", "left", "center"] = "left",
        on_enter: Callable[[], None] = lambda: None,
        on_value_changed: Callable[[str], None] = lambda x: None,
        sound: pygame.mixer.Sound | None = None,
    ) -> None:
        self.sound = sound
        self.font = font
        self.width = width
        self.disabled = disabled
        self.surface: pygame.Surface = pygame.transform.scale(
            pygame.Surface((1, 1), flags=pygame.SRCALPHA, depth=32),
            (width + 30, font.get_height() + 20),
        )
        self.surface.convert_alpha()
        self.surface_rect = self.surface.get_rect(topleft=(0, 0))
        self.rect = self.surface.get_rect(**position.dump())
        self.max_text_rect = pygame.Surface((width, font.get_height())).get_rect(
            center=self.surface_rect.center
        )
        self.value = default
        self.text_align = text_align
        self.on_enter = on_enter
        self.on_value_changed = on_value_changed

    def is_input_recieved(self) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)

    def update(self, events: list[Event]) -> None:
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.disabled = not self.is_input_recieved()

            if event.type != pygame.KEYDOWN or self.disabled:
                continue

            match event.key:
                case pygame.K_BACKSPACE:
                    # get text input from 0 to -1 i.e. end.
                    self.value = self.value[:-1]
                case pygame.K_RETURN | pygame.K_KP_ENTER:
                    self.on_enter()
                case pygame.K_ESCAPE:
                    self.disabled = True
                case _:
                    # Unicode standard is used for string formation
                    self.value += event.unicode

        self.on_value_changed(self.value)

    def click(self, events: list[pygame.event.Event]):
        if self.is_input_recieved() and any(
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            for event in events
        ):
            if self.sound:
                self.sound.play()
            self.disabled = False
            return True
        elif not self.is_input_recieved() and any(
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            for event in events
        ):
            self.disabled = True

        return False

    def render(self, surface: pygame.Surface) -> None:
        text_to_render = self.value
        long = False
        while self.font.size("..." + text_to_render)[0] > self.max_text_rect.width:
            text_to_render = text_to_render[1:]
            long = True
        if long:
            text_to_render = "..." + text_to_render

        TEXT = self.font.render(text_to_render, True, "black")
        TEXT_RECT = TEXT.get_rect(midleft=self.max_text_rect.midleft)
        match self.text_align:
            case "right":
                TEXT_RECT = TEXT.get_rect(midright=self.max_text_rect.midright)
            case "center":
                TEXT_RECT = TEXT.get_rect(center=self.max_text_rect.center)

        pygame.draw.rect(
            self.surface,
            ("gray" if self.disabled else "white"),
            self.surface_rect,
            0,
            math.floor(self.surface_rect.height / 5),
        )
        pygame.draw.rect(
            self.surface,
            "black",
            self.surface_rect,
            math.floor(self.surface_rect.height / 12),
            math.floor(self.surface_rect.height / 8),
        )
        self.surface.blit(TEXT, TEXT_RECT)

        surface.blit(self.surface, self.rect)


class TimerElement(Element):
    def __init__(
        self,
        font: pygame.font.Font,
        position: Position = Position(coords=(0, 0)),
        timer_type: Literal["sec", "min"] = "min",
        threshold: float = 0,
        color: pygame.Color = pygame.Color("white"),
        threshold_color: pygame.Color = pygame.Color("red"),
        on_done: Callable[[], None] = lambda: None,
        threshold_sound: pygame.mixer.Sound | None = None,
    ) -> None:
        """Time in seconds"""
        self._time = 0
        self._type: Literal["sec", "min"] = timer_type
        self._font = font
        self._position = position
        self._threshold = threshold
        self._color = color
        self._threshold_color = threshold_color
        self._current_time: float = 0
        self.on_done = on_done
        self.surface = self._get_timer_surface(self.format_timer(0, timer_type))
        self.rect = self.surface.get_rect(**position.dump())
        self.disabled = True
        self.threshold_sound = threshold_sound

    def start(self, new_timer: float | None = None):
        if new_timer is not None:
            self.timer = new_timer
        self.disabled = False
        self._current_time = time.time()

    def stop(self):
        self.disabled = True

    def update(self, events: list[Event]) -> None:
        if self.disabled:
            return

        new_time = time.time()
        last_timer = self.timer
        self.timer -= new_time - self._current_time
        self._current_time = new_time

        if (
            last_timer > self._threshold
            and self.timer < self._threshold
            and self.threshold_sound
        ):
            self.threshold_sound.play()

        if self.timer < 0:
            self.timer = 0
            self.stop()
            self.on_done()

    @classmethod
    def format_timer(cls, timer: float, type: Literal["sec", "min"]):
        return (
            f"{round(timer)}"
            if type == "sec"
            else time.strftime("%M:%S", time.gmtime(timer))
        )

    def _get_timer_surface(self, text: str):
        return OutlineText.get_surface(
            text=text,
            font=self._font,
            text_color=(
                self._color if self.timer > self._threshold else self._threshold_color
            ),
            outline_color=pygame.Color("black"),
            outline_width=math.floor(self._font.get_height() / 20),
        )

    def render(self, surface: pygame.Surface) -> None:
        text = self.format_timer(timer=self.timer, type=self._type)

        self.surface = self._get_timer_surface(text)

        self.rect = self.surface.get_rect(**self._position.dump())

        surface.blit(self.surface, self.rect)

    @property
    def timer(self):
        return self._time

    @timer.setter
    def timer(self, time: float):
        self._time = time

    def click(self, events: list[Event]) -> bool:
        return super().click(events)
