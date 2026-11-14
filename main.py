import os
import math
import struct
import zlib


WIDTH = 1024
HEIGHT = 1024
SAMPLE = 2
PAPER = "#f7f2e7"
INK = "#1c1a17"
RED = "#b3402e"
BLUE = "#2e5f8a"
GOLD = "#d9a441"
GREEN = "#76b900"
GREY = "#77746e"


FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000",) * 7,
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00110", "00100"),
    ":": ("00000", "00110", "00110", "00000", "00110", "00110", "00000"),
    "'": ("00100", "00100", "00010", "00000", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "•": ("00000", "00100", "01110", "01110", "01110", "00100", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
}


class Canvas:
    def __init__(self):
        self.width = WIDTH * SAMPLE
        self.height = HEIGHT * SAMPLE
        self.stride = self.width * 3
        self.pixels = bytearray(self.stride * self.height)

    @staticmethod
    def color(value):
        value = value.removeprefix("#")
        return bytes(int(value[index:index + 2], 16) for index in (0, 2, 4))

    def rect(self, x, y, width, height, color):
        x0 = max(0, round(x * SAMPLE))
        y0 = max(0, round(y * SAMPLE))
        x1 = min(self.width, round((x + width) * SAMPLE))
        y1 = min(self.height, round((y + height) * SAMPLE))
        if x1 <= x0 or y1 <= y0:
            return
        row = self.color(color) * (x1 - x0)
        for py in range(y0, y1):
            start = py * self.stride + x0 * 3
            self.pixels[start:start + len(row)] = row

    def ellipse(self, cx, cy, rx, ry, color):
        cx, cy, rx, ry = (value * SAMPLE for value in (cx, cy, rx, ry))
        if rx <= 0 or ry <= 0:
            return
        ink = self.color(color)
        for py in range(max(0, int(cy - ry)), min(self.height, int(cy + ry + 1))):
            dy = (py + 0.5 - cy) / ry
            span = rx * math.sqrt(max(0.0, 1.0 - dy * dy))
            x0 = max(0, int(cx - span))
            x1 = min(self.width, int(cx + span + 1))
            row = ink * max(0, x1 - x0)
            start = py * self.stride + x0 * 3
            self.pixels[start:start + len(row)] = row

    def polygon(self, points, color):
        points = [(x * SAMPLE, y * SAMPLE) for x, y in points]
        ink = self.color(color)
        y0 = max(0, int(min(y for _, y in points)))
        y1 = min(self.height, int(max(y for _, y in points)) + 1)
        for py in range(y0, y1):
            scan = py + 0.5
            cuts = []
            for index, (x1, y1p) in enumerate(points):
                x2, y2p = points[(index + 1) % len(points)]
                if (y1p <= scan < y2p) or (y2p <= scan < y1p):
                    cuts.append(x1 + (scan - y1p) * (x2 - x1) / (y2p - y1p))
            cuts.sort()
            for index in range(0, len(cuts) - 1, 2):
                left = max(0, int(cuts[index]))
                right = min(self.width, int(cuts[index + 1]) + 1)
                if right > left:
                    row = ink * (right - left)
                    start = py * self.stride + left * 3
                    self.pixels[start:start + len(row)] = row

    def line(self, x1, y1, x2, y2, color, width=2):
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            self.ellipse(x1, y1, width / 2, width / 2, color)
            return
        px, py = -dy * width / (2 * length), dx * width / (2 * length)
        self.polygon(((x1 + px, y1 + py), (x2 + px, y2 + py),
                      (x2 - px, y2 - py), (x1 - px, y1 - py)), color)

    def outline(self, x, y, width, height, weight, color):
        self.rect(x, y, width, weight, color)
        self.rect(x, y + height - weight, width, weight, color)
        self.rect(x, y + weight, weight, height - 2 * weight, color)
        self.rect(x + width - weight, y + weight, weight, height - 2 * weight, color)

    @staticmethod
    def text_width(text, scale):
        if not text:
            return 0
        return (len(text) * 6 - 1) * scale

    def text(self, text, x, y, scale, color, box, align="left"):
        box_x, box_y, box_width, box_height = box
        measured_width = self.text_width(text, scale)
        measured_height = 7 * scale
        assert all(char in FONT for char in text), f"Unsupported glyph in {text!r}"
        assert measured_width <= box_width, f"Text overflows width: {text!r}"
        assert measured_height <= box_height, f"Text overflows height: {text!r}"
        assert x >= box_x and y >= box_y
        if align == "center":
            x = box_x + (box_width - measured_width) / 2
        elif align == "right":
            x = box_x + box_width - measured_width
        cursor = x
        for char in text:
            for row_index, row in enumerate(FONT[char]):
                for column, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cursor + column * scale, y + row_index * scale,
                                  scale, scale, color)
            cursor += 6 * scale

    def fitted_text(self, text, x, y, preferred, width, height, color, align="left"):
        for scale in range(preferred, 0, -1):
            if self.text_width(text, scale) <= width and 7 * scale <= height:
                self.text(text, x, y, scale, color, (x, y, width, height), align)
                return scale
        raise AssertionError(f"No readable fit for {text!r}")

    def save(self, path):
        raw = bytearray()
        for y in range(HEIGHT):
            raw.append(0)
            upper = (y * 2) * self.stride
            lower = upper + self.stride
            for x in range(WIDTH):
                offset = upper + x * 6
                below = lower + x * 6
                for channel in range(3):
                    raw.append((self.pixels[offset + channel]
                                + self.pixels[offset + 3 + channel]
                                + self.pixels[below + channel]
                                + self.pixels[below + 3 + channel]) // 4)

        def chunk(name, payload):
            body = name + payload
            return (struct.pack(">I", len(payload)) + body
                    + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

        image = (b"\x89PNG\r\n\x1a\n"
                 + chunk(b"IHDR", struct.pack(">2I5B", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
                 + chunk(b"IEND", b""))
        with open(path, "wb") as stream:
            stream.write(image)


def rule(canvas, x1, y, x2, color=INK, width=1):
    canvas.rect(x1, y, x2 - x1, width, color)


def draw_capitol(canvas, x, y):
    canvas.ellipse(x + 33, y + 23, 25, 19, BLUE)
    canvas.rect(x + 7, y + 24, 52, 18, PAPER)
    canvas.rect(x + 5, y + 23, 56, 4, INK)
    for column in (13, 25, 37, 49):
        canvas.rect(x + column, y + 27, 3, 14, INK)
    canvas.rect(x + 2, y + 41, 62, 6, INK)
    canvas.rect(x + 6, y + 47, 54, 4, BLUE)
    canvas.rect(x + 32, y + 5, 2, 4, INK)
    canvas.ellipse(x + 33, y + 3, 2, 2, INK)


def draw_flags(canvas, x, y):
    canvas.rect(x + 3, y + 4, 2, 58, INK)
    canvas.rect(x + 39, y + 4, 2, 58, INK)
    canvas.rect(x + 5, y + 6, 28, 12, BLUE)
    canvas.rect(x + 5, y + 18, 28, 12, GOLD)
    canvas.rect(x + 41, y + 6, 28, 24, BLUE)
    for index in range(8):
        angle = 2 * math.pi * index / 8
        canvas.ellipse(x + 55 + math.cos(angle) * 7,
                       y + 18 + math.sin(angle) * 7, 2, 2, GOLD)


def draw_ship(canvas, x, y):
    canvas.polygon(((x + 4, y + 47), (x + 67, y + 47),
                    (x + 56, y + 59), (x + 17, y + 59)), GREY)
    canvas.rect(x + 20, y + 35, 29, 12, INK)
    canvas.rect(x + 28, y + 25, 13, 10, GREY)
    canvas.rect(x + 33, y + 12, 2, 16, INK)
    canvas.line(x + 26, y + 13, x + 43, y + 13, INK, 2)
    canvas.line(x + 34, y + 13, x + 27, y + 20, INK, 1)
    canvas.line(x + 34, y + 13, x + 42, y + 20, INK, 1)
    canvas.ellipse(x + 15, y + 22, 4, 3, GREY)
    canvas.ellipse(x + 21, y + 19, 5, 4, GREY)
    canvas.ellipse(x + 27, y + 23, 4, 3, GREY)
    canvas.polygon(((x + 26, y + 4), (x + 34, y + 1),
                    (x + 43, y + 4), (x + 34, y + 6)), INK)
    canvas.line(x + 34, y + 3, x + 34, y + 10, INK, 1)


def draw_radar(canvas, x, y):
    canvas.rect(x + 33, y + 31, 4, 30, INK)
    canvas.rect(x + 23, y + 60, 24, 4, INK)
    canvas.ellipse(x + 35, y + 22, 18, 14, BLUE)
    canvas.ellipse(x + 35, y + 22, 11, 8, PAPER)
    canvas.line(x + 35, y + 22, x + 49, y + 12, INK, 3)
    for radius in (25, 35):
        points = []
        for step in range(13):
            angle = math.radians(205 + step * 10)
            points.append((x + 35 + radius * math.cos(angle),
                           y + 25 + radius * math.sin(angle)))
        for first, second in zip(points, points[1:]):
            canvas.line(*first, *second, BLUE, 1.5)


def draw_chip(canvas):
    left, top, size = 706, 235, 208
    for offset in range(17, size - 12, 28):
        canvas.rect(left + offset, top - 13, 9, 14, INK)
        canvas.rect(left + offset, top + size - 1, 9, 14, INK)
        canvas.rect(left - 13, top + offset, 14, 9, INK)
        canvas.rect(left + size - 1, top + offset, 14, 9, INK)
    canvas.rect(left, top, size, size, INK)
    canvas.rect(left + 25, top + 25, size - 50, size - 50, PAPER)
    canvas.rect(left + 40, top + 40, size - 80, size - 80, GREEN)
    crack = ((left + 55, top + 40), (left + 67, top + 58),
             (left + 62, top + 70), (left + 88, top + 84),
             (left + 80, top + 97), (left + 110, top + 110),
             (left + 101, top + 123), (left + 132, top + 137),
             (left + 124, top + 150), (left + 168, top + 168))
    for start, end in zip(crack, crack[1:]):
        canvas.line(*start, *end, RED, 5.5)
    canvas.line(left + 88, top + 84, left + 104, top + 75, RED, 5.5)
    canvas.line(left + 104, top + 75, left + 114, top + 60, RED, 5.5)
    canvas.rect(713, 429, 194, 27, INK)
    canvas.line(720, 453, 899, 431, RED, 4)
    canvas.text("J. HUANG, CEO", 719, 435, 2, PAPER, (719, 433, 182, 18), "center")


def draw_laptop(canvas):
    canvas.rect(65, 807, 73, 43, INK)
    canvas.rect(70, 812, 63, 33, BLUE)
    canvas.ellipse(101, 827, 12, 13, PAPER)
    canvas.ellipse(96, 823, 1.7, 1.7, INK)
    canvas.ellipse(106, 823, 1.7, 1.7, INK)
    canvas.polygon(((90, 828), (101, 825), (112, 828),
                    (110, 834), (101, 837), (92, 834)), INK)
    canvas.polygon(((62, 851), (141, 851), (151, 858), (57, 858)), INK)
    canvas.ellipse(75, 858, 7, 4, GOLD)
    canvas.ellipse(91, 858, 7, 4, GOLD)
    canvas.ellipse(107, 858, 7, 4, GOLD)


def render():
    canvas = Canvas()
    canvas.rect(0, 0, WIDTH, HEIGHT, PAPER)
    canvas.outline(16, 16, 992, 992, 6, INK)
    canvas.outline(28, 28, 968, 968, 2, INK)

    canvas.text("LATE CITY EDITION", 48, 44, 2, INK, (48, 44, 360, 15))
    canvas.text("THE WORLD IN ONE PAGE", 48, 44, 2, INK, (48, 44, 928, 15), "right")
    rule(canvas, 48, 65, 976, INK, 1)

    canvas.text("THE DAILY RECORD", 48, 80, 9, INK, (48, 80, 928, 64), "center")
    rule(canvas, 48, 150, 976, RED, 5)
    rule(canvas, 48, 158, 976, INK, 2)

    rule(canvas, 48, 170, 976, INK, 1)
    canvas.text("FRIDAY 13 NOVEMBER 2026", 48, 175, 4, INK, (48, 175, 928, 29), "center")
    rule(canvas, 48, 208, 976, INK, 1)

    canvas.text("TECHNOLOGY", 58, 229, 2, RED, (58, 229, 520, 16))
    canvas.fitted_text("NVIDIA CHIEF", 58, 250, 6, 520, 44, INK)
    canvas.fitted_text("HUANG RESIGNS", 58, 298, 6, 520, 44, INK)
    rule(canvas, 58, 352, 166, INK, 2)
    lead_caption = (
        "JENSEN HUANG RESIGNS AS PRESIDENT,",
        "CEO AND BOARD MEMBER AT ONCE.",
        "CFO COLETTE KRESS TAKES OVER",
        "AS INTERIM CHIEF EXECUTIVE.",
    )
    for index, line in enumerate(lead_caption):
        canvas.fitted_text(line, 58, 365 + index * 17, 2, 530, 15, INK)
    draw_chip(canvas)
    rule(canvas, 48, 474, 976, INK, 4)

    stories = (
        {
            "x": 58, "y": 500, "icon": draw_capitol, "ix": 421, "iy": 504,
            "kicker": "WASHINGTON",
            "headline": ("SENATE SUMMONS", "HUANG & LUTNICK"),
            "caption": ("THE SENATE BANKING COMMITTEE",
                        "CALLS BOTH MEN TO TESTIFY."),
        },
        {
            "x": 528, "y": 500, "icon": draw_flags, "ix": 887, "iy": 500,
            "kicker": "DIPLOMACY",
            "headline": ("EUROPE JOINS", "UKRAINE TALKS"),
            "caption": ("RUSSIA AGREES EUROPE WILL JOIN",
                        "THE NEXT ROUND OF PEACE TALKS."),
        },
        {
            "x": 58, "y": 643, "icon": draw_ship, "ix": 421, "iy": 647,
            "kicker": "THE BALTIC",
            "headline": ("DRONE HITS", "RUSSIAN WARSHIP"),
            "caption": ("UKRAINIAN DRONE STRIKES A SHIP",
                        "IN THE GULF OF FINLAND."),
        },
        {
            "x": 528, "y": 643, "icon": draw_radar, "ix": 887, "iy": 647,
            "kicker": "MIDDLE EAST",
            "headline": ("IRAN CLAIMS", "RADAR STRIKE"),
            "caption": ("TEHRAN SAYS IT STRUCK A US",
                        "RADAR SITE IN BAHRAIN."),
        },
    )
    for story in stories:
        x, y = story["x"], story["y"]
        canvas.text(story["kicker"], x, y, 2, RED, (x, y, 345, 16))
        canvas.fitted_text(story["headline"][0], x, y + 19, 4, 350, 29, INK)
        canvas.fitted_text(story["headline"][1], x, y + 48, 4, 350, 29, INK)
        canvas.fitted_text(story["caption"][0], x, y + 83, 2, 440, 16, INK)
        canvas.fitted_text(story["caption"][1], x, y + 101, 2, 440, 16, INK)
        story["icon"](canvas, story["ix"], story["iy"])

    canvas.rect(511, 491, 1, 288, INK)
    rule(canvas, 48, 636, 976, INK, 1)
    rule(canvas, 48, 779, 976, INK, 2)

    rule(canvas, 48, 795, 976, INK, 1)
    draw_laptop(canvas)
    canvas.fitted_text("FBI BLAMES N. KOREA", 166, 806, 3, 448, 23, INK)
    canvas.fitted_text("FOR $400M CRYPTO HACK", 166, 832, 3, 448, 23, INK)
    canvas.fitted_text("HACKERS USED FAKE VIDEO", 636, 814, 2, 322, 16, INK)
    canvas.fitted_text("CALLS TO TRICK STAFF.", 636, 836, 2, 322, 16, INK)
    rule(canvas, 48, 869, 976, INK, 1)

    canvas.text("IN BRIEF", 48, 886, 2, RED, (48, 886, 928, 15), "center")
    canvas.text("RECORD 483,200 US DEPORTATIONS • KANE'S 126TH ENGLAND CAP",
                48, 910, 2, INK, (48, 910, 928, 16), "center")
    canvas.text("CHINA'S PACIFIC DRILLS", 48, 934, 2, INK, (48, 934, 928, 16), "center")
    return canvas


def main():
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    render().save(os.path.join(output_dir, "entry.png"))


if __name__ == "__main__":
    main()
