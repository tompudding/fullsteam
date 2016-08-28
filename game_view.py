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
    arrow_name = 'arrow.png'
    start_pos = Point(0.02,0.72)
    wobble = 0.2
    centre = Point(24,32)
    arrow_coords = ((-11,-3),(-11,3),(9,3),(9,-3))
    def __init__(self, train, initial_level=0.0):
        self.train = train
        self.quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.name))
        self.size = globals.atlas.SubimageSprite(self.name).size
        self.arrow_quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.arrow_name))
        self.arrow_size = globals.atlas.SubimageSprite(self.arrow_name).size
        bl = self.start_pos*globals.screen
        tr = bl + self.size
        self.pos = bl
        self.arrow_pos = bl + self.centre
        self.quad.SetVertices(bl,tr,5.4)
        self.Update(initial_level,0)

    def set_dial(self):
        new_angle = -self.level*self.range + self.start
        vertices = [0,0,0,0]
        for i,coord in enumerate(self.arrow_coords):
            p = coord[0] + coord[1]*1j
            distance,old_angle = cmath.polar(p)
            c = cmath.rect(distance,old_angle + new_angle)
            vertices[i] = self.arrow_pos + Point(c.real, c.imag)
        self.arrow_quad.SetAllVertices(vertices, 5.5)

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
    start_pos = Point(0.13,0.72)
    wobble = 0.2

#The position should be an argument, it's crazy to make classes just for a different position
#oh well, ludum rush

class CoalDial(PressureGauge):
    start_pos = Point(0.51,0.85)
    name = 'dial.png'
    arrow_name = 'needle.png'
    wobble = 0.2
    start = 0
    centre = Point(16,4)
    range = math.pi
    max_level = 4
    arrow_coords = ((-11,-2),(-11,2),(0,3),(0,-3))

    def Update(self, level, elapsed):
        level = float(level)/self.max_level
        super(CoalDial,self).Update(level, elapsed)

class HealthDial(CoalDial):
    max_level = 100
    start_pos = CoalDial.start_pos + Point(0.11,0)

class Regulator(object):
    name = 'regulator.png'
    knob_name = 'regulator_knob.png'
    start_pos = Point(0.25,0.74)
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
        self.quad.SetVertices(bl,tr,5.6)
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

class Brake(object):
    knob_name = 'brake_handle.png'
    start_pos = Point(0.32,0.72)
    start_angle = 0.6
    end_angle   = -0.27
    def __init__(self, train):
        self.train = train
        self.size = Point(64,48)
        self.knob_quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.knob_name))
        self.knob_coords = ((-30,-29),(-30,19),(34,19),(34,-29))
        self.knob_settings = (0.45,0.13,-0.25)
        bl = self.start_pos*globals.screen
        #tr = bl + self.size
        self.knob_pos = bl + Point(30,29)
        self.pos = bl
        self.level = 0
        self.Update(self.start_angle)

    def snap(self):
        #choose the nearest setting and switch to it
        self.Update(self.start_angle)
        #possibly play sound here
        self.train.set_brake(0)


    def Update(self, angle):
        new_angle = angle - 0.20
        self.current_angle = angle
        if new_angle < 0.3:
            brake_amount = (0.3 - new_angle)/(0.50 - self.end_angle)
            self.train.set_brake(brake_amount)
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
        diff = pos - (self.knob_pos)
        p = diff.x + diff.y*1j
        r,a = cmath.polar(p)
        if r > 18 and r < 29 and a > -0.45 and a < 0.6:
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

class Cloud(object):
    rise_speed = 30
    cloud_index = 0
    def __init__(self,start,duration,pos,steam):
        self.x_coord = pos
        self.start_pos = start
        self.duration = duration
        self.z = 0.35
        if not steam:
            self.z += Cloud.cloud_index*0.001
            Cloud.cloud_index = (Cloud.cloud_index + 1)&0xff
        self.start_time = globals.time
        self.end_time = self.start_time + duration
        self.spin = random.random()*math.pi*2
        self.final_size = Point(64,64)*(0.6 + random.random()*0.4)
        self.rise_speed = Cloud.rise_speed * (0.6 + random.random()*0.4)
        self.quad = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords('steam.png' if steam else 'smoke.png'))

    def Update(self, moved, elapsed):
        if globals.time > self.end_time:
            self.quad.Delete()
            return False

        partial = float(globals.time-self.start_time)/self.duration
        angle = partial * self.spin

        size = self.final_size*(partial+0.2)
        height = (float(globals.time - self.start_time)/1000)*self.rise_speed
        bl = self.start_pos + Point(moved - self.x_coord,height) - (size*0.5)
        tr = bl + size
        self.quad.SetVertices(bl,tr,self.z)
        self.quad.SetColour((1,1,1,1-partial**2))
        return True

    def Destroy(self):
        self.quad.Delete()


class Train(object):
    max_speed = 20
    safe_speed = 13
    max_coal = 4
    burn_rate = 0.03
    max_pressure = 1
    coal_to_pressure = 0.5
    pressure_usage = 0.04
    pressure_to_speed = 10
    friction = 0.02
    safe_pressure = 0.65
    safe_braking = 1
    min_pressure = 0.05
    max_clouds = 300
    pressure_loss = 0.005
    name = 'train.png'
    def __init__(self,parent):
        self.parent = parent
        self.pos = Point(20,43)
        self.size = globals.atlas.SubimageSprite(self.name).size
        self.quad = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords(self.name))
        self.quad.SetVertices(self.pos,self.pos + self.size,0.2)
        self.pressure_gauge = PressureGauge(self)
        self.speedo = Speedo(self)
        self.regulator = Regulator(self)
        self.brake = Brake(self)
        self.coal_dial   = CoalDial(self)
        self.health = 100
        self.health_dial = HealthDial(self, self.health)
        self.wheels = [Wheel(20+x,y,r) for (x,y,r) in ((99,43,0),(141,43,math.pi))]
        self.add_coal_text = ui.TextBoxButton(globals.screen_root, 'Add',Point(0.51,0.770),Point(0.61,0.83),size=2,callback=self.add_coal_button,colour=(0.0,0.0,0.0,1.0))
        self.spout_pos = self.pos + Point(53,67)
        self.vent_pos = self.pos + Point(133,49)
        self.clouds = []
        self.move_direction = 0
        self.speed = 0
        self.moved = 0
        self.coal = 0
        self.pressure = 0
        self.steam_flow = 0
        self.braking = 0


    def Update(self, elapsed):
        #if self.move_direction:
        #    self.speed += self.move_direction*elapsed*10
        #Burn fuel in the engine
        #print 'coal : %4.2f, pressure : %4.2f, speed : %4.2f, brake : %4.2f, health : %6.2f' % (self.coal, self.pressure, self.speed, self.braking, self.health)
        self.burn(elapsed)

        if self.steam_flow > 0:
            #We can drive the engine!
            rate = self.steam_flow * self.pressure_usage * elapsed
            rate = min(rate, self.pressure)
            if rate > 0 and self.pressure > self.min_pressure:
                self.adjust_pressure(-rate)
                self.speed += rate * self.pressure_to_speed
        self.adjust_pressure(-self.pressure_loss*elapsed, loss=True)


        if self.braking:
            friction = self.friction + (self.braking**2)*2
        else:
            friction = self.friction

        self.speed -= friction*elapsed*self.speed

        if self.speed > self.max_speed:
            self.speed = self.max_speed
        if self.speed < 0.03 and self.braking:
            self.speed = 0

        self.moved += self.speed

        for wheel in self.wheels:
            wheel.Update(self.moved)

        self.pressure_gauge.Update(self.pressure, elapsed)
        self.speedo.Update(self.speed/self.max_speed, elapsed)
        self.damage(elapsed)
        self.health_dial.Update(self.health, elapsed)
        self.coal_dial.Update(self.coal, elapsed)
        self.clouds = [cloud for cloud in self.clouds if cloud.Update(self.moved, elapsed)]
        #self.regulator.Update(0)

    def add_coal_button(self, pos):
        self.add_coal(1)

    def damage(self, elapsed):
        over_speed = self.speed - self.safe_speed
        if over_speed < 0:
            over_speed = 0

        over_pressure = (self.pressure - self.safe_pressure)*10
        if over_pressure < 0:
            over_pressure = 0
        elif over_pressure > 0:
            self.add_vent_steam(over_pressure*elapsed)

        if self.pressure > 0:
            if self.steam_flow < 0.1:
                brake_sf = 2
            elif self.steam_flow < 0.8:
                brake_sf = 20
            else:
                brake_sf = 30
        else:
            brake_sf = 2
        braking = ((self.braking * self.speed) - self.safe_braking)*brake_sf
        if braking < 0:
            braking = 0


        total = over_speed + over_pressure + braking
        self.parent.shake = min(total, 10)
        self.health -= total*elapsed

    def set_brake(self, amount):
        self.braking = amount

    def burn(self, elapsed):
        scale_factor = [0.5,1,2,3,4,3,1,0.5,0.25,0.1][int(self.coal)]
        if self.coal == 0:
            return

        amount = elapsed * self.burn_rate

        if amount > self.coal:
            amount = self.coal

        self.coal -= amount
        if self.speed > 0:
            speed_factor = math.sqrt(self.speed)
        else:
            speed_factor = 1
        if self.coal < 0.5:
            coal_factor = 0.1
        elif self.coal < 1:
            coal_factor = 0.5
        elif self.coal > 4:
            coal_factor = 2
        else:
            coal_factor = 1
        self.add_smoke(numpy.random.poisson(amount*2000*speed_factor*coal_factor))
        self.adjust_pressure(amount*self.coal_to_pressure*scale_factor)

    def add_steam(self, num, steam=True, pos=None):
        for i in xrange(num):
            new_cloud = Cloud(pos if pos is not None else self.spout_pos, 3000, self.moved, steam=steam)
            self.clouds.insert(0, new_cloud)
        for cloud in self.clouds[self.max_clouds:]:
            cloud.Destroy()
        self.clouds = self.clouds[:self.max_clouds]

    def add_smoke(self, num):
        return self.add_steam(num, steam=False)

    def add_vent_steam(self, num):
        n = numpy.random.poisson(num*10)
        return self.add_steam(n, steam=True, pos=self.vent_pos)

    def adjust_pressure(self, amount, loss=False):
        if amount < 0 and not loss:
            self.add_steam(numpy.random.poisson(-amount*2000*self.steam_flow*math.sqrt(self.speed)))
            #print 'use steam %8.4f' % amount,p

        self.pressure += amount
        if self.pressure > self.max_pressure:
            self.pressure = self.max_pressure
        if self.pressure < 0:
            self.pressure = 0

    def set_steam(self, value):
        self.steam_flow = value
        print 'steam flow now',self.steam_flow

    def mouse_button_down(self, pos, button):
        if button != 1:
            return False, False
        if pos in self.regulator:
            return self.regulator.click(pos)
        elif pos in self.brake:
                return self.brake.click(pos)
        return False, False

    def mouse_button_up(self, pos, button):
        if button != 1:
            return False, False
        if globals.dragging:
            globals.dragging.snap()
            return True,False
        return False,False

    def add_coal(self, amount):
        self.coal += amount
        if self.coal > self.max_coal:
            self.coal = self.max_coal

class LoopingQuad(object):
    def __init__(self, pos, z, name, sf):
        self.pos = pos
        self.name = name
        self.z = z
        self.sf = sf
        self.quads = [drawing.Quad(globals.quad_buffer) for i in xrange(2)]
        self.size = globals.atlas.SubimageSprite(self.name).size
        self.centre = self.pos + (self.size*0.5)
        self.tc = globals.atlas.TextureSpriteCoords(self.name)
        self.moved = 10
        self.angle = 0
        self.set_coords()

    def set_coords(self):
        #The first quad is the amount moved
        bl = self.pos
        tr = Point(self.pos.x + self.moved, self.pos.y + self.size.y)
        vertices = [0,0,0,0]
        for (i,coord) in enumerate((Point(bl.x, bl.y),
                                    Point(bl.x, tr.y),
                                    Point(tr.x, tr.y),
                                    Point(tr.x, bl.y))):
            vertices[i] = coord.Rotate(self.angle)
        self.quads[0].SetAllVertices(vertices,self.z)
        # #The texture coordinate is
        moved_partial = 1-float(self.moved)/self.size.x
        coords = [[moved_partial,0],[moved_partial,1],[1,1],[1,0]]
        globals.atlas.TransformCoords(os.path.join(globals.dirs.sprites,self.name), coords)
        self.quads[0].SetTextureCoordinates(coords)
        #The second goes from moved to the end
        bl = self.pos + Point(self.moved,0)
        tr = Point(self.pos.x + self.size.x,self.pos.y + self.size.y)
        for (i,coord) in enumerate((Point(bl.x, bl.y),
                                    Point(bl.x, tr.y),
                                    Point(tr.x, tr.y),
                                    Point(tr.x, bl.y))):
            vertices[i] = coord.Rotate(self.angle)
        #self.quads[1].SetVertices(self.pos + Point(self.moved,0), Point(self.pos.x + self.size.x,self.pos.y + self.size.y), self.z)
        self.quads[1].SetAllVertices(vertices,self.z)
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
        #self.hills.angle = -0.1
        #self.sky.angle = -0.1
        self.train = Train(self)
        self.last = None
        self.move_direction = 0
        self.shake = 0
        self.text = ui.TextBox(parent = globals.screen_root,
                               bl     = Point(0,0.68)         ,
                               tr     = Point(1,0.78)         ,
                               text   = 'Pressure  Speed   Regulator  Brake       Coal     Health' ,
                               textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                               colour = drawing.constants.colours.black,
                               scale  = 2)
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

