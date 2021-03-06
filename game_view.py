from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import modes
import random

class Wheel(object):
    def __init__(self, train, x, y, angle):
        self.train = train
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
        self.vertices = [0,0,0,0]
        self.set_vertices()
        self.circumference = math.pi*2*self.radius

    def set_vertices(self):
        pos = globals.rotation_offset + (self.pos - globals.rotation_offset).Rotate(self.train.parent.incline)
        for i,coord in enumerate(self.coords):
            p = coord[0] + coord[1]*1j
            distance,angle = cmath.polar(p)
            c = cmath.rect(distance,angle + self.angle + self.train.parent.incline)
            self.vertices[i] = pos + Point(c.real, c.imag)
        self.quad.SetAllVertices(self.vertices, 0.3)

    def get_point(self, r):
        c = cmath.rect(self.radius*r, (self.angle-self.initial_angle) )
        return self.pos + Point(c.real, c.imag)

    def Update(self, moved):
        self.angle = self.initial_angle + (moved/self.radius)
        self.set_vertices()

class PressureGauge(object):
    range = math.pi*2*0.77
    start = math.pi/4
    name = 'pressure.png'
    arrow_name = 'arrow.png'
    start_pos = Point(-0.02,0.72)
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
    start_pos = Point(0.085,0.72)
    wobble = 0.2

class Clock(object):
    range = math.pi*2*0.77
    start = math.pi/4
    name = 'clock.png'
    hour_hand_name = 'hour_hand.png'
    minute_hand_name = 'minute_hand.png'
    start_pos = Point(0.8,0.81)
    centre = Point(16,16)
    hour_hand_coords = ((-1,-1),(-1,6),(1,6),(1,-1))
    minute_hand_coords = ((-0.5,-1),(-0.5,13),(0.5,13),(0.5,-1))
    seconds_to_hours = 0.01
    def __init__(self, train, initial_level=0.0):
        self.train = train
        self.quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.name))
        self.size = globals.atlas.SubimageSprite(self.name).size
        self.hour_hand_quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.hour_hand_name))
        self.hour_hand_size = globals.atlas.SubimageSprite(self.hour_hand_name).size
        self.minute_hand_quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.minute_hand_name))
        self.minute_hand_size = globals.atlas.SubimageSprite(self.minute_hand_name).size
        bl = self.start_pos*globals.screen
        tr = bl + self.size
        self.pos = bl
        self.hour_hand_pos = bl + self.centre
        self.minute_hand_pos = bl + self.centre
        self.quad.SetVertices(bl,tr,5.4)
        self.Update(0)

    def set_dial(self, hour, minute):
        hour_angle = -2*math.pi*float(hour)/12
        minute_angle = -2*math.pi*float(minute)/60
        for quad,coords,angle in ((self.hour_hand_quad, self.hour_hand_coords, hour_angle),
                                  (self.minute_hand_quad, self.minute_hand_coords, minute_angle)):
            vertices = [0,0,0,0]
            for i,coord in enumerate(coords):
                p = coord[0] + coord[1]*1j
                distance,old_angle = cmath.polar(p)
                c = cmath.rect(distance,old_angle + angle)
                vertices[i] = self.pos + self.centre + Point(c.real, c.imag)
            quad.SetAllVertices(vertices, 5.5+i+1)

    def Update(self, elapsed):
        time = self.train.parent.start_time_hours + self.seconds_to_hours * float(globals.time - self.train.parent.start_time)/1000
        minutes = (time % 1.0) * 60
        hours = time % 12

        self.set_dial(hours, minutes)


#The position should be an argument, it's crazy to make classes just for a different position
#oh well, ludum rush

class CoalDial(PressureGauge):
    start_pos = Point(0.47,0.85)
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
    start_pos = Point(0.205,0.74)
    start_angle = 0.45
    end_angle   = -0.27
    knob_settings = (0.45,0.13,-0.25)
    def __init__(self, train):
        self.train = train
        if self.name:
            self.quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.name))
            self.size = globals.atlas.SubimageSprite(self.name).size
        self.knob_quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.knob_name))
        if not self.name:
            self.size = globals.atlas.SubimageSprite(self.knob_name).size
        self.knob_coords = ((-10,-28),(-10,20),(54,20),(54,-28))
        bl = self.start_pos*globals.screen
        tr = bl + self.size
        self.knob_pos = bl + Point(5,28)
        self.pos = bl
        if self.name:
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
        #possibly play sound here
        globals.sounds.cachunk.play()

    def choose_setting(self, n):
        if self.train.parent.tutorial == self.train.parent.tutorial_regulator_on and n == 1:
            self.train.parent.tutorial()
        elif self.train.parent.tutorial == self.train.parent.tutorial_regulator_off and n == 0:
            self.train.parent.tutorial()
        self.Update(self.knob_settings[n])
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

        self.knob_quad.SetAllVertices(vertices, 5.5)

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

class Reverser(Regulator):
    name = None
    knob_name = 'reverser.png'
    start_pos = Point(0.69,0.72)
    start_angle = 0.45
    end_angle   = -0.4
    knob_settings = (0.45,-0.25)

    def __init__(self, *args, **kwargs):
        super(Reverser,self).__init__(*args,**kwargs)
        self.last_setting = 0

    def choose_setting(self, n):
        if abs(self.train.steam_flow) < 0.01:
            self.Update(self.knob_settings[n])
            self.last_setting = n
            self.train.set_dir(1 if n == 0 else -1)
        else:
            self.Update(self.knob_settings[self.last_setting])

    def snap(self):
        #choose the nearest setting and switch to it
        if self.current_angle < -0.1:
            self.choose_setting(1)
        else:
            self.choose_setting(0)
        if abs(self.train.steam_flow) < 0.01:
            globals.sounds.cachunk.play()


    def click(self, pos):
        diff = pos - (self.knob_pos - Point(1.5,1.2))
        p = diff.x + diff.y*1j
        r,a = cmath.polar(p)
        if r > 15 and r < 30 and a > -0.45 and a < 0.7:
            return True, self
        return False, False

    def motion(self, pos):
        diff = pos - (self.knob_pos + Point(0,4))
        p = diff.x + diff.y*1j
        r,a = cmath.polar(p)
        if a < self.end_angle:
            a = self.end_angle
        if a > 0.6:
            a = 0.6
        self.Update(a)



class Brake(object):
    knob_name = 'brake_handle.png'
    start_pos = Point(0.28,0.72)
    start_angle = 0.6
    end_angle   = -0.27
    def __init__(self, train):
        self.train = train
        self.last_screech = 0
        self.size = Point(64,48)
        self.knob_quad = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords(self.knob_name))
        self.knob_coords = ((-30,-29),(-30,19),(34,19),(34,-29))
        self.knob_settings = (0.45,0.13,-0.25)
        bl = self.start_pos*globals.screen
        #tr = bl + self.size
        self.knob_pos = bl + Point(30,29)
        self.pos = bl
        self.level = 0
        self.Reset()

    def Reset(self):
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
            if brake_amount > 0.5 and self.train.speed > 0.1:
                if (globals.time - self.last_screech) > 1000:
                    globals.sounds.screech.play()
                    self.last_screech = globals.time
        vertices = [0,0,0,0]
        for i,coord in enumerate(self.knob_coords):
            p = coord[0] + coord[1]*1j
            distance,old_angle = cmath.polar(p)
            c = cmath.rect(distance,old_angle + new_angle)
            vertices[i] = self.knob_pos + Point(c.real, c.imag)

        self.knob_quad.SetAllVertices(vertices, 5.5)

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
    gravity = 4
    name = 'train.png'
    def __init__(self,parent):
        self.parent = parent
        self.pos = Point(20,43)
        self.size = globals.atlas.SubimageSprite(self.name).size
        self.quad = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords(self.name))
        self.flag_quad = drawing.Quad(globals.quad_buffer, tc=globals.atlas.TextureSpriteCoords('flag.png'))
        self.flag_size = globals.atlas.SubimageSprite('flag.png').size
        self.bars = [drawing.Quad(globals.quad_buffer, tc=globals.atlas.TextureSpriteCoords('wheel_bar.png')),
                     drawing.Quad(globals.quad_buffer, tc=globals.atlas.TextureSpriteCoords('mid_bar.png')),
                     drawing.Quad(globals.quad_buffer, tc=globals.atlas.TextureSpriteCoords('piston_bar.png'))]
        self.pressure_gauge = PressureGauge(self)
        self.speedo = Speedo(self)
        self.regulator = Regulator(self)
        self.reverser  = Reverser(self)
        self.brake = Brake(self)
        self.coal_dial   = CoalDial(self)
        self.clock = Clock(self)
        self.clouds = []
        self.distance_text = ui.TextBox(globals.screen_root,Point(0.9,0.83),Point(1.0,0.93),'????.??',scale=2,colour=(0,0,0,1.0))
        self.Reset()
        self.health_dial = HealthDial(self, self.health)
        self.wheels = [Wheel(self,20+x,y,r) for (x,y,r) in ((99,43,0),(141,43,math.pi))]
        self.add_coal_text = ui.TextBoxButton(globals.screen_root, 'Add',Point(0.475,0.770),Point(0.575,0.83),size=2,callback=self.add_coal_button,colour=(0.0,0.0,0.0,1.0))
        self.Disable()
        self.spout_pos = self.pos + Point(53,67)
        self.vent_pos = self.pos + Point(133,49)


    def Reset(self):
        self.health = 100
        self.chug_type = None
        self.last_chug = 0
        self.high_speed = 0
        self.coal_used = 0
        self.coal = 0
        self.moved = 0
        self.speed = 0
        self.move_direction = 0
        self.steam_flow = 0
        self.braking = 0
        self.set_vertices()
        for cloud in self.clouds:
            cloud.Destroy()
        self.clouds = []
        self.distance_text.SetText('????.??')
        self.direction = 1
        self.pressure = 0
        self.reverser.choose_setting(0)
        self.regulator.choose_setting(0)
        self.brake.Reset()
        for sound in globals.sounds.chugs:
            sound.stop()

    def set_vertices(self):
        if self.parent.incline == 0:
            return self.quad.SetVertices(self.pos,self.pos + self.size,0.2)
        bl = self.pos - globals.rotation_offset
        tr = bl + self.size
        vertices = [0,0,0,0]
        for (i,coord) in enumerate((Point(bl.x, bl.y),
                                    Point(bl.x, tr.y),
                                    Point(tr.x, tr.y),
                                    Point(tr.x, bl.y))):
            vertices[i] = globals.rotation_offset + coord.Rotate(self.parent.incline)
        self.quad.SetAllVertices(vertices,0.2)

    def Enable(self):
        self.distance_text.Enable()
        self.add_coal_text.Enable()

    def Disable(self):
        self.distance_text.Disable()
        self.add_coal_text.Disable()

    def set_dir(self, direction):
        self.direction = direction

    def draw_bars(self, elapsed):
        #Do the wheel bar first
        a = self.wheels[0].get_point(0.7)
        #b = self.wheels[1].get_point(0.6)
        bl = a - globals.rotation_offset
        tr = bl + Point(42,4)
        vertices = [0,0,0,0]
        for (i,coord) in enumerate((Point(bl.x, bl.y),
                                    Point(bl.x, tr.y),
                                    Point(tr.x, tr.y),
                                    Point(tr.x, bl.y))):
            vertices[i] = globals.rotation_offset + coord.Rotate(self.parent.incline)
        self.bars[0].SetAllVertices(vertices,0.7)
        x_adjust = a.x - self.wheels[0].pos.x

        #Now the piston bar which oscillates sideways
        bl = Point(54 + x_adjust,12) - globals.rotation_offset + self.pos
        tr = bl + Point(23,4)
        for (i,coord) in enumerate((Point(bl.x, bl.y),
                                    Point(bl.x, tr.y),
                                    Point(tr.x, tr.y),
                                    Point(tr.x, bl.y))):
            vertices[i] = globals.rotation_offset + coord.Rotate(self.parent.incline)
        self.bars[2].SetAllVertices(vertices,0.19)

        #Now the middle piston. This needs rotating twice unfortunately
        #first we rotate it about the position on the end of the piston bar so it reaches the wheel
        centre = Point(54 + x_adjust,12) + self.pos + Point(23,2)
        bl = Point(-2,-2)
        tr = bl + Point(42,4)
        diff = a - (centre + bl)
        r,angle = cmath.polar(diff.x + diff.y*1j)
        for (i,coord) in enumerate((Point(bl.x, bl.y),
                                    Point(bl.x, tr.y),
                                    Point(tr.x, tr.y),
                                    Point(tr.x, bl.y))):
            vertices[i] = centre + coord.Rotate(angle)
        for (i,coord) in enumerate(vertices):
            vertices[i] = (vertices[i] - globals.rotation_offset).Rotate(self.parent.incline) + globals.rotation_offset
        self.bars[1].SetAllVertices(vertices,0.7)

    def Update(self, elapsed):
        #if self.move_direction:
        #    self.speed += self.move_direction*elapsed*10
        #Burn fuel in the engine
        #print 'coal : %4.2f, pressure : %4.2f, speed : %4.2f, brake : %4.2f, health : %6.2f' % (self.coal, self.pressure, self.speed, self.braking, self.health)
        self.clock.Update(elapsed)
        self.set_vertices()
        self.burn(elapsed)
        level_left = self.parent.mode.level_length() - self.moved
        flag_bl = Point(120,40) - Point(level_left,0)
        flag_tr = flag_bl + self.flag_size
        self.flag_quad.SetVertices(flag_bl, flag_tr, 0.1)


        self.distance_text.SetText('%7.2f' % (level_left), colour = (0,0,0,1))

        if self.steam_flow > 0:
            #We can drive the engine!
            rate = self.steam_flow * self.pressure_usage * elapsed
            rate = min(rate, self.pressure)
            if rate > 0 and self.pressure > self.min_pressure:
                self.adjust_pressure(-rate)
                self.speed += rate * self.pressure_to_speed * self.direction
        self.adjust_pressure(-self.pressure_loss*elapsed, loss=True)


        if self.braking:
            friction = self.friction + (self.braking**2)*2
        else:
            friction = self.friction

        #gravity term
        if self.parent.incline != 0:
            d = cmath.rect(1, self.parent.incline)
            self.speed += d.imag*self.gravity*elapsed

        self.speed -= friction*elapsed*self.speed

        if self.speed > self.max_speed:
            self.speed = self.max_speed
        if self.speed < -self.max_speed:
            self.speed = -self.max_speed
        if self.speed > self.high_speed:
            self.high_speed = self.speed

        if abs(self.speed) < 0.03:
            if self.braking:
                self.speed = 0
                if self.parent.tutorial == self.parent.tutorial_brake:
                    self.parent.tutorial()
            if abs(level_left) < 40 and self.speed < 0.01:
                globals.sounds.win_music.play()
                self.parent.mode.level_complete(self.coal_used, self.health, globals.time - self.parent.start_time,self.high_speed)
            if self.chug_type is not None:
                globals.sounds.chugs[self.chug_type].stop()
            self.chug_type = None
        elif abs(self.speed) < 1.5:
            if self.chug_type != 0:
                if self.chug_type is not None:
                    globals.sounds.chugs[self.chug_type].stop()
                self.chug_type = 0
                globals.sounds.chugs[self.chug_type].play(-1)
        elif abs(self.speed) < 2:
            if self.chug_type != 1:
                if self.chug_type is not None:
                    globals.sounds.chugs[self.chug_type].stop()
                self.chug_type = 1
                globals.sounds.chugs[self.chug_type].play(-1)
        elif abs(self.speed) < 10:
            if self.chug_type != 2:
                if self.chug_type is not None:
                    globals.sounds.chugs[self.chug_type].stop()
                self.chug_type = 2
                globals.sounds.chugs[self.chug_type].play(-1)
        elif self.chug_type != 3:
            if self.chug_type is not None:
                globals.sounds.chugs[self.chug_type].stop()
            self.chug_type = 3
            globals.sounds.chugs[self.chug_type].play(-1)



        self.moved += self.speed

        for wheel in self.wheels:
            wheel.Update(self.moved)

        self.draw_bars(elapsed)

        self.pressure_gauge.Update(self.pressure, elapsed)
        self.speedo.Update(self.speed/self.max_speed, elapsed)
        self.damage(elapsed)
        self.health_dial.Update(self.health, elapsed)
        self.coal_dial.Update(self.coal, elapsed)
        self.clouds = [cloud for cloud in self.clouds if cloud.Update(self.moved, elapsed)]
        #self.regulator.Update(0)

    def add_coal_button(self, pos):
        self.add_coal(1)
        self.coal_used += 1
        globals.sounds.whoosh.play()
        if self.parent.tutorial == self.parent.tutorial_coal:
            self.parent.tutorial()


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
                brake_sf = 10
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
        if self.health <= 0:
            self.parent.shake = 0
            globals.sounds.die.play()
            if self.chug_type is not None:
                globals.sounds.chugs[self.chug_type].stop()
            self.parent.mode.level_fail(globals.time - self.parent.start_time)

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
            pos = pos if pos is not None else self.spout_pos
            if self.parent.incline != 0:
                new_pos = globals.rotation_offset + (pos-globals.rotation_offset).Rotate(self.parent.incline)
            else:
                new_pos = pos
            new_cloud = Cloud(new_pos, 3000, self.moved, steam=steam)
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
            self.add_steam(numpy.random.poisson(-amount*2000*self.steam_flow*math.sqrt(abs(self.speed))))
            #print 'use steam %8.4f' % amount,p

        self.pressure += amount
        if self.pressure > self.max_pressure:
            self.pressure = self.max_pressure
        if self.pressure < 0:
            self.pressure = 0
        if self.parent.tutorial == self.parent.tutorial_pressure and self.pressure > self.min_pressure:
            self.parent.tutorial()

    def set_steam(self, value):
        self.steam_flow = value

    def mouse_button_down(self, pos, button):
        if button != 1:
            return False, False
        if pos in self.regulator:
            return self.regulator.click(pos)
        elif pos in self.brake:
                return self.brake.click(pos)
        elif pos in self.reverser:
            return self.reverser.click(pos)
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
        self.quads = [drawing.Quad(globals.quad_buffer) for i in xrange(4)]
        self.size = globals.atlas.SubimageSprite(self.name).size
        self.centre = self.pos + (self.size*0.5)
        self.tc = globals.atlas.TextureSpriteCoords(self.name)
        for quad in self.quads:
            quad.SetTextureCoordinates(self.tc)
        self.moved = 10
        self.angle = 0
        self.set_coords()

    def set_coords(self):
        for (i,quad) in enumerate(self.quads):
            view_offset = Point((i-2)*self.size.x + self.moved,0)

            bl = self.pos - globals.rotation_offset + view_offset
            tr = bl + self.size
            vertices = [0,0,0,0]
            for (j,coord) in enumerate((Point(bl.x, bl.y),
                                        Point(bl.x, tr.y),
                                        Point(tr.x, tr.y),
                                        Point(tr.x, bl.y))):
                vertices[j] = globals.rotation_offset + coord.Rotate(self.angle)

            quad.SetAllVertices(vertices,self.z)

    def Update(self, moved):
        self.moved = (moved*self.sf) % self.size.x
        self.set_coords()

class GameView(ui.RootElement):
    def __init__(self):
        self.start_time_hours = 0
        self.tutorial = False
        self.atlas = globals.atlas = drawing.texture.TextureAtlas('tiles_atlas_0.png','tiles_atlas.txt')
        self.game_over = False
        self.sky = LoopingQuad(Point(0,0), 0, 'sky.png', 0.1)
        self.hills = LoopingQuad(Point(0,-50), 0.05, 'hills.png', 0.6)
        self.tracks = LoopingQuad(Point(0,-84), 0.1, 'tracks.png', 1.0)
        self.start_time = globals.time
        self.incline = 0
        self.train = Train(self)
        self.last = None
        self.box = ui.Box(parent = globals.screen_root,
                          pos = Point(0.005,0.74),
                          tr = Point(0.995,0.99),
                          colour = (1,1,1,0.5),
                          z=5
                          )
        self.text = ui.TextBox(parent = globals.screen_root,
                               bl     = Point(-0.045,0.71)         ,
                               tr     = Point(1.2,0.81)         ,
                               text   = 'Pressure  Speed   Regulator  Brake       Coal     Health   Reverser  Time  Distance' ,
                               textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                               colour = drawing.constants.colours.black,
                               scale  = 2)
        self.tutorial_text = ui.TextBox(parent = globals.screen_root,
                                        bl = Point(-0.02,0),
                                        tr = Point(1,0.1),
                                        text = ' ',
                                        textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                        colour = drawing.constants.colours.white,
                                        scale = 2,
                                        alignment = drawing.texture.TextAlignments.LEFT)
        self.tutorial_text.Disable()
        self.text.Disable()
        #pygame.mixer.music.load('music.ogg')
        #self.music_playing = False
        super(GameView,self).__init__(Point(0,0),globals.screen)
        #skip titles for development of the main game
        self.mode = modes.MainMenu(self)
        self.StartMusic()
        self.Reset()

    def start_tutorial(self):
        self.tutorial = self.tutorial_just_click
        self.tutorial_text.SetText('Howdy Pardner! Welcome to the railroad. Click on this text to begin')
        self.tutorial_text.Enable()

    def tutorial_just_click(self):
        self.tutorial = self.tutorial_coal
        self.tutorial_text.SetText('To get started add some coal into the boiler. Only one for now')

    def tutorial_coal(self):
        self.tutorial = self.tutorial_pressure
        self.tutorial_text.SetText('Now wait for the pressure indicator to pass the green line')

    def tutorial_pressure(self):
        self.tutorial = self.tutorial_regulator_on
        self.tutorial_text.SetText('Great now ease the regulator in position 1; half steam')

    def tutorial_regulator_on(self):
        self.tutorial = self.tutorial_regulator_off
        self.tutorial_text.SetText('We\'re underway! Keep and eye on the distance and switch the regulator to 0 around 500')

    def tutorial_regulator_off(self):
        self.tutorial = self.tutorial_brake
        self.tutorial_text.SetText('Now *gently* apply the brake to stop. Too much can damage the train')

    def tutorial_brake(self):
        self.tutorial = None
        self.tutorial_text.SetText('Brilliant. Now try to reach the flag at distance 0')

    def end_tutorial(self):
        self.tutorial = False
        self.tutorial_text.Disable()

    def add_pause_time(self, amount):
        self.start_time += amount

    def Reset(self):
        self.train.Reset()
        self.incline = 0
        self.shake = 0
        self.start_time = globals.time

    def StartMusic(self):
        globals.sounds.win_music.play()
        #pygame.mixer.music.play(-1)
        #self.music_playing = True

    def Enable(self):
        self.box.Enable()
        self.text.Enable()
        self.train.Enable()
        if self.tutorial:
            self.tutorial_text.Enable()

    def Disable(self):
        self.box.Disable()
        self.text.Disable()
        self.train.Disable()
        self.tutorial_text.Disable()

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
        if self.mode:
            if not self.mode.Update(t):
                #mode is not ready for us yet
                return

        elapsed = float(t - self.last)/1000
        self.last = t

        self.incline = self.mode.get_incline(self.train.moved)
        self.hills.angle = self.incline/2
        self.tracks.angle = self.incline


        self.train.Update(elapsed)
        for backdrop in self.sky,self.tracks,self.hills:
            backdrop.Update(self.train.moved)


        if self.game_over:
            return

        self.t = t

    def GameOver(self):
        self.game_over = True
        self.mode = modes.GameOver(self)

    def MouseButtonDown(self,pos,button):
        new_pos = (pos - globals.rotation_offset).Rotate(-self.incline)
        if new_pos.x >= 9 and new_pos.x <= 19 and new_pos.y >= 89 and new_pos.y <= 93:
            globals.sounds.whistle.play()
        return self.mode.MouseButtonDown(pos, button)

    def MouseButtonUp(self,pos,button):
        if self.tutorial == self.tutorial_just_click and pos.y < 15:
            self.tutorial()
        return self.mode.MouseButtonUp(pos, button)

    def MouseMotion(self,pos,rel,handled):
        return self.mode.MouseMotion(pos, rel)

    def KeyDown(self,key):
        self.mode.KeyDown(key)

    def KeyUp(self,key):
        #self.mode.level_fail(globals.time - self.start_time)
        #self.mode.level_complete(0,100,21000,15.653)
        self.mode.KeyUp(key)

