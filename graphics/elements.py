import math
from typing import Callable, Literal
import pygame
from pygame.event import Event
from config import get_font
import config
from game_manager import GameManager, SettingsKeys
from graphics.outline_text import OutlineText
from sound_manager import SoundManager


class Element:
    rect: pygame.Rect
    disabled: bool

    def __init__(self) -> None:
        pass
        raise NotImplementedError()

    def render(self, surface: pygame.Surface) -> None:
        pass
        raise NotImplementedError()

    def update(self, events: list[pygame.event.Event]) -> None:
        """
        Updates the element properties. Ususally implemented with is_input_recieved.
        """
        pass

    def click(self):
        pass

    def is_input_recieved(self) -> bool:
        mouse_position = pygame.mouse.get_pos()
        return not self.disabled and self.rect.collidepoint(mouse_position)


class ButtonElement(Element):
    image: pygame.Surface
    position: tuple[int, int]
    disabled: bool
    text_input: str

    _font: pygame.font.Font
    _base_color: pygame.Color
    _hovering_color: pygame.Color
    _text: pygame.Surface
    _outline_size: int
    _outline_color: pygame.Color
    rect: pygame.Rect
    _text_rect: pygame.Rect
    _on_click: Callable[[], None]

    def __init__(
        self,
        position: tuple[int, int],
        font: pygame.font.Font,
        text_input: str = "",
        image: pygame.Surface | None = None,
        base_color: pygame.Color = pygame.Color("red"),
        hovering_color: pygame.Color = pygame.Color("white"),
        outline_size: int = 1,
        outline_color: pygame.Color = pygame.Color("black"),
        on_click: Callable[[], None] = lambda: (),
    ) -> None:

        self.disabled = False

        self.position = position
        self._font = font
        self._base_color = base_color
        self._hovering_color = hovering_color
        self.text_input = text_input
        self._outline_size = outline_size
        self._outline_color = outline_color
        self._toggle_text_color(self._base_color)
        self._text_rect = self._text.get_rect(
            center=(self.position[0], self.position[1])
        )
        self.image = image

        self.update_position(position)
        self._on_click = on_click

    def update_position(self, position: tuple[int, int]):
        if self.image is None:
            self.rect = self._text.get_rect(center=position)
        else:
            self.rect = self.image.get_rect(center=position)

    def click(self):
        SoundManager.play_sound(
            config.BUTTON_SOUND_PATH,
            volume=GameManager.get_setting(SettingsKeys.volume),
        )
        self._on_click()

    def render(self, screen: pygame.Surface) -> None:
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self._text, self._text_rect)

    def toggle(self, disabled: bool | None = None) -> None:
        if disabled is None:
            self.disabled = not self.disabled
        else:
            self.disabled = disabled

    def _toggle_text_color(self, color: pygame.Color):

        disabled_color = self._base_color // pygame.Color(2, 2, 2)
        color = color if not self.disabled else disabled_color

        if self._outline_size > 0:
            self._text = OutlineText.get_surface(
                text=self.text_input,
                font=self._font,
                text_color=color,
                outline_color=self._outline_color,
                outline_width=self._outline_size,
            )
        else:
            self._text = self._font.render(self.text_input, True, color)

    def update(self, events: list[pygame.event.Event]) -> None:
        color = self._hovering_color if self.is_input_recieved() else self._base_color
        if self.image is None:
            self._toggle_text_color(color)

    def get_surface(self):
        if self.image is None:
            return self._text
        return self.image


class BetterButtonElement(ButtonElement):
    image: pygame.Surface | None
    position: tuple[int, int]
    disabled: bool
    text_input: str
    text_color: pygame.Color
    base_color: pygame.Color
    hovering_color: pygame.Color
    text_outline_size: int
    text_outline_color: pygame.Color
    rect: pygame.Rect
    padding: int
    _border_radius: int
    _displayed_color: pygame.Color
    _displayed_outline_color: pygame.Color
    _font: pygame.font.Font
    _text: pygame.Surface
    _outline_size: int
    outline_color: pygame.Color

    _text_rect: pygame.Rect
    _on_click: Callable[[], None]
    surface: pygame.Surface
    _surface_rect: pygame.Rect

    def __init__(
        self,
        position: tuple[int, int],
        font: pygame.font.Font = None,
        text_input: str = "",
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
        on_click: Callable[[], None] = lambda: (),
    ) -> None:

        self._border_radius = border_radius
        self.disabled = False
        self.text_color = text_color
        self.position = position
        self.text_outline_color = text_outline_color
        self.text_outline_size = text_outline_size
        self._font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.text_input = text_input
        self._outline_size = outline_size
        self.outline_color = outline_color
        self.image = image

        if image is None:
            self._toggle_color(False)
            text_rect = self._text.get_rect(center=position)
            scaley = (text_rect.height + padding) / text_rect.height
            scalex = (
                text_rect.width + padding + font.get_height() / 3
            ) / text_rect.width
            self.rect = text_rect.scale_by(scalex, scaley)
        else:
            image_rect = image.get_rect(center=position)
            scaley = (image_rect.height + padding) / image_rect.height
            scalex = (image_rect.width + padding) / image_rect.width
            self.rect = image_rect.scale_by(scalex, scaley)

        self.surface = pygame.Surface(self.rect.size, flags=pygame.SRCALPHA, depth=32)
        self.surface.convert_alpha()
        self._surface_rect = self.surface.get_rect(topleft=(0, 0))

        if image is None:
            self._text_rect = self._text.get_rect(center=self._surface_rect.center)
        else:
            self._image_rect = image.get_rect(center=self._surface_rect.center)

        self._on_click = on_click

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
        if self.image is not None:
            return

        text_color = self.text_color if not self.disabled else disabled_text_color
        text_outline_color = (
            self.text_outline_color
            if not self.disabled
            else disabled_text_outline_color
        )
        if self._outline_size > 0:
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

    def get_surface(self):
        return self.surface


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
        on_click: Callable[[], None] = lambda x: None,
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

    def is_input_recieved(self) -> bool:
        mouse_position = pygame.mouse.get_pos()

        return mouse_position[0] - self.surface_rect.left in range(
            self.rect.left, self.rect.right
        ) and mouse_position[1] + self.surface_rect.top in range(
            self.rect.top, self.rect.bottom
        )


type RelativePosition = Literal["top", "bottom", "left", "right"]


type AnchorPosition = Literal[
    "topleft",
    "bottomleft",
    "topright",
    "bottomright",
    "midtop",
    "midleft",
    "midbottom",
    "midright",
    "center",
]


class SliderElement(Element):
    def __init__(
        self,
        min_value: float,
        max_value: float,
        anchor: dict[AnchorPosition, tuple[int, int]],
        default_value: float | None = None,
        slider_size: tuple[int, int] = (150, 15),
        knob_size: tuple[int, int] = (10, 30),
        slider_surface: pygame.Surface | None = None,
        slider_color: pygame.Color = pygame.Color("white"),
        knob_color: pygame.Color = pygame.Color("white"),
        label: str | pygame.Surface | ButtonElement = "",
        label_position: RelativePosition = "right",
        label_padding: int = 10,
        label_color: pygame.Color = pygame.Color("white"),
        on_value_changed: Callable[[float, str], None] = lambda x: None,
        id: str = "",
    ) -> None:
        self.id: str = id
        self.on_value_changed: Callable[[float, str], None] = on_value_changed
        self.min: float = min_value
        self.max: float = max_value

        self.value: float = default_value if default_value is not None else min_value
        self.knob_size: tuple[int, int] = knob_size
        self.slider_height = max(knob_size[1], slider_size[1])
        self.knob_color = knob_color
        self.slider_size = slider_size
        self.disabled = False

        self.label_padding = label_padding

        if type(slider_surface) is pygame.Surface:
            self.slider_surface = pygame.transform.scale(slider_surface, slider_size)
        else:
            self.slider_surface = pygame.Surface(slider_size)
            self.slider_surface.fill(slider_color)
            pygame.draw.rect(self.slider_surface, "black", (0, 0) + (slider_size), 2)

        if type(label) is str:
            self.label = OutlineText.get_surface(
                text=label,
                font=get_font(math.floor(self.slider_height * 0.8)),
                text_color=label_color,
                outline_color=pygame.Color("black"),
            )
        elif isinstance(label, ButtonElement):
            self.label = pygame.Surface(
                label.get_surface().get_size(), flags=pygame.SRCALPHA, depth=32
            )
            self.label.convert_alpha()
        elif type(label) is pygame.Surface:
            self.label = label

        label_size = self.label.get_size()
        match label_position:
            case "left" | "right":
                width = slider_size[0] + label_padding + label_size[0]
                height = max(slider_size[1], label_size[1])
                self.rect = pygame.Surface((width, height)).get_rect(**anchor)
            case "top" | "bottom":
                width = max(slider_size[0], label_size[0])
                height = slider_size[1] + label_padding + label_size[1]
                self.rect = pygame.Surface((width, height)).get_rect(**anchor)
        self.label_position = label_position
        self.set_elements_position(label_position)

        if isinstance(label, ButtonElement):
            label.rect = self._label_rect

        self.slider_color = slider_color

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.label, self._label_rect)
        surface.blit(self.slider_surface, self._slider_rect)
        surface.blit(self.label, self._label_rect)
        # render knob based on value
        knob_surface = pygame.Surface(size=self.knob_size)
        knob_center = self._value_to_position(self.value)
        knob_rect = knob_surface.get_rect(center=knob_center)
        pygame.draw.rect(surface, self.knob_color, knob_rect)
        pygame.draw.rect(surface, pygame.Color("black"), knob_rect, width=2)

    def is_input_recieved(self) -> bool:
        mouse_position = pygame.mouse.get_pos()
        return not self.disabled and self._slider_rect.collidepoint(mouse_position)

    def click(self):
        print("clicked")
        SoundManager.play_sound(
            config.BUTTON_SOUND_PATH,
            volume=GameManager.get_setting(SettingsKeys.volume),
        )

        if self.is_input_recieved():
            mouse_position = pygame.mouse.get_pos()
            value = self._position_to_value(mouse_position)
            self.set_value(value)

    def update(self, events: list[pygame.event.Event]) -> None:
        mouse_position = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and self.is_input_recieved():
            value = self._position_to_value(mouse_position)
            self.set_value(value)

    def _value_to_position(self, value: float):
        ratio = value / self.max
        centerx = ratio * self._slider_rect.width + self._slider_rect.left
        return (centerx, self._slider_rect.centery)

    def _position_to_value(self, mouse_position: tuple[int, int]):
        ratio = (mouse_position[0] - self._slider_rect.left) / self._slider_rect.width
        return ratio * self.max

    def set_value(self, value: float):
        value = max(value, self.min) if value < self.min else min(value, self.max)
        self.on_value_changed(value, self.id)
        self.value = value

    def set_elements_position(self, position: RelativePosition):

        match position:
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
        anchor: dict[AnchorPosition, tuple[int, int]],
        width: int = 0,
        default: str = "",
        disabled: bool = True,
        text_align: Literal["right", "left", "center"] = "left",
        on_enter: Callable[[], None] = lambda: None,
        on_value_changed: Callable[[str], None] = lambda x: None,
    ) -> None:
        self.font = font
        self.width = width
        self.disabled = disabled
        self.surface: pygame.Surface = pygame.transform.scale(
            pygame.Surface((1, 1), flags=pygame.SRCALPHA, depth=32),
            (width + 30, font.get_height() + 20),
        )
        self.surface.convert_alpha()
        self.surface_rect = self.surface.get_rect(topleft=(0, 0))
        self.rect = self.surface.get_rect(**anchor)
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

    def click(self):
        if self.is_input_recieved():
            self.disabled = False
        else:
            self.disabled = True

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
