import pygame


class OutlineText:
    _circle_cache: dict[int, list[tuple[int, int]]] = {}

    screen: pygame.Surface
    position: tuple[int, int]
    text: str
    font: pygame.font.Font
    text_color: pygame.Color
    outline_color: pygame.Color
    outline_width: int

    def __init__(
        self,
        position: tuple[int, int],
        text: str,
        font: pygame.font.Font,
        text_color: pygame.Color = pygame.Color("black"),
        outline_color: pygame.Color = pygame.Color(255, 255, 255),
        outline_width: int = 2,
    ) -> None:
        self.position = position
        self.text = text
        self.font = font
        self.text_color = text_color
        self.outline_color = outline_color
        self.outline_width = outline_width

    @classmethod
    def _circlepoints(cls, radius: float):
        radius = int(round(radius))
        if radius in cls._circle_cache:
            return cls._circle_cache[radius]
        x, y, e = radius, 0, 1 - radius
        cls._circle_cache[radius] = points = []
        while x >= y:
            points.append((x, y))
            y += 1
            if e < 0:
                e += 2 * y - 1
            else:
                x -= 1
                e += 2 * (y - x) - 1
        points += [(y, x) for x, y in points if x > y]
        points += [(-x, y) for x, y in points if x]
        points += [(x, -y) for x, y in points if y]
        points.sort()
        return points

    @classmethod
    def get_surface(
        cls,
        text: str,
        font: pygame.font.Font,
        text_color: pygame.Color = pygame.Color("black"),
        outline_color: pygame.Color = pygame.Color(255, 255, 255),
        outline_width: int = 2,
    ) -> pygame.Surface:
        textsurface = font.render(text, True, text_color).convert_alpha()
        w = textsurface.get_width() + 2 * outline_width
        h = font.get_height()

        osurf = pygame.Surface((w, h + 2 * outline_width)).convert_alpha()
        osurf.fill((0, 0, 0, 0))

        surf = osurf.copy()

        osurf.blit(font.render(text, True, outline_color).convert_alpha(), (0, 0))

        for dx, dy in cls._circlepoints(outline_width):
            surf.blit(osurf, (dx + outline_width, dy + outline_width))

        surf.blit(textsurface, (outline_width, outline_width))
        return surf

    @classmethod
    def render(
        cls,
        surface: pygame.Surface,
        position: tuple[int, int],
        text: str,
        font: pygame.font.Font,
        text_color: pygame.Color = pygame.Color("black"),
        outline_color: pygame.Color = pygame.Color(255, 255, 255),
        outline_width: int = 2,
    ):
        TEXT_SURFACE = cls.get_surface(
            text=text,
            font=font,
            text_color=text_color,
            outline_color=outline_color,
            outline_width=outline_width,
        )

        TEXT_RECT = TEXT_SURFACE.get_rect(center=position)

        surface.blit(TEXT_SURFACE, TEXT_RECT)

        return TEXT_RECT

    def update(self, surface: pygame.Surface):
        OutlineText.render(
            surface=surface,
            text=self.text,
            text_color=self.text_color,
            outline_color=self.outline_color,
            outline_width=self.outline_width,
            position=self.position,
            font=self.font,
        )
