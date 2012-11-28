from svgdraw import SvgDraw


class SvgDrawWaveform(SvgDraw):
    """draw waveforms in svg"""

    def __init__(self, fileObject, picWidth, picHeight, type):
        SvgDraw.__init__(self, fileObject, picWidth, picHeight)
        self.period = 80
        self.waveheight = 50
        self.height = 40
        self.distance = self.period / 4
        self.type = type
        self.pic_height = picHeight
        self.pic_width = picWidth
        self.no_waves = 1
        self.values = []
        self.wave_list = [{"values" : [], "position" : (0, 0)}]
        

    def refresh(self, no_waves):
        
        self.no_waves = no_waves
        self.pic_height = no_waves * (self.waveheight + 5)
        self.pic_width = self.currentX + 150
        self.wave_list = [{"values" : [], "position": (5, 1 + (self.waveheight+5)*i)} for i in range(no_waves)]
        SvgDraw.refresh(self, self.pic_width, self.pic_height)

    def setBoolStartLevel(self, level):
        self.currentX += self.distance / 2
        self.ctx.move_to(self.currentX, self.currentY)
        if not level:
            self.currentY += self.height
            self.ctx.move_to(self.currentX, self.currentY)
    
    def drawPeriod(self, type_="bool"):
        if (type_ == "bool"):
            self.currentX = self.currentX + self.period + self.distance
            self.ctx.line_to(self.currentX, self.currentY)
        else:
            self.ctx.move_to(self.currentX, self.currentY)
            self.ctx.line_to(self.currentX + self.period, self.currentY)
            self.ctx.move_to(self.currentX, self.currentY + self.height)
            self.ctx.line_to(self.currentX + self.period, self.currentY + self.height)
            self.currentX += self.period

    def drawChangeValue(self):
        self.ctx.move_to(self.currentX, self.currentY)
        self.ctx.line_to(self.currentX + self.distance, self.currentY + self.height)
        self.ctx.move_to(self.currentX, self.currentY + self.height)
        self.ctx.line_to(self.currentX + self.distance, self.currentY)
        self.currentX = self.currentX + self.distance

    def drawNoChangeValue(self):
        self.ctx.line_to(self.currentX + self.distance, self.currentY)
        self.ctx.move_to(self.currentX, self.currentY + self.height)
        self.ctx.line_to(self.currentX + self.distance, self.currentY + self.height)
        self.currentX += self.distance

    def drawChangeLevelToHigh(self):
        self.ctx.line_to(self.currentX, self.currentY - self.height)
        self.currentY = self.currentY - self.height

    def drawChangeLevelToLow(self):
        self.ctx.line_to(self.currentX, self.currentY + self.height)
        self.currentY = self.currentY + self.height

    def drawBoolWaveform(self, currVal):
        self.ctx.move_to(self.currentX, self.currentY)
        
        if not len(self.values):
            lastVal = currVal
            self.setBoolStartLevel(currVal)
        else:
            lastVal = self.values[-1]

        if lastVal == currVal:
            self.drawPeriod()

        elif lastVal == 0 and currVal == 1:
            self.drawChangeLevelToHigh()
            self.drawPeriod()

        elif lastVal == 1 and currVal == 0:
            self.drawChangeLevelToLow()
            self.drawPeriod()

        self.values.append(currVal)

    def drawValueWaveform(self, currVal):
        self.ctx.move_to(self.currentX, self.currentY)
        lastVal = self.values[-1] if len(self.values) else 0

        if lastVal == currVal:
            self.drawNoChangeValue()
            self.drawPeriod("int")

        elif lastVal != currVal:
            self.drawChangeValue()
            self.drawPeriod("int")
            self.drawText(self.currentX - self.period,
                          self.currentY + self.height / 1.5,
                          str(currVal))

    def drawWaveform(self, i, currVal, type_, name):
        self.values = self.wave_list[i]["values"]
        self.currentX, self.currentY = self.wave_list[i]["position"]
        self.ctx.move_to(self.currentX, self.currentY)
        
        if (self.currentX == 5):
            self.drawText(self.currentX, self.currentY+self.height*0.6, name)
            self.currentX += 40
        
        if (type_ == "bool"):
            self.drawBoolWaveform(currVal)
        else:
            self.drawValueWaveform(currVal)
        self.wave_list[i]["position"] = (self.currentX, self.currentY)

