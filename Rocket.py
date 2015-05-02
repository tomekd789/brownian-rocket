### PUBLIC SECTION
# Imports
from random import seed as _seed, randint as _randint
from os import system as _system
from time import sleep as _sleep

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.graphics import Color
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.vector import Vector

# Constants
RESOURCE_COUNT = 15 # No. of resources in the game
ASTEROID_COUNT = 24 # No. of asteroids in the game
GAME_TIME = 180.0 # seconds
TIME_STEP = 1.0/60.0 # seconds; game update interval
JOYSTICKS_CONNECTED = False # A flag if the joysticks are actually connected
XSIZE = 900 # Horizontal size of the display; 0..XSIZE-1
YSIZE = 600 # Vertical size of the display; 0..YSIZE-1
MARGIN = 35 # Margin for moving objects to be considered to be out of the window
MAX_ASTEROID_SPEED = 0.15 # Maximum asteroid speed along any axis
MAX_RESOURCE_SPEED = 0.15 # Maximum resource speed along any axis
MAX_ROCKET_SPEED = 0.3 # Maximum rocket speed along any axis

def joystick_summary_status():
    # returns [x, y] for summary position
    if JOYSTICKS_CONNECTED: # case of joysticks actually connected
        # Sum of states; TBC
        pass
    else: # No joysticks; random data
        return [_randint(-10, 10), _randint(-10, 10)]

### PRIVATE SECTION

# Generic widget class for freely moving objects
class SelfMovingItem(Widget):
    pos_x = NumericProperty(0.0)
    pos_y = NumericProperty(0.0)
    vel_x = NumericProperty(0.0)
    vel_y = NumericProperty(0.0)

# Various subclasees, because of different GIFs defined in the .ky file
class Asteroid1(SelfMovingItem):
    pass
class Asteroid2(SelfMovingItem):
    pass
class Asteroid3(SelfMovingItem):
    pass
class Resource(SelfMovingItem):
    pass

class Rocket(Widget):
    # Velocity of the rocket along a given axis
    vel_x = NumericProperty(0.0)
    vel_y = NumericProperty(0.0)
    # ReferenceList to use rocket.vel as a shorthand
    vel = ReferenceListProperty(vel_x, vel_y)

    # Move the rocket one step. Called in equal intervals to animate the rocket
    def move(self):
        # Get velocity from joysticks; if not connected, take a random value
        self.vel = joystick_summary_status()
        # Normalize the speed with the defined maximum
        self.vel_x = self.vel_x * MAX_ROCKET_SPEED
        self.vel_y = self.vel_y * MAX_ROCKET_SPEED
        # Change rocket position
        self.pos = Vector(*self.vel) + self.pos

class GameWidget(Widget):
    rocket = ObjectProperty(None)
    score = NumericProperty(0)
    timer = NumericProperty(GAME_TIME)

    def collision(self):
        # Called if the rocket collides with an obstacle
        # i.e. the window frame, or an asteroid
        
        # Penalty by decreasing available time;
        # Maybe I'll put an explosion animation here
        _sleep(2)
        
        # Rocket is then moved to a collision-safe place
        rocket_is_safe = False
        while not rocket_is_safe:
            # Select a new random position
            xpos = _randint(100, XSIZE - 100)
            ypos = _randint(100, YSIZE - 100)
            self.rocket.center = (xpos, ypos)
            # ...until not colliding with any asteroid
            for i in range(ASTEROID_COUNT):
                if self.rocket.collide_widget(self.children[i]):
                    break
            else:
                rocket_is_safe = True

    def update(self, dt):
        # One step game status update
        
        # Move the rocket by the speed vector
        self.rocket.move()
        
        # Decrease the timer; it will display automatically
        self.timer = self.timer - dt

        # Move the freely floating objects, i.e. asteroids & resources
        # It's aplicable to all these objects with the same algorithm
        # Then there is no separate 'move' function for each class
        for i in range(ASTEROID_COUNT + RESOURCE_COUNT):
            new_x = self.children[i].pos_x + self.children[i].vel_x
            new_y = self.children[i].pos_y + self.children[i].vel_y
            # Wrap up if out of the window
            if new_x < -MARGIN:
                new_x = XSIZE + MARGIN
            if new_x > XSIZE + MARGIN:
                new_x = -MARGIN
            if new_y < -MARGIN:
                new_y = YSIZE + MARGIN
            if new_y > YSIZE + MARGIN:
                new_y = -MARGIN
            self.children[i].pos_x = new_x
            self.children[i].pos_y = new_y
            # Using float due to sub-unit steps; then rounding is needed
            self.children[i].pos = (round(new_x), round(new_y))

        # Check for a rocket collision with the window frame
        if ((self.rocket.y < 0) or
           (self.rocket.top > self.height) or
           (self.rocket.x < 0) or
           (self.rocket.right > self.width)):
            self.collision()
        
        # Check for a rocket collision with an asteroid
        for i in range(ASTEROID_COUNT):
            if self.rocket.collide_widget(self.children[i]):
                self.collision()

        # Check for a rocket meeting with a resource
        for i in range(ASTEROID_COUNT, ASTEROID_COUNT + RESOURCE_COUNT):
            if self.rocket.collide_widget(self.children[i]):
                # Score increases by 1
                self.score = self.score + 1
                # The resource disappears; actually it gets new coordinates,
                # So it immediately translates far away. Then there's no need
                # to destroy and recreate the object.
                xpos = _randint(0, XSIZE)
                ypos = -MARGIN # To avoid resources popping out within the window
                self.children[i].pos = (xpos, ypos)
                self.children[i].pos_x = xpos
                self.children[i].pos_y = ypos

class RocketApp(App):
    def build(self):
        # Building the main window widget
        game = GameWidget()
        # c1, c2, c3 to split the ASTEROID_COUNT into three
        c1 = ASTEROID_COUNT // 3
        c2 = c1 * 2
        # Adding asteroids; three various classes to have three different images
        for i in range(c1):
            game.add_widget(Asteroid1(), i)
        for i in range(c1, c2):
            game.add_widget(Asteroid2(), i)
        for i in range(c2, ASTEROID_COUNT):
            game.add_widget(Asteroid3(), i)
        # Generate random positions for all asteroids (type 1, 2, and 3)
        for i in range(ASTEROID_COUNT):
            while True:
                xpos = _randint(0, XSIZE)
                ypos = _randint(0, YSIZE)
                # ...until being reasonably far from the center,
                # to avoid an immediate collsion with the rocket
                if abs(xpos - XSIZE//2) > 50:
                    if abs(ypos - YSIZE//2) > 50:
                        break
            # Set the asteroid actual location
            game.children[i].pos = (xpos, ypos)
            # Set the asteroid location attributes;
            # These are separate to accumulate computed movement
            game.children[i].pos_x = xpos
            game.children[i].pos_y = ypos
            # Set the asteroid velocity attributes
            game.children[i].vel_x = MAX_ASTEROID_SPEED / (_randint(-3, 3) + 0.5)
            game.children[i].vel_y = MAX_ASTEROID_SPEED / (_randint(-3, 3) + 0.5)
            
        # Adding resources as next items on the widget list
        for i in range(ASTEROID_COUNT, ASTEROID_COUNT + RESOURCE_COUNT):
            # Resource index starts after the ASTEROID_COUNT
            game.add_widget(Resource(), i) # Adding i-th resource
            xpos = _randint(0, XSIZE)
            ypos = _randint(0, YSIZE)
            # Set the resource location
            game.children[i].pos = (xpos, ypos)
            # Set the resource location attributes, float
            game.children[i].pos_x = xpos
            game.children[i].pos_y = ypos
            # Set the resource velocity; float
            game.children[i].vel_x = MAX_RESOURCE_SPEED / (_randint(-3, 3) + 0.5)
            game.children[i].vel_y = MAX_RESOURCE_SPEED / (_randint(-3, 3) + 0.5)

        Clock.schedule_interval(game.update, TIME_STEP)
        return game

if __name__ == '__main__':
    # Initialize the random generator
    _seed()
    
    # Set the window size; the way is ugly, but this is the best advice I've found
    Config.set('graphics', 'width', str(XSIZE))
    Config.set('graphics', 'height', str(YSIZE))

    # Launch the application
    RocketApp().run()
