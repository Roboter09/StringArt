from re import M
from PIL import Image, ImageOps
import math
from collections import deque
from queue import PriorityQueue


class StringArt:
    def __init__(self, nails, input_image, resolution=0.7):
        if type(input_image) == str:
            self.image = self.load_image(input_image)
            # self.emptyImage = self.load_image(input_image.split(".")[0] + "_empty." + input_image.split(".")[1])
        else:
            self.image = input_image
        self.scale = resolution
        self.image = self.image.resize((round(self.image.width * self.scale), round(self.image.height * self.scale)),
                                       Image.Resampling.LANCZOS)
        # self.emptyImage = self.emptyImage.resize(
        #    (round(self.emptyImage.width * self.scale), round(self.emptyImage.height * self.scale)),
        #    Image.Resampling.LANCZOS)
        self.nails = nails
        self.radius = min(self.image.height, self.image.width) * 0.49
        self.midx = self.image.width / 2
        self.midy = self.image.height / 2
        self.operations = []
        # self.invert()

    def load_image(self, path):
        image = Image.open(path).convert("L")  # Convert to grayscale
        return image

    def nailToCoordinate(self, nail):
        # from polar coordinates
        return round(self.midx + self.radius * math.cos(2 * math.pi * (nail / self.nails))), round(
            self.midy + self.radius * math.sin(2 * math.pi * nail / self.nails))

    def getLine(self, start, end):
        p0 = self.nailToCoordinate(start)
        p1 = self.nailToCoordinate(end)
        sum = [0.0, 0.1]

        def pixel(img, p, color, transparency):
            sum[0] += transparency * img.getpixel(p)
            sum[1] += transparency

        self.bresenham(p0, p1, 20, 1, pixel)
        return sum[0] / sum[1]

    def getDarkestLineFromNail(self, nail, lastNails):
        darkest = (0, 0)
        for n in range(self.nails):
            if n == nail:
                continue
            if n in lastNails:
                continue
            sum = self.getLine(nail, n)
            if sum >= darkest[0]:
                darkest = (sum, n)
        return darkest[1]

    def getLineBrightnesses(self):
        l = []
        for a in range(self.nails):
            for b in range(a + 1, self.nails):
                l.append([(a, b), self.getLine(a, b)])
        return l

    def drawLine(self, start, end, color=20, alpha_correction=1, function=None):
        p0 = self.nailToCoordinate(start)
        p1 = self.nailToCoordinate(end)
        self.bresenham(p0, p1, color, alpha_correction, function)
        self.operations.append((start, end))

    def tryChange(self, start, end, color=20, transparency=1, function=None):
        self.pending_img = self.image.copy()
        self.bresenham(start, end, color, transparency, function)
        self.pending_operation = (start, end)

        return self.pending_img

    def acceptChange(self):
        self.image = self.pending_img
        self.operations.append(self.pending_operation)

    def invert(self):
        self.image = ImageOps.invert(self.image)

    def bresenham(self, p0, p1, color=20, transparency=1, function=None):
        def meta(img, p, switch, color=20, transparency=1, function=None):
            if function is None:
                def function(img, p, color=20, transparency=1):
                    oldColor = img.getpixel(p)
                    img.putpixel(p, round(oldColor * (1 - transparency) + color * transparency))
                    # self.emptyImage.putpixel(p, round(oldColor * (1 - transparency) + color * transparency))

            if switch:
                p = (p[1], p[0])

            function(img, p, color, transparency)

        img = self.image

        if p0[1] == p1[1]:
            y = p0[1]
            for x in range(p0[0], p1[0] + 1):
                meta(img, (x, y), False, color, transparency, function)
        elif p0[0] == p1[0]:
            x = p0[0]
            for y in range(min(p0[1], p1[1]), max(p0[1], p1[1])):
                meta(img, (x, y), False, color, transparency, function)
        else:
            # o.b.d.a Sei p0.x<=p1.x
            if p0[0] > p1[0]:
                p0, p1 = p1, p0

            anstieg = (p1[1] - p0[1]) / (p1[0] - p0[0])

            if anstieg == 1:
                y = p0[1]
                for x in range(p0[0], p1[0] + 1):
                    meta(img, (x, y), False, color, transparency, function)
                    y += 1
            elif anstieg == -1:
                y = p0[1]
                for x in range(p0[0], p1[0] + 1):
                    meta(img, (x, y), False, color, transparency, function)
                    y -= 1
            else:
                switch = True
                if -1 < anstieg < 1:
                    switch = False
                else:
                    p0 = (p0[1], p0[0])
                    p1 = (p1[1], p1[0])

                    # o.b.d.a Sei q0.x<=q1.x
                    if p0[0] > p1[0]:
                        p0, p1 = p1, p0

                anstieg = (p1[1] - p0[1]) / (p1[0] - p0[0])

                if 0 < anstieg < 1:
                    y = p0[1]
                    error = 0
                    for x in range(p0[0], p1[0] + 1):
                        meta(img, (x, y), switch, color, transparency, function)
                        error += anstieg
                        if error >= 0.5:
                            error -= 1
                            y += 1
                elif -1 < anstieg < 0:
                    y = p0[1]
                    error = 0
                    for x in range(p0[0], p1[0] + 1):
                        meta(img, (x, y), switch, color, transparency, function)
                        error -= anstieg
                        if error >= 0.5:
                            error -= 1
                            y -= 1

            """
            print(3)
            anstieg = (p1[1] - p0[1]) / (p1[0] - p0[0])
            verschiebung = p0[1] - p0[0]*anstieg

            for x in range(p0[0], p1[0], 1):
                y_high, y_low = 0, 0
                if anstieg > 0:
                    y_low = max(math.floor((x - 0.5) * anstieg + verschiebung), p0[1])
                    y_high = min(math.ceil((x + 0.5) * anstieg + verschiebung), p1[1])
                else:
                    y_low = min(math.floor((x - 0.5) * anstieg + verschiebung), p0[1])
                    y_high = max(math.ceil((x + 0.5) * anstieg + verschiebung), p1[1])
                print(x,y_low,y_high)
                for y in range(y_low, y_high + 1):
                    function(img, (x, y), color, transparency)
            """

    def printOperations(self, file=None):
        content = str(self.nails) + "\n"
        for o in self.operations:
            content += str(o[0]) + " " + str(o[1]) + "\n"
        f = open(file, "w")
        f.write(content)
        f.close()


def strat1(art):
    art.invert()
    curNail = 0
    lastNails = deque()
    i = 0
    while i < 3000:
        nextNail = art.getDarkestLineFromNail(curNail, lastNails)
        lastNails.append(nextNail)
        if i >= 100:
            lastNails.popleft()
        art.drawLine(curNail, nextNail, 20, 0.15)
        curNail = nextNail
        if i % 100 == 99:
            print(i)
        i += 1
    art.printOperations("operations.txt")


def strat2(art, step=5, minimumBrightness=50):
    art.invert()
    lineBrightnesses = art.getLineBrightnesses()
    minBrightness = 255
    while minBrightness > minimumBrightness:
        for line in lineBrightnesses:
            ends = line[0]
            if line[1] >= minBrightness:
                line[1] = art.getLine(ends[0], ends[1])
                if line[1] >= minBrightness:
                    art.drawLine(ends[0], ends[1], 20, 0.15)
                    line[1] = art.getLine(ends[0], ends[1])
                    if line[1] < minimumBrightness:
                        lineBrightnesses.remove(line)

        minBrightness -= step
        print(minBrightness)
    art.printOperations("operations.txt")


def sortBrightnesses(lineBrightnesses):
    if lineBrightnesses == []:
        return []
    smaller = []
    bigger = []
    value = lineBrightnesses[0][1]

    for line in lineBrightnesses[1:]:
        if line[1] >= value:
            bigger.append(line)
        else:
            smaller.append(line)

    return sortBrightnesses(smaller) + [lineBrightnesses[0]] + sortBrightnesses(bigger)


def strat3(art):
    art.invert()
    lineBrightnesses = sortBrightnesses(art.getLineBrightnesses())
    minBrightness = 255
    while minBrightness > 50:
        validLines = []
        for line in lineBrightnesses:
            ends = line[0]
            if line[1] >= minBrightness:
                line[1] = art.getLine(ends[0], ends[1])
                if line[1] >= minBrightness:
                    validLines.append(line)

        validLines = sortBrightnesses(validLines)

        for line in validLines:
            art.drawLine(line[0][0], line[0][1], 20, 0.15)

        minBrightness -= 5
        print(minBrightness)
    art.printOperations("operations.txt")


def strat4(art, numberOfLines=3000):
    art.invert()
    lines = PriorityQueue()
    brightnesses = art.getLineBrightnesses()

    for l in brightnesses:
        lines.put((-l[1], l[0]))

    counter = 0
    while counter < numberOfLines:
        line = lines.get()
        if line[0] == -art.getLine(line[1][0], line[1][1]):
            art.drawLine(line[1][0], line[1][1], 20, 0.15)
            counter += 1
            if counter % 100 == 0:
                print(counter)
            continue
        lines.put((-art.getLine(line[1][0], line[1][1]),line[1]))
    art.printOperations("operations.txt")


art = StringArt(288, "test-images/rotkehlchen.jpeg")
strat4(art)
