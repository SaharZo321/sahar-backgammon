from game_manager import GameManager
from menus.screens import MainScreen

def main():
    GameManager.start()
    MainScreen.start(GameManager.screen, GameManager.clock)
    GameManager.quit()
    
if __name__ == '__main__':
    main()