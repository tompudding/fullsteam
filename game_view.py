from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import modes
import random

class Wheel(object):
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.initial_angle = angle
        self.height = 28
        self.radius = self.height/2
        self.pos = Point(x+self.radius,y+self.radius)
        self.quad = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords(os.path.join('wheel.png')))
        self.coords = ((-self.radius, -self.radius),
                       (-self.radius, self.radius),
                       (self.radius, self.radius),
                       (self.radius, -self.radius))
        self.set_vertices()
        self.circumference = math.pi*2*self.radius

    def set_vertices(self):
        vertices = [0,0,0,0]
        for i,coord in enumerate(self.coords):
            p = coord[0] + coord[1]*1j
            distance,angle = cmath.polar(p)
            c = cmath.rect(distance,angle + self.angle)
            vertices[i] = self.pos + Point(c.real, c.imag)
        self.quad.SetAllVertices(vertices, 0.3)

    def Update(self, moved):
        self.angle = self.initial_angle + (moved/self.radius)
        self.set_vertices()


class Train(object):
    def __init__(self):
        self.quad = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords('train.png'))
        self.quad.SetVertices(Point(20,43),Point(300,43+80),0.2)
        self.wheels = [Wheel(20+x,y,r) for (x,y,r) in ((99,43,0),(141,43,math.pi))]
        self.move_direction = 0
        #self.wheel = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords(os.path.join('wheel.png')))
        #self.wheel.SetVertices(Point(20+99,43),Point(20+99+28,43+28),0.3)
        self.speed = 0
        self.moved = 0

    def Update(self, elapsed):
        if self.move_direction:
            self.speed += self.move_direction*elapsed*0.001
        self.moved += self.speed

        for wheel in self.wheels:
            wheel.Update(self.moved)

class LoopingQuad(object):
    def __init__(self, pos, z, name):
        self.pos = pos
        self.name = name
        self.z = z
        self.quads = [drawing.Quad(globals.quad_buffer) for i in xrange(2)]
        self.size = globals.atlas.SubimageSprite(self.name).size
        self.tc = globals.atlas.TextureSpriteCoords(self.name)
        self.moved = 10
        self.set_coords()

    def set_coords(self):
        #The first quad is the amount moved
        self.quads[0].SetVertices(self.pos, Point(self.pos.x + self.moved, self.pos.y + self.size.y), self.z)
        # #The texture coordinate is
        moved_partial = 1-float(self.moved)/self.size.x
        coords = [[moved_partial,0],[moved_partial,1],[1,1],[1,0]]
        globals.atlas.TransformCoords(os.path.join(globals.dirs.sprites,self.name), coords)
        self.quads[0].SetTextureCoordinates(coords)
        #The second goes from moved to the end
        self.quads[1].SetVertices(self.pos + Point(self.moved,0), Point(self.pos.x + self.size.x,self.pos.y + self.size.y), self.z)
        coords = [[0,0],[0,1],[moved_partial,1],[moved_partial,0]]
        tc = globals.atlas.TransformCoords(os.path.join(globals.dirs.sprites,self.name), coords)
        self.quads[1].SetTextureCoordinates(coords)

    def Update(self, moved):
        self.moved = moved % self.size.x
        self.set_coords()


class GameView(ui.RootElement):
    def __init__(self):
        self.atlas = globals.atlas = drawing.texture.TextureAtlas('tiles_atlas_0.png','tiles_atlas.txt')
        self.game_over = False
        self.sky = LoopingQuad(Point(0,0), 0, 'sky.png')
        self.tracks = LoopingQuad(Point(0,0), 0.1, 'tracks.png')
        self.train = Train()
        self.last = None
        self.move_direction = 0
        #pygame.mixer.music.load('music.ogg')
        #self.music_playing = False
        super(GameView,self).__init__(Point(0,0),globals.screen)
        #skip titles for development of the main game
        self.mode = modes.GameMode(self)
        #self.mode = modes.LevelOne(self)
        self.StartMusic()

    def StartMusic(self):
        pass
        #pygame.mixer.music.play(-1)
        #self.music_playing = True

    def Draw(self):
        drawing.ResetState()
        drawing.DrawNoTexture(globals.line_buffer)
        drawing.DrawNoTexture(globals.colour_tiles)
        drawing.DrawAll(globals.quad_buffer,self.atlas.texture.texture)
        drawing.DrawAll(globals.nonstatic_text_buffer,globals.text_manager.atlas.texture.texture)

    def Update(self,t):
        if self.last is None:
            self.last = t
            return
        elapsed = float(t - self.last)/1000

        self.train.Update(elapsed)
        self.sky.Update(self.train.moved)
        self.tracks.Update(self.train.moved)
        if self.mode:
            self.mode.Update(t)

        if self.game_over:
            return

        self.t = t

    def GameOver(self):
        self.game_over = True
        self.mode = modes.GameOver(self)

    def KeyDown(self,key):
        self.mode.KeyDown(key)

    def KeyUp(self,key):
        if key == pygame.K_DELETE:
            if self.music_playing:
                self.music_playing = False
                pygame.mixer.music.set_volume(0)
            else:
                self.music_playing = True
                pygame.mixer.music.set_volume(1)
        self.mode.KeyUp(key)

