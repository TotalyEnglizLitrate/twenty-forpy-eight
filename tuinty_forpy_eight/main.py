#TODO
# work on the colour schemes
# implement a function to update colour along with number
# allow modification of the colour scheme with a command line argument
# add an prompt asking whether to save game state for next launch



from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.containers import Horizontal
from textual.screen import Screen
from textual.css.query import DOMQuery
from textual.color import Color
from textual.widget import Widget
from textual.widgets import Digits, Footer, Label, Markdown

from pathlib import Path
from random import randint, choice, choices
from pickle import dump, load
from math import log2
from argparse import ArgumentParser


scr_fl_path = Path(__file__).parent.joinpath("scr.pkl")
md_fl_path = Path(__file__).parent.joinpath("2048.md")

def not_found(path: Path):
    raise FileNotFoundError(f"File {path.__str__()} not found, make sure you have all the required files, if you don't, try reinstalling or grab them from the github repository")


if scr_fl_path.exists():
    with open(scr_fl_path, 'rb') as scrfl:
        HIGH_SCORE = load(scrfl)
else:
    HIGH_SCORE = 0

parser: ArgumentParser = ArgumentParser(prog = 'tuinty-forpy-eight', description = 'A tui implementation of the "2048" game')
parser.add_argument(
    '-bg', '--background', choices = range(256), nargs = 3, default = (143, 0, 255), required = False
    , type = int
    )

parser.add_argument(
    '-tl', '--tile', choices = range(256), nargs = 3, default = (237, 115, 115), required = False
    , type = int
)

parser.add_argument(
    '-op', '--opacity', choices = [round(x*0.01, 2) for x in range(101)], default = 0.13, required = False, type = float
)

arguments = parser.parse_args()

BACKGROUND_RGB = arguments.background
OPACITY = arguments.opacity
TILE_RGB = arguments.tile


class Help(Screen):

    BINDINGS = [("escape,space,q,question_mark", "pop_screen", "Close")]

    def compose(self) -> ComposeResult:
        yield Markdown(md_fl_path.read_text() if md_fl_path.exists() else not_found())



class GameOver(Label):

    def show(self, score:int, high_score:int) -> None:
        self.update(
            f"Uh oh it seems like you ran out of space :(\n\n\nScore: {score}  High Score: {high_score}"
        )
        if score > high_score:
            with open(scr_fl_path,'wb') as scrfl:
                dump(score, scrfl)
            global HIGH_SCORE
            HIGH_SCORE = score
        self.add_class("visible")

    def hide(self) -> None:
        self.remove_class("visible")



class GameHeader(Widget):
    global HIGH_SCORE
    score = reactive(0)
    high_score = reactive(HIGH_SCORE)

    def compose(self):
        with Horizontal():
            yield Label(self.app.title, id = "app-title")
            yield Label(id = "score")
            yield Label(id = "high_score")

    def watch_score(self, score:int):
        self.query_one("#score", Label).update(f"Score: {score}")

    def watch_high_score(self, high_score:int):
        self.query_one("#high_score", Label).update(f"High Score: {high_score}")


class Cell(Digits):
    def update_with_colour(self, value:str):
        opacity:float = ((log2(int(value) if value else 1)) % 10)*0.05
        self.update(value)
        self.styles.background = Color(TILE_RGB[0], TILE_RGB[1], TILE_RGB[2], opacity)

    def __init__(self, x, y):
        super().__init__("", id = f"cell-{x}-{y}")
        self.update_with_colour("")

    def get_val(self):
        return int(self.value) if self.value else 0


class GameGrid(Widget):
    def __init__(self):
        super().__init__()
        self.styles.background= Color(BACKGROUND_RGB[0], BACKGROUND_RGB[1], BACKGROUND_RGB[2], OPACITY)

    def compose(self) -> ComposeResult:
        for x in range(4):
            for y in range(4):
                yield Cell(x, y)



class Game(Screen):


    BINDINGS = [
        Binding("question_mark,f1", "push_screen('help')", "Help", key_display="?"),
        Binding("r", "reset", "Reset board"),
        Binding("up,w", "move('up')", "Move up"),
        Binding("down,s", "move('down')", "Move down"),
        Binding("left,a", "move('left')", "Move left"),
        Binding("right,d", "move('right')", "Move right"),
        Binding("q", "quit", "Quit")
    ]


    def __init__(self):
        super().__init__()
        self.disabled = True


    def compose(self) -> ComposeResult:
        yield GameHeader()
        yield GameGrid()
        yield Footer()
        yield GameOver()

    def action_reset(self) -> None:
        for x in range(4):
            for y in range(4):
                self.query_one(f"#cell-{x}-{y}", Cell).update_with_colour("")
        self.query_one(GameOver).hide()
        self.query_one(GameHeader).score = 0
        global HIGH_SCORE
        self.query_one(GameHeader).high_score = HIGH_SCORE
        self.query_one(f"#cell-{randint(0, 3)}-{randint(0, 3)}", Cell).update_with_colour("2")
        self.disabled = False



    def cell(self, x, y):
        return self.query_one(f"#cell-{x}-{y}", Cell)


    def action_move(self, direction:str) -> None:

        if self.disabled:
            return

        _grid = [[self.query_one(f"#cell-{x}-{y}", Cell) for y in range(4)] for x in range(4)]
        _grid_vals = [[y.get_val() for y in x] for x in _grid]
        scr = []

        if direction == "up":
            grid = _grid

        elif direction == "down":
            grid = _grid[::-1]

        elif direction == "right":
            grid = [[_grid[x][y] for x in range(4)] for y in range(3, -1, -1)]

        elif direction == "left":
            grid = [[_grid[x][y] for x in range(4)] for y in range(4)]

        del _grid

        for x in range(1, 4):
            for y in range(4):
                for z in range(1, 5-x):
                    if not grid[x-1][y].value:
                        grid[x-1][y].update_with_colour(grid[x][y].value)
                        if x+z < 4:
                            grid[x][y].update_with_colour(grid[x+z][y].value)
                            grid[x+z][y].update_with_colour("")
                        else:
                            grid[x][y].update_with_colour("")

        while any(
            grid[x][y].get_val() and grid[x][y].get_val() == grid[x-1][y].get_val() for x in range(1, 4) for y in range(4)
        ):
            for x in range(1, 4):
                for y in range(4):
                    if grid[x][y].get_val() and grid[x-1][y].get_val() == grid[x][y].get_val():
                        scr.append(grid[x][y].get_val()*2)
                        grid[x-1][y].update_with_colour(str(scr[-1]))
                        grid[x][y].update_with_colour("")
                        for z in range(x, 3):
                            grid[z][y].update_with_colour(grid[z+1][y].value)
                        grid[3][y].update_with_colour("")

        self.query_one(GameHeader).score += sum(scr)


        if self.query_one(GameHeader).score >= self.query_one(GameHeader).high_score:
            self.query_one(GameHeader).high_score = self.query_one(GameHeader).score

        empty_sqrs = [
            (x, y) for x in range(4) for y in range(4) if not self.query_one(f"#cell-{x}-{y}").value
            ]

        if empty_sqrs and _grid_vals != [[self.query_one(f"#cell-{x}-{y}", Cell).get_val() for y in range(4)] for x in range(4)]:
            randx, randy = choice(empty_sqrs)
            self.query_one(f"#cell-{randx}-{randy}", Cell).update_with_colour(choices(("2", "4"), cum_weights = (90, 100))[0])

        elif not empty_sqrs:
            self.disabled = True
            global HIGH_SCORE
            self.query_one(GameOver).show(
                score = self.query_one(GameHeader).score, high_score = HIGH_SCORE
                )


    def on_mount(self) -> None:
        self.action_reset()


class Board(App[None]):

    _CSS_PATH = Path(__file__).parent.joinpath("2048.tcss")

    if not _CSS_PATH.exists():
        not_found(_CSS_PATH)

    CSS_PATH = _CSS_PATH

    SCREENS = {"help": Help}

    TITLE = "A bad implementation of 2048"

    def on_mount(self) -> None:
        self.push_screen(Game())


def main():
        Board().run()



if __name__ == "__main__":
    main()