import pygame
import pygame_gui as gui
from library.contants import Values, Colors
from library.elements import DrawBoard, Game, Player
from library.ui import StartGame, UI

menu = StartGame()

if menu.isQuit:
    exit(0)

pygame.init()
pygame.display.set_caption("skrable")

mainWindow = pygame.display.set_mode(UI.SIZE_MW)
clock = pygame.time.Clock()

drawBoard = DrawBoard(
    window=pygame.surface.Surface(UI.SIZE_DB),
    brushSizes=Values.SIZE_BRUSHES,
    brushColors=Colors.getAllColors()
)

ui = UI()
game = Game(menu.playerName, menu.gameCode, menu.isHost, drawBoard)
player = Player(game.playerName)
opponent = Player(game.opponentName)


def isQuit(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        exit(0)


def update(dt, blitDrawBoard):
    ui.panelWord.updateTimer()

    ui.manager.update(dt)
    ui.manager.draw_ui(mainWindow)

    mainWindow.blit(drawBoard.window, Values.POINT_DB) if blitDrawBoard else ...

    pygame.display.update()


def waitForPlayerLoop():
    for event in pygame.event.get():
        isQuit(event)
        ui.manager.process_events(event)

    if game.opponentName:
        return False

    return True


def chooseWordLoop():
    for event in pygame.event.get():
        isQuit(event)

        if event.type == pygame.USEREVENT:
            if event.user_type == gui.UI_BUTTON_PRESSED:
                objID = event.ui_object_id.split(".")

                if objID[0] == "textOverlay":
                    game.word = event.ui_element.text
                    return False

        ui.manager.process_events(event)

    return True


def waitWordLoop():
    for event in pygame.event.get():
        isQuit(event)
        ui.manager.process_events(event)

    if game.wordChosen:
        print("word chosen")
        return False

    return True


def drawLoop():
    with game.lock:
        pg = game.pendingGuesses
        isCorrect = False
        for guess in pg:
            if ui.addGuessAndCheckCorrect(guess, opponent):
                isCorrect = True
            pg.pop(0)

        if isCorrect:
            return False

    for event in pygame.event.get():
        isQuit(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            buttons = pygame.mouse.get_pressed(3)
            if buttons[0]:
                drawBoard.setModeToInk()
                if drawBoard.last_position is None:
                    drawBoard.last_position = pygame.mouse.get_pos()
                drawBoard.isDrawing = True
            elif buttons[1]:
                drawBoard.setModeToEraser()
                if drawBoard.last_position is None:
                    drawBoard.last_position = pygame.mouse.get_pos()
                drawBoard.isDrawing = True

        if drawBoard.isDrawing and event.type == pygame.MOUSEMOTION:
            pos = pygame.mouse.get_pos()
            game.addToPendingCoordinates(pos)

            drawBoard.draw(drawBoard.last_position, pos)
            drawBoard.last_position = pos

        if event.type == pygame.MOUSEBUTTONUP:
            drawBoard.last_position = None
            drawBoard.isDrawing = False

        ui.manager.process_events(event)

    if ui.panelWord.isTimeUp():
        game.setRoundInactive()
        return False

    return True


def guessLoop():
    with game.lock:
        pc = game.pendingCoordinates
        if len(pc) > 1:
            for i in range(len(pc)-1):
                drawBoard.draw(pc[0], pc[1])
                pc.pop(0)

        if pc and not drawBoard.isDrawing:
            pc.clear()

    for event in pygame.event.get():
        isQuit(event)

        if event.type == pygame.USEREVENT:
            if event.user_type == gui.UI_TEXT_ENTRY_FINISHED:
                if event.ui_object_id == "guessPanel.guessInput" and event.text:
                    guess = event.text.strip().lower()
                    game.addToPendingGuesses(guess)
                    if ui.addGuessAndCheckCorrect(guess, player):
                        return False

        ui.manager.process_events(event)

    if ui.panelWord.isTimeUp():
        game.setRoundInactive()
        return False

    return True


def run(loop, blitDrawBoard=True):
    flag = True
    while flag:
        delta_time = clock.tick(Values.FRAMERATE) / 1000.0
        flag = loop()
        update(delta_time, blitDrawBoard)


if __name__ == '__main__':
    proceededToSetup = game.newGame(rounds=2, timePerRound=10) if game.isTurn else game.newGame()

    if not proceededToSetup:
        exit()

    ui.panelGuess.disableGuessInput()

    ui.panelDrawBoard.setOneLinerText(UI.WAITING_FOR_PLAYER)
    ui.panelDrawBoard.showTextOverlay()
    run(waitForPlayerLoop, blitDrawBoard=False)
    ui.panelDrawBoard.hideTextOverlay()

    opponent.name = game.opponentName

    if not game.isTurn:
        ui.panelPlayer.addPlayer(opponent)
        ui.panelPlayer.addPlayer(player)
        game.addPlayers(opponent, player)
    else:
        ui.panelPlayer.addPlayer(player)
        ui.panelPlayer.addPlayer(opponent)
        game.addPlayers(player, opponent)

    ui.panelPlayer.showRoundLabel()
    ui.panelDrawBoard.setOneLinerText(UI.CHOOSING_WORD)

    for _ in range(game.rounds * 2):
        game.setRoundActive()
        ui.panelGuess.disableGuessInput()

        if game.isTurn:
            while not game.wordChoices:
                pass

            ui.panelDrawBoard.showTextOverlay(game.wordChoices)
            run(chooseWordLoop, blitDrawBoard=False)
            ui.panelDrawBoard.hideTextOverlay()

            ui.panelWord.setWord(game.word, isHost=True)
            ui.panelWord.startTimer(game.roundTime)

            if not game.is_alive():
                game.start()

            run(drawLoop)
        else:
            ui.panelDrawBoard.showTextOverlay()
            run(waitWordLoop, blitDrawBoard=False)
            ui.panelDrawBoard.hideTextOverlay()

            ui.panelGuess.enableGuessInput()

            ui.panelWord.setWord(game.word, isHost=False)
            ui.panelWord.startTimer(game.roundTime)

            if not game.is_alive():
                game.start()

            run(guessLoop)

        drawBoard.clearBoard()
        game.calculateScore(*[int(time) for time in ui.panelWord.currentTime.split(':')])
        ui.endRound()

        while game.isRoundActive:
            pass

    print("Game finished. Thanks for playing!")
