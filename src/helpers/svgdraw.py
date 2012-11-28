import cairo
import rsvg
import math


class SvgDraw():
    '''Draws simple objects in svg'''

    def __init__(self, fileObject, picWidth, picHeight):
        self.fo = fileObject
        SvgDraw.refresh(self, picWidth, picHeight)

        # settings for text
        #self.ctx.set_font_size(20.0)
        #self.ctx.set_line_width(3.0)
        self.ctx.set_source_rgb(0.0, 0.0, 0.0)
        self.ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        
        # reset coordinates
        self.currentX = 0
        self.currentY = 0
        
    def refresh(self, width, height):
        self.__width = width
        self.__height = height
        self.resize(self.__width, self.__height)

    def getWidth(self):
        return self.__width

    def getHeight(self):
        return self.__height

    def drawLine(self, xPos, yPos):
        self.ctx.line_to(xPos, yPos)
        self.currentX = xPos
        self.currentY = yPos

    def finish(self):
        self.ctx.stroke()
        self.surface.finish()

    def drawText(self, xPos, yPos, text):
        self.ctx.move_to(xPos, yPos)
        self.ctx.show_text(text)

    def resize(self, width, height):
        self.surface = cairo.SVGSurface(self.fo, self.__width, self.__height)
        self.ctx = cairo.Context(self.surface)




