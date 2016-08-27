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

class PressureGauge(object):
    range = math.pi*2*0.77
    start = math.pi/4
    name = 'pressure.png'
    start_pos = Point(0.05,0.72)
    wobble = 0.2
    def __init__(self, train):
        self.train = train
        self.quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.name))
        self.size = globals.atlas.SubimageSprite(self.name).size
        self.arrow_quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords('arrow.png'))
        self.arrow_size = globals.atlas.SubimageSprite('arrow.png').size
        self.arrow_coords = ((-11,-3),(-11,3),(9,3),(9,-3))
        bl = self.start_pos*globals.screen
        tr = bl + self.size
        self.pos = bl
        self.arrow_pos = bl + Point(24,32)
        self.quad.SetVertices(bl,tr,0.4)
        self.level = 0
        self.set_dial()

    def set_dial(self):
        new_angle = -self.level*self.range + self.start
        vertices = [0,0,0,0]
        for i,coord in enumerate(self.arrow_coords):
            p = coord[0] + coord[1]*1j
            distance,old_angle = cmath.polar(p)
            c = cmath.rect(distance,old_angle + new_angle)
            vertices[i] = self.arrow_pos + Point(c.real, c.imag)
        self.arrow_quad.SetAllVertices(vertices, 0.5)

    def Update(self, level, elapsed):
        self.level = level
        if level < 0.05:
            #no wobble
            pass
        elif level < 0.5:
            self.level += self.wobble*random.random()*elapsed
        if level > 0.5:
            self.level += self.wobble*random.random()*elapsed*20*(level-0.5)

        if self.level < 0:
            self.level = 0
        if self.level > 1:
            self.level = 1.0
        self.set_dial()

class Speedo(PressureGauge):
    name = 'speed.png'
    start_pos = Point(0.2,0.72)
    wobble = 0.2

class Regulator(object):
    name = 'regulator.png'
    knob_name = 'regulator_knob.png'
    start_pos = Point(0.35,0.72)
    start_angle = 0.45
    end_angle   = -0.27
    def __init__(self, train):
        self.train = train
        self.quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.name))
        self.size = globals.atlas.SubimageSprite(self.name).size
        self.knob_quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.knob_name))
        self.knob_coords = ((-10,-28),(-10,20),(54,20),(54,-28))
        self.knob_settings = (0.45,0.13,-0.25)
        bl = self.start_pos*globals.screen
        tr = bl + self.size
        self.knob_pos = bl + Point(5,28)
        self.pos = bl
        self.quad.SetVertices(bl,tr,0.6)
        self.level = 0
        self.Update(self.start_angle)

    def snap(self):
        #choose the nearest setting and switch to it
        if self.current_angle > 0.35:
            self.choose_setting(0)
        elif self.current_angle > 0:
            self.choose_setting(1)
        else:
            self.choose_setting(2)

    def choose_setting(self, n):
        self.Update(self.knob_settings[n])
        #possibly play sound here
        self.train.set_steam(n*0.5)


    def Update(self, angle):
        new_angle = angle - 0.20
        self.current_angle = angle
        vertices = [0,0,0,0]
        for i,coord in enumerate(self.knob_coords):
            p = coord[0] + coord[1]*1j
            distance,old_angle = cmath.polar(p)
            c = cmath.rect(distance,old_angle + new_angle)
            vertices[i] = self.knob_pos + Point(c.real, c.imag)

        self.knob_quad.SetAllVertices(vertices, 0.5)

    def __contains__(self, item):
        return (item.x >= self.pos.x) and (item.x < self.pos.x + self.size.x) and (item.y >= self.pos.y) and (item.y < self.pos.y + self.size.y)

    def click(self, pos):
        diff = pos - (self.knob_pos - Point(0,4))
        p = diff.x + diff.y*1j
        r,a = cmath.polar(p)
        if r > 28 and r < 36 and a > -0.45 and a < 0.48:
            return True, self
        return False, False

    def motion(self, pos):
        diff = pos - (self.knob_pos - Point(0,4))
        p = diff.x + diff.y*1j
        r,a = cmath.polar(p)
        if a < self.end_angle:
            a = self.end_angle
        if a > self.start_angle:
            a = self.start_angle
        self.Update(a)

class Train(object):
    max_speed = 20
    safe_speed = 13
    def __init__(self,parent):
        self.parent = parent
        self.quad = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords('train.png'))
        self.quad.SetVertices(Point(20,43),Point(300,43+80),0.2)
        self.pressure_gauge = PressureGauge(self)
        self.speedo = Speedo(self)
        self.regulator = Regulator(self)
        self.wheels = [Wheel(20+x,y,r) for (x,y,r) in ((99,43,0),(141,43,math.pi))]
        self.move_direction = 0
        #self.wheel = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords(os.path.join('wheel.png')))
        #self.wheel.SetVertices(Point(20+99,43),Point(20+99+28,43+28),0.3)
        self.speed = 0
        self.moved = 0
        self.steam = 0

    def Update(self, elapsed):
        if self.move_direction:
            self.speed += self.move_direction*elapsed*10

        if self.speed > self.max_speed:
            self.speed = self.max_speed
        if self.speed >= self.safe_speed:
            self.parent.shake = (self.speed - self.safe_speed)
        else:
            self.parent.shake = 0
        self.moved += self.speed

        for wheel in self.wheels:
            wheel.Update(self.moved)

        self.pressure_gauge.Update(0, elapsed)
        self.speedo.Update(self.speed/self.max_speed, elapsed)
        #self.regulator.Update(0)

    def set_steam(self, value):
        self.steam = value
        print 'steam now',value

    def mouse_button_down(self, pos, button):
        if button != 1:
            return False, False
        if pos in self.regulator:
            return self.regulator.click(pos)
        return False, False

    def mouse_button_up(self, pos, button):
        if button != 1:
            return False, False
        if globals.dragging is self.regulator:
            self.regulator.snap()
            return True,False
        return False,False

class LoopingQuad(object):
    def __init__(self, pos, z, name, sf):
        self.pos = pos
        self.name = name
        self.z = z
        self.sf = sf
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
        self.moved = (moved*self.sf) % self.size.x
        self.set_coords()


class GameView(ui.RootElement):
    def __init__(self):
        self.atlas = globals.atlas = drawing.texture.TextureAtlas('tiles_atlas_0.png','tiles_atlas.txt')
        self.game_over = False
        self.sky = LoopingQuad(Point(0,0), 0, 'sky.png', 0.1)
        self.hills = LoopingQuad(Point(0,0), 0.05, 'hills.png', 0.6)
        self.tracks = LoopingQuad(Point(0,0), 0.1, 'tracks.png', 1.0)
        self.train = Train(self)
        self.last = None
        self.move_direction = 0
        self.shake = 0
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
        if self.shake:
            r1 = ((random.random()*2)-1)
            r2 = ((random.random()*2)-1)
            adjust = (r1*self.shake, r2*self.shake)
            drawing.Translate( adjust[0], adjust[1],0)
        else:
            adjust = (0,0)
        drawing.DrawNoTexture(globals.line_buffer)
        drawing.DrawNoTexture(globals.colour_tiles)
        drawing.DrawAll(globals.quad_buffer,self.atlas.texture.texture)
        drawing.DrawAll(globals.nonstatic_text_buffer,globals.text_manager.atlas.texture.texture)
        return adjust

    def Update(self,t):
        if self.last is None:
            self.last = t
            return
        elapsed = float(t - self.last)/1000
        self.last = t

        self.train.Update(elapsed)
        for backdrop in self.sky,self.tracks,self.hills:
            backdrop.Update(self.train.moved)

        if self.mode:
            self.mode.Update(t)

        if self.game_over:
            return

        self.t = t

    def GameOver(self):
        self.game_over = True
        self.mode = modes.GameOver(self)

    def MouseButtonDown(self,pos,button):
        return self.mode.MouseButtonDown(pos, button)

    def MouseButtonUp(self,pos,button):
        return self.mode.MouseButtonUp(pos, button)

    def MouseMotion(self, pos, rel):
        return self.mode.MouseMotion(pos, rel)

    def MouseMotion(self,pos,rel,handled):
        if globals.dragging:
            globals.dragging.motion(pos)

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

