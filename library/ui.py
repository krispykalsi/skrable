import PySimpleGUI as sg
import pygame_gui as gui
import pygame_gui.elements as guiElements
from pygame.rect import Rect
from library.contants import Values
import clipboard
import random
import string


class StartGame:
    def __init__(self):
        self.isHost = None
        self.playerName = None
        self.gameCode = None
        self.isQuit = self.__root()

    def __root(self):
        nameWindow = self.__name()

        while True:
            event, values = nameWindow.read()

            if event == "Exit" or event == sg.WIN_CLOSED:
                print("game exit. ByeBye!")
                nameWindow.close()
                return True
            elif event == 'OK':
                self.playerName = values['-NAME-']
                nameWindow.hide()

            gameModeWindow = self.__gameMode()
            while True:
                event, values = gameModeWindow.read()
                gameModeWindow.Hide()

                if event == '-HOST-':
                    self.isHost = True
                    hostJoinWindow = StartGame.__host()

                    event, values = hostJoinWindow.read()
                    if event == 'Copy':
                        code = self.gameCode = hostJoinWindow['-CODE-'].get()
                        clipboard.copy(code)
                        hostJoinWindow.close()
                        gameModeWindow.close()
                        nameWindow.close()
                        return False
                    elif event == 'Back':
                        hostJoinWindow.close()
                        gameModeWindow.UnHide()
                elif event == '-JOIN-':
                    self.isHost = False
                    hostJoinWindow = StartGame.__join()

                    while True:
                        event, values = hostJoinWindow.read()
                        if event == 'Back' or event == sg.WIN_CLOSED:
                            hostJoinWindow.close()
                            gameModeWindow.UnHide()
                            break
                        elif event == '-CODE-':
                            if len(values['-CODE-']) > 5:
                                values['-CODE-'] = values['-CODE-'][:-1]
                            hostJoinWindow.Element('-CODE-').Update(values['-CODE-'].upper())
                        elif event == '-GO-':
                            self.gameCode = hostJoinWindow['-CODE-'].get()
                            hostJoinWindow.close()
                            gameModeWindow.close()
                            nameWindow.close()
                            return False

                elif event == 'Back' or event == sg.WIN_CLOSED:
                    gameModeWindow.close()
                    nameWindow.UnHide()
                    break

    @staticmethod
    def __name():
        layout = [
            [sg.Text("Welcome to Skrable.", font="any 20")],
            [sg.Text("Please enter your name:")],
            [sg.InputText(key='-NAME-', size=(20, 1))],
            [sg.Column([[sg.Button("OK", font="any 14", bind_return_key=True), sg.Exit(font="any 14")]],
                       justification='right')]
        ]
        return sg.Window('', layout, font="any 17", no_titlebar=True)

    @staticmethod
    def __gameMode():
        layout = [
            [sg.Button('Host Game', key='-HOST-')],
            [sg.Button('Join Game', key='-JOIN-')],
            [sg.Exit("Back")]
        ]
        return sg.Window('', layout, font="any 23", element_justification='right', no_titlebar=True)

    @staticmethod
    def __join():
        layout = [
            [sg.Text('Enter Code')],
            [sg.InputText(key='-CODE-', size=(5, 1), font="any 25", enable_events=True)],
            [sg.Button("Go", key='-GO-', font="any 14", bind_return_key=True), sg.Button('Back', font="any 14")]
        ]
        return sg.Window('', layout, font="any 19", no_titlebar=True, element_justification='center')

    @staticmethod
    def __host():
        code = ''.join((random.choice(string.ascii_uppercase) for _ in range(5)))
        layout = [
            [
                sg.Text('Room Code: '),
                sg.Text(code, text_color="yellow", key='-CODE-'),
                sg.Button('Copy', font="any 14"),
                sg.Button('Back', font="any 14")
            ]
        ]

        return sg.Window('', layout, no_titlebar=True, font="any 19")


class GuessPanel:
    def __init__(self):
        size = Values.SIZE_MAIN_WINDOW
        ratio = (1 - Values.RATIO_DB_TO_MW[0]) / 2

        x = -UI.PADDING_WIN - UI.MARGIN
        y = UI.PADDING_WIN + UI.MARGIN

        width = size[0] * ratio - (UI.PADDING_WIN + 2 * UI.MARGIN)
        height = size[1] - 2 * (UI.PADDING_WIN + UI.MARGIN)

        rect = Rect(0, 0, width, height)
        rect.topright = (x, y)

        self.panel = guiElements.UIPanel(
            object_id="guessPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=UI.manager,
            anchors={
                "left": "right",
                "right": "right",
                "top": "top",
                "bottom": "bottom"
            },
            margins={
                "left": UI.PADDING,
                "top": UI.PADDING,
                "right": UI.PADDING,
                "bottom": UI.PADDING
            }
        )

        rect = Rect((0, 0), (width - 2 * UI.PADDING, 2 * UI.PADDING))
        rect.bottomleft = (0, 0)

        self.guessInput = guiElements.UITextEntryLine(
            object_id="guessInput",
            relative_rect=rect,
            manager=UI.manager,
            container=self.panel,
            anchors={
                "left": "left",
                "right": "right",
                "top": "bottom",
                "bottom": "bottom"
            }
        )

        width -= 2 * UI.PADDING
        height -= 3 * UI.PADDING + self.guessInput.rect.h
        rect = Rect((0, 0), (width, height))

        self.guessBox = guiElements.UITextBox(
            object_id="guessBox",
            html_text="",
            relative_rect=rect,
            manager=UI.manager,
            container=self.panel
        )

        self.guessBox.scroll_bar_width = 3

    def addGuess(self, *guesses):
        self.guessInput.set_text("")

        for guess in guesses:
            self.guessBox.html_text += "<br>" + guess
        self.guessBox.rebuild()

    def disableGuessInput(self):
        self.guessBox.disable()

    def enableGuessInput(self):
        self.guessBox.enable()


class WordPanel:
    def __init__(self):
        size = Values.SIZE_MAIN_WINDOW
        ratio = Values.RATIO_DB_TO_MW[0], (1 - Values.RATIO_DB_TO_MW[1]) * (1 - Values.RATIO_PP)

        x = size[0] * ((1 - ratio[0]) / 2) + UI.MARGIN * 2
        y = UI.PADDING_WIN + UI.MARGIN

        width = size[0] * ratio[0] - (4 * UI.MARGIN)
        height = size[1] * ratio[1] - (UI.PADDING_WIN + 2 * UI.MARGIN)

        rect = Rect(x, y, width, height)
        self.panel = guiElements.UIPanel(
            object_id="wordPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=UI.manager
        )


class PenPanel:
    def __init__(self):
        size = Values.SIZE_MAIN_WINDOW
        ratio = Values.RATIO_DB_TO_MW[0], (1 - Values.RATIO_DB_TO_MW[1]) * Values.RATIO_PP

        x = size[0] * ((1 - ratio[0]) / 2) + UI.MARGIN * 2
        y = - UI.PADDING_WIN - UI.MARGIN

        width = size[0] * ratio[0] - (4 * UI.MARGIN)
        height = size[1] * ratio[1] - (UI.PADDING_WIN + 2 * UI.MARGIN)

        rect = Rect(0, 0, width, height)
        rect.bottomleft = (x, y)

        self.panel = guiElements.UIPanel(
            object_id="penPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=UI.manager,
            anchors={
                "left": "left",
                "right": "left",
                "top": "bottom",
                "bottom": "bottom"
            }
        )


class DrawBoardPanel:
    def __init__(self):
        size = Values.SIZE_MAIN_WINDOW
        ratio = Values.RATIO_DB_TO_MW

        x = Values.POINT_DB[0] - UI.PADDING
        y = Values.POINT_DB[1] - UI.PADDING

        width = size[0] * ratio[0] - (4 * UI.MARGIN)
        height = size[1] * ratio[1] - (UI.PADDING_WIN + 2 * UI.MARGIN)

        rect = Rect(x, y, width, height)

        self.panel = guiElements.UIPanel(
            object_id="drawBoardPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=UI.manager,
            margins={
                "left": UI.PADDING,
                "top": UI.PADDING,
                "right": UI.PADDING,
                "bottom": UI.PADDING
            }
        )


class PlayerPanel:
    def __init__(self):
        size = Values.SIZE_MAIN_WINDOW
        ratio = (1 - Values.RATIO_DB_TO_MW[0]) / 2

        x = UI.PADDING_WIN + UI.MARGIN
        y = UI.PADDING_WIN + UI.MARGIN

        width = size[0] * ratio - (UI.PADDING_WIN + 2 * UI.MARGIN)
        height = size[1] - 2 * (UI.PADDING_WIN + UI.MARGIN)

        rect = Rect(x, y, width, height)

        self.panel = guiElements.UIPanel(
            object_id="playerPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=UI.manager,
        )


class UI:
    SIZE_MW = Values.SIZE_MAIN_WINDOW
    SIZE_DB = Values.SIZE_DRAW_BOARD

    PADDING_WIN = Values.PADDING_WINDOW
    PADDING = Values.PADDING
    MARGIN = Values.MARGINS

    manager: gui.UIManager

    panelPlayer: PlayerPanel
    panelDrawBoard: DrawBoardPanel
    panelGuess: GuessPanel
    panelPen = PenPanel
    panelWord = WordPanel

    @classmethod
    def init(cls):
        cls.manager = gui.UIManager(Values.SIZE_MAIN_WINDOW)

        cls.panelPlayer = PlayerPanel()
        cls.panelDrawBoard = DrawBoardPanel()
        cls.panelGuess = GuessPanel()
        cls.panelPen = PenPanel()
        cls.panelWord = WordPanel()
