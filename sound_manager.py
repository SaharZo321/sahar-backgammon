import pygame


class SoundManager:
    
    @staticmethod
    def play_sound(path: str, volume: float):
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        pygame.mixer.Sound.play(sound)
        