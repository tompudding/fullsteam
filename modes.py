from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import sys

class Mode(object):
    """ Abstract base class to represent game modes """
    def __init__(self,parent):
        self.parent = parent

    def KeyDown(self,key):
        pass

    def KeyUp(self,key):
        pass

    def MouseButtonDown(self,pos,button):
        return False,False

    def Update(self,t):
        pass

class TitleStages(object):
    STARTED  = 0
    COMPLETE = 1
    TEXT     = 2
    SCROLL   = 3
    WAIT     = 4

class Titles(Mode):
    blurb = "FULL STEAM"
    def __init__(self,parent):
        self.parent          = parent
        self.start           = pygame.time.get_ticks()
        self.stage           = TitleStages.STARTED
        self.handlers        = {TitleStages.STARTED  : self.Startup,
                                TitleStages.COMPLETE : self.Complete}
        bl = self.parent.GetRelative(Point(0,0))
        tr = bl + self.parent.GetRelative(globals.screen)
        self.blurb_text = ui.TextBox(parent = self.parent,
                                     bl     = bl         ,
                                     tr     = tr         ,
                                     text   = self.blurb ,
                                     textType = drawing.texture.TextTypes.GRID_RELATIVE,
                                     colour = (1,1,1,1),
                                     scale  = 4)
        self.backdrop        = ui.Box(parent = globals.screen_root,
                                      pos    = Point(0,0),
                                      tr     = Point(1,1),
                                      colour = (0,0,0,0))
        self.backdrop.Enable()

    def KeyDown(self,key):
        self.stage = TitleStages.COMPLETE

    def Update(self,t):
        self.elapsed = t - self.start
        self.stage = self.handlers[self.stage](t)

    def Complete(self,t):
        self.backdrop.Delete()
        self.blurb_text.Delete()
        self.parent.mode = GameOver(self.parent)

    def Startup(self,t):
        return TitleStages.STARTED

chunk_width = 1000

def smoothstep(last,target,x):
    diff = (target - last)
    height = last + diff*x*x*(3-2*x)
    incline = (diff*6*x*(1-x))/chunk_width
    #That incline is a ratio, we want an angle
    r,a = cmath.polar( 1 + incline*1j)
    return -a

class MainMenu(Mode):
    blurb  = 'FULL STEAM'
    blurbs = ["Always wanted to be a train driver",
              "Job One - Across the plains",
              "Job Two - Down the mountain",
              "Job Three - To Eagle's Perch"]
    level_names = ['Tutorial',
                   'Job One',
                   'Job Two',
                   'Job Three']
    level_heights = [[0,0],        #Totally flat and short
                     [0,0,0,0,0,0], #Normal
                     [2000,1500,1400,1200,1000,800,400,200,0], #Downhill
                     [1000,900,800,600,400,200,0,100,200,400,600,800,1000,500,0]] #Reach the perch]


    def __init__(self,parent):
        self.parent = parent
        #bl = self.parent.GetRelative(self.parent.viewpos.pos)
        #self.parent.viewpos.Follow(globals.time,self.parent.map.player)


        self.backdrop = drawing.Quad(globals.screen_texture_buffer,tc = globals.atlas.TextureSpriteCoords('parchment.png'))
        self.backdrop_size = globals.atlas.SubimageSprite('parchment.png').size
        backdrop_bl = Point(40,0)
        backdrop_tr = backdrop_bl + self.backdrop_size
        self.backdrop.SetVertices(backdrop_bl,backdrop_tr,10)
        self.keydownmap = 0
        self.playing = False
        self.current_level = 0
        self.pause_time = 0

        self.frame = ui.UIElement(globals.screen_root,
                                  globals.screen_root.GetRelative(backdrop_bl),
                                  globals.screen_root.GetRelative(backdrop_tr))
        #tr = bl + self.parent.GetRelative(globals.screen)
        self.blurb_text = ui.TextBox(parent = self.frame,
                                     bl     = Point(0.0,0.72) ,
                                     tr     = Point(1,1) ,
                                     text   = self.blurb ,
                                     textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                     colour = (0,0,0,1),
                                     scale  = 3,
                                     alignment = drawing.texture.TextAlignments.CENTRE,
                                     )
        self.underline = ui.TextBox(parent = self.frame,
                                     bl     = Point(0.0,0.67) ,
                                     tr     = Point(1,0.95) ,
                                     text   = '**********' ,
                                     textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                     colour = (0,0,0,1),
                                     scale  = 3,
                                     alignment = drawing.texture.TextAlignments.CENTRE,
                                     )
        self.level_ok_button = ui.TextBoxButton(self.frame, 'OK',Point(0.4,0.15),Point(0.5,0.22),size=2,callback=self.click_ok,colour=(0.0,0.0,0.0,1.0))

        self.level_back_button = ui.TextBoxButton(self.frame, 'Back',Point(0.5,0.15),Point(0.6,0.22),size=2,callback=self.click_back,colour=(0.0,0.0,0.0,1.0))
        self.quit_button = ui.TextBoxButton(self.frame, 'QUIT',Point(0.45,0.1),Point(0.55,0.17),size=2,callback=self.click_quit,colour=(0.0,0.0,0.0,1.0))
        self.back_to_game = ui.TextBoxButton(self.frame, 'Cancel',Point(0.6,0.1),Point(0.7,0.17),size=2,callback=self.click_cancel,colour=(0.0,0.0,0.0,1.0))
        self.level_callbacks = [self.click_tutorial,self.click_level_one,self.click_level_two,self.click_level_three]
        self.level_buttons = [ui.TextBoxButton(self.frame, self.level_names[i],Point(0.4,0.6-0.075*i),Point(0.6,0.66-0.075*i),size=2,callback=self.level_callbacks[i],colour=(0.0,0.0,0.0,1.0)) for i in xrange(4)]
        self.show_main_menu()

    def show_main_menu(self):
        self.level_ok_button.Disable()
        self.level_back_button.Disable()
        for label in self.level_buttons:
            label.Enable()
        self.blurb_text.SetText(self.blurb,colour=(0,0,0,1))
        self.quit_button.Enable()
        self.underline.Enable()
        self.back_to_game.Disable()

    def click_tutorial(self,pos):
        self.show_level_intro(0)

    def click_level_one(self,pos):
        self.show_level_intro(1)

    def click_level_two(self, pos):
        self.show_level_intro(2)

    def click_level_three(self, pos):
        self.show_level_intro(3)

    def click_cancel(self, pos):
        self.frame.Disable()
        self.backdrop.Disable()
        self.playing = True
        self.parent.Enable()
        self.parent.add_pause_time(globals.time - self.pause_time)

    def show_level_intro(self, level):
        for label in self.level_buttons:
            label.Disable()
        self.underline.Disable()
        self.current_level = level
        self.blurb_text.Enable()
        self.blurb_text.SetText(self.blurbs[level],colour=(0,0,0,1))
        self.level_ok_button.Enable()
        self.quit_button.Disable()
        self.level_back_button.Enable()


    def level_length(self):
        return chunk_width * (len(self.level_heights[self.current_level])-1)

    def click_ok(self, pos):
        self.frame.Disable()
        self.backdrop.Disable()
        self.playing = True
        self.parent.Enable()
        self.parent.Reset()

    def click_back(self, pos):
        self.show_main_menu()

    def click_quit(self, pos):
        raise SystemExit(0)

    def get_incline(self, moved):
        chunk = int(1 + (float(moved) / chunk_width))
        if chunk >= len(self.level_heights[self.current_level]):
            return 0
        target = self.level_heights[self.current_level][chunk]
        last = self.level_heights[self.current_level][chunk-1]
        partial = float(moved % chunk_width) / chunk_width
        return smoothstep(last,target,partial)

    def KeyDown(self,key):
        pass

    def KeyUp(self,key):
        if self.playing and key == pygame.K_ESCAPE:
            self.playing = False
            self.frame.Enable()
            self.backdrop.Enable()
            self.parent.Disable()
            self.back_to_game.Enable()
            self.pause_time = globals.time

    def MouseButtonDown(self,pos,button):
        if self.playing:
            return self.parent.train.mouse_button_down(pos,button)
        return False,False

    def MouseButtonUp(self,pos,button):
        if self.playing:
            return self.parent.train.mouse_button_up(pos,button)
        return False,False

    def MouseMotion(self,pos,rel):
        if self.playing:
            if globals.dragging:
                globals.dragging.motion(pos)


    def Update(self, t):
        return self.playing



class GameOver(Mode):
    blurb = "GAME OVER"
    def __init__(self,parent):
        self.parent          = parent
        self.blurb           = self.blurb
        self.blurb_text      = None
        self.handlers        = {TitleStages.TEXT    : self.TextDraw,
                                TitleStages.SCROLL  : self.Wait,
                                TitleStages.WAIT    : self.Wait}
        self.backdrop        = ui.Box(parent = globals.screen_root,
                                      pos    = Point(0,0),
                                      tr     = Point(1,1),
                                      colour = (0,0,0,0.6))

        bl = self.parent.GetRelative(Point(0,0))
        tr = bl + self.parent.GetRelative(globals.screen)
        self.blurb_text = ui.TextBox(parent = globals.screen_root,
                                     bl     = bl         ,
                                     tr     = tr         ,
                                     text   = self.blurb ,
                                     textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                     scale  = 3)

        self.start = None
        self.blurb_text.EnableChars(0)
        self.stage = TitleStages.TEXT
        self.played_sound = False
        self.skipped_text = False
        self.letter_duration = 20
        self.continued = False
        #pygame.mixer.music.load('end_fail.mp3')
        #pygame.mixer.music.play(-1)

    def Update(self,t):
        if self.start == None:
            self.start = t
        self.elapsed = t - self.start
        self.stage = self.handlers[self.stage](t)
        if self.stage == TitleStages.COMPLETE:
            raise sys.exit('Come again soon!')

    def Wait(self,t):
        return self.stage

    def SkipText(self):
        if self.blurb_text:
            self.skipped_text = True
            self.blurb_text.EnableChars()

    def TextDraw(self,t):
        if not self.skipped_text:
            if self.elapsed < (len(self.blurb_text.text)*self.letter_duration) + 2000:
                num_enabled = int(self.elapsed/self.letter_duration)
                self.blurb_text.EnableChars(num_enabled)
            else:
                self.skipped_text = True
        elif self.continued:
            return TitleStages.COMPLETE
        return TitleStages.TEXT


    def KeyDown(self,key):
        #if key in [13,27,32]: #return, escape, space
        if not self.skipped_text:
            self.SkipText()
        else:
            self.continued = True

    def MouseButtonDown(self,pos,button):
        self.KeyDown(0)
        return False,False
