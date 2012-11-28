from svgdraw import SvgDraw

class SvgDrawDiagram(SvgDraw):
    '''draw diagrams in svg'''
    
    def __init__(self, filename, picWidth, picHeight):
        SvgDraw.__init__(self, filename, picWidth, picHeight)
        # constants
        self.cEntityheight = 0.6
        self.cEntitylength = 0.5
        
        
    def drawEntity(self, xPos, yPos, name):
        self.drawRectangle(xPos, yPos+0.05, self.cEntitylength, self.cEntityheight)
        self.drawText(xPos, yPos, name)