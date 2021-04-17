import pygame
import time
from library.network import Client
from library.contants import Colors, Values
from threading import Thread


# TODO - disconnect/exit implementation

class Pen:
    INK = 0
    ERASE = 1

    def __init__(self, size, color, mode=INK):
        self.size = size
        self.color = color
        self.mode = mode


class DrawBoard:
    def __init__(self, window: pygame.Surface, brushSizes, brushColors):
        self.window = window
        self.brushSizes = brushSizes
        self.brushColors = brushColors
        self.pen = Pen(brushSizes[0], brushColors[0])
        self.last_position = None
        self.isDrawing = False

        self.window.fill(Colors.WHITE)

    def draw(self, start, end):
        s = [x - y for x, y in zip(start, Values.POINT_DB)]
        e = [x - y for x, y in zip(end, Values.POINT_DB)]

        pygame.draw.line(
            surface=self.window,
            color=self.pen.color,
            start_pos=s,
            end_pos=e,
            width=self.pen.size
        )

    def setModeToInk(self):
        self.pen.mode = Pen.INK

    def setModeToEraser(self):
        self.pen.mode = Pen.ERASE

    def clearBoard(self):
        self.window.fill(Colors.WHITE)


class Game(Client):
    def __init__(self, name, code, isHost, drawBoard):
        super().__init__()

        self.drawBoard = drawBoard
        self.__game = {
            "name": name,
            "opponent": "",
            "code": code,
            "type": "host" if isHost else "join",
            "word": "",
            "pendingCoordinates": [],
            "pendingGuesses": [],
            "isDrawing": False,
            "exitCode": self.SUCCESS
        }

        self.__isTurn = isHost
        self.__wordChoices = []
        self.guesses = []
        self.wordChosen = False

    @property
    def playerName(self):
        return self.__game["name"]

    @property
    def opponentName(self):
        return self.__game["opponent"]

    @property
    def wordChoices(self):
        return self.__wordChoices

    @property
    def word(self):
        return self.__game["word"]

    @word.setter
    def word(self, new):
        self.wordChosen = True
        self.__game["word"] = new

    @property
    def isDrawing(self):
        return self.__game["isDrawing"]

    @isDrawing.setter
    def isDrawing(self, new):
        self.__game["isDrawing"] = new

    @property
    def gameCode(self):
        return self.__game['code']

    @gameCode.setter
    def gameCode(self, new):
        self.__game['code'] = new

    @property
    def isTurn(self):
        return self.__isTurn

    @isTurn.setter
    def isTurn(self, new):
        self.__game['type'] = "host" if new else "join"
        self.__isTurn = new

    @property
    def playerType(self):
        return self.__game['type']

    @property
    def pendingCoordinates(self):
        return self.__game["pendingCoordinates"]

    @property
    def pendingGuesses(self):
        return self.__game["pendingGuesses"]

    def addToPendingGuesses(self, guess):
        self.guesses.append(guess)
        self.__game["pendingGuesses"].append(guess)

    def addToPendingCoordinates(self, coordinate):
        if not self.__game["pendingCoordinates"]:
            self.__game["pendingCoordinates"].append(self.drawBoard.last_position)
        self.__game["pendingCoordinates"].append(coordinate)

    def __sendDrawBoard(self):
        while True:
            self._sendMsg(self.__game)
            self.__game["pendingCoordinates"].clear()

            newGuesses = self._receiveMsg()

            if newGuesses == self.EXIT:
                break

            self.guesses.extend(newGuesses)
            self.__game["pendingGuesses"].extend(newGuesses)

            time.sleep(self.interval)

    def __receiveDrawBoard(self):
        while True:
            self._sendMsg(self.__game)
            self.__game["pendingGuesses"].clear()

            msg = self._receiveMsg()

            if msg:
                if msg == self.EXIT:
                    break

                isDrawing, pendingCoordinates = msg
                self.__game["pendingCoordinates"].extend(pendingCoordinates)
                self.drawBoard.isDrawing = self.isDrawing

            time.sleep(self.interval)

    def __receiveWord(self):
        self.word = self._receiveMsg()
        print(self.word)

    def __sendWord(self):
        while not self.wordChosen:
            pass

        print("sending word", self.word)
        self._sendMsg(self.word)
        print("sent")

    def run(self):
        if self.isTurn:
            self.__sendDrawBoard()
        else:
            self.__receiveDrawBoard()

        print("Game InActive")

    def newGame(self):
        self._establishConnection()

        playerType = "host" if self.isTurn else "join"
        self._sendMsg({"code": self.gameCode, "name": self.playerName, "type": playerType, "exitCode": self.SUCCESS})
        msg = self._receiveMsg()
        if msg == self.SUCCESS:
            print(f"game {playerType}ed")
            print("Code:", self.gameCode)

            Thread(name="setupGame", target=self.__setupGame, daemon=True).start()

            return True
        elif msg == self.FAIL:
            print(f"game {playerType}ing failed")
        else:
            print("findGame() ->", msg)

        return False

    def __setupGame(self):
        if self.isTurn:
            joinName = self._receiveMsg()
            if joinName:
                self.__game["opponent"] = joinName
                wc = self.__wordChoices = self._receiveMsg()
                print("received:", wc)
            else:
                print("error setting up host")
            self.__sendWord()
        else:
            hostName = self._receiveMsg()
            if hostName:
                self.__game["opponent"] = hostName
            else:
                print("error setting up host")
            print("waiting for word")
            self.__receiveWord()

    def __del__(self):
        msg = {
            "code": self.gameCode,
            "type": self.playerType,
            "exitCode": self.DISCONNECT
        }
        self._sendMsg(msg)
        msg = self._receiveMsg()
        if msg == self.SUCCESS:
            print("\nSuccessfully closed at Server")
        else:
            print("\nFailed to close at Server")
        super().__del__()


class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
