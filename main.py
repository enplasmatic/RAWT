import pygame
import sys
import edit
import numpy as np
from scipy.io import wavfile
import math
import tkinter as tk
from tkinter import filedialog
# Initialize Tkinter (used only for file dialog; hide when pygame window)
root = tk.Tk()
root.withdraw()

PATH = "input.wav"


pygame.init()
pygame.font.init()

fName = "fonts/HelveticaNeue-Medium.otf"
font = pygame.font.Font(fName, 20)
dfont = pygame.font.Font(fName, 15)

WHITE = (255,255,255)
BLACK = (0,0,0)

def upload():
    file_path = filedialog.askopenfilename(
            title="Select Code File",
            filetypes=(
                ("Wave files", "*.wav"),
            )
        )
    if file_path:
        uploaded_file = file_path
    else:
        uploaded_file = "input.wav"
    return uploaded_file

def draw_text(surface, text, font, position, color=(255, 255, 255)):
    """
    Draws text on a Pygame surface.

    :param surface: The Pygame surface to draw on (e.g., screen)
    :param text: The string of text to display
    :param position: (x, y) tuple for where to draw the text
    :param font_size: Size of the font
    :param color: RGB tuple for text color
    :param font_name: Optional font name (e.g., "arial")
    """
    
    text_surface = font.render(str(text), True, color)
    surface.blit(text_surface, position)

import random

def draw_wah_visualizer(surface, x, y, w, h, wah_value):
    """
    Draws a sine-based wave that changes shape based on the wah_value.
    
    Args:
        surface: Pygame surface to draw on.
        x, y: Top-left corner of the visualizer.
        w, h: Width and height of the visualizer box.
        wah_value: Value from 0 (no wah) to 1 (full wah sweep).
    """
    points = []
    amplitude = h / 2 * (0.3 + 0.7 * wah_value)  # More 'wah' means more wave
    frequency = 2 + 6 * wah_value               # 2 to 8 full sine cycles
    sharpness = 0.5 + 1.5 * wah_value           # Controls choppiness

    for i in range(w):
        t = i / w
        angle = t * frequency * 2 * math.pi
        sine = math.sin(angle)
        # Sharpen the wave shape (make it grittier as wah_value increases)
        modified = math.copysign(abs(sine)**sharpness, sine)
        y_pos = y + h/2 - modified * amplitude
        if effects["Wah q"] <= 0: y_pos = y + h / 2
        points.append((x + i, int(y_pos)))

    # pygame.draw.rect(surface, (30, 30, 30), (x, y, w, h), 1)
    if len(points) >= 2:
        pygame.draw.lines(surface, "#17848c", False, points, 2)

import math
import time

def get_wah_value(t, depth=0.7, rate=2.0, base_freq=400, q=0.6):
    """
    Generate a normalized wah_value (0.0 to 1.0) for visualization.

    Parameters:
    - t: Current time in seconds
    - depth: Wah range intensity (0.0 to 1.0)
    - rate: Wah sweep rate in Hz
    - base_freq: Starting frequency (used for visual sense of scale)
    - q: Resonance factor (influences visual sharpness idea, optional)

    Returns:
    - wah_value: A float between 0.0 and 1.0
    """
    # Sine LFO modulator (moves between 0 and 1)
    lfo = (math.sin(2 * math.pi * rate * t) + 1) / 2

    # Control how deeply the LFO affects the visual
    wah_value = depth * lfo

    # Optionally, adjust visually based on resonance (q)
    # Here, we make higher q subtly increase the sharpness (normalized to 0–1 range)
    sharpness_factor = min(max((q - 0.3) / 1.0, 0), 1)

    # Combine both ideas: depth * lfo sweep with slight q enhancement
    return min(1.0, wah_value + 0.2 * sharpness_factor)

def draw_gritty_sinewave(surface, top_left_x, top_left_y, width, height, grit, freq=2, col=(255,0,0)):
    """
    Draw a red sine wave inside the box (top_left_x, top_left_y, width, height).
    grit: float >=0 controlling the 'dirtiness' / choppiness of the wave.
          0 = clean sine wave; higher values = more noise/chop.
    """

    points = []
    amplitude = height / 2 * 0.9
    mid_y = top_left_y + height / 2

    # Step in pixels, smaller step = smoother wave
    step = 2
    for i in range(0, width + 1, step):
        # base sine wave value (from 0 to width mapped to 0 to freq*2pi)
        angle = (i / width) * (freq * 2 * math.pi)
        clean_y = math.sin(angle)

        # Add grit noise - random jitter scaled by grit and amplitude
        noise = (random.uniform(-1, 1) * grit)

        # Add some random distortion - e.g., quantize signal or add random jumps
        distortion = 0
        if grit > 0:
            distortion = int((random.uniform(-grit, grit) * 5)) * 0.02

        y = mid_y - amplitude * (clean_y + noise + distortion)

        points.append((top_left_x + i, int(y)))

    # Draw the wave as a connected line
    if len(points) > 1:
        pygame.draw.lines(surface, col, False, points, 2)


# === Function to draw waveform ===
def draw_waveform(filename, surface, color=(0, 255, 0), position=(0, 0), size=(1000, 200)):
    """
    Draws the waveform of a .wav file onto the given Pygame surface.

    :param filename: Path to the .wav file
    :param surface: Pygame surface to draw on
    :param color: RGB color of the waveform
    :param position: (x, y) top-left position of waveform
    :param size: (width, height) size of the waveform display area
    """
    try:
        rate, data = wavfile.read(filename)
    except Exception as e:
        print(f"Error loading audio: {e}")
        return

    # Handle stereo by taking one channel
    if data.ndim > 1:
        data = data[:, 0]

    # Normalize the audio data
    data = data / np.max(np.abs(data))

    # Downsample if needed
    width, height = size
    samples_per_pixel = max(1, len(data) // width)
    scaled_data = data[::samples_per_pixel][:width]

    # Convert to screen coordinates
    midline = position[1] + height // 2
    amplitude = (height // 2) - 5
    points = [
    ]
    for x, value in enumerate(scaled_data):
        try:
            points.append((position[0] + x, midline - int(value * amplitude)))
        except ValueError:
            points.append((position[0] + x, midline))

    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, 1)

def draw_gritty_curve(surface, top_left_x, top_left_y, width, height, start_height, end_height, grit):
    """
    Draw a red noisy curve inside the rectangle (top_left_x, top_left_y, width, height).

    start_height, end_height: floats from 0.0 to 1.0
        Represent the relative vertical position of start and end points (0=top, 1=bottom)

    grit: float >= 0, controls choppiness/dirtiness of the curve.
          0 = clean curve, higher = noisier.

    """
    points = []
    step = 2  # pixels step for drawing

    # Convert normalized heights to absolute Y positions
    y_start = top_left_y + start_height * height
    y_end = top_left_y + end_height * height

    for i in range(0, width + 1, step):
        t = i / width  # normalized horizontal position [0..1]

        # Simple smooth curve: quadratic interpolation between start and end heights
        # You can change this to any other smooth curve you want
        base_y = (1 - t)**2 * y_start + 2*(1 - t)*t*((y_start + y_end)/2) + t**2 * y_end

        # Add grit noise (vertical jitter)
        noise = random.uniform(-grit, grit) * height * 0.05

        # Add a little random distortion (like quantization)
        distortion = 0
        if grit > 0:
            distortion = int(random.uniform(-grit*5, grit*5)) * 0.01 * height

        y = base_y + noise + distortion

        points.append((top_left_x + i, int(y)))

    if len(points) > 1:
        pygame.draw.lines(surface, "#17848c", False, points, 2)


# === Pygame setup ===
pygame.init()

# Set up the window
WIDTH, HEIGHT = 1400, 680
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RAWT")

# Clock for controlling frame rate
clock = pygame.time.Clock()

def Image(p):
    return pygame.image.load(p).convert_alpha()
class Button:
    def __init__(self, x, y, width, height, color, text, font_name, font_size, font_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.original_col = color
        self.highlighted_col = tuple([max(0, self.original_col[i]-70) for i in range(3)])
        self.color = self.original_col
        self.text = text
        self.font = pygame.font.Font(font_name, font_size)
        self.pressed = False  # Track press state
        self.clicked = False  # Track full click cycle
        self.textcol = font_color

    def draw(self, surface):
        # Draw the button
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)

        # Render text and center it
        text_surf = self.font.render(self.text, True, self.textcol)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

        # Handle click detection
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if self.rect.collidepoint(mouse_pos):
            self.color = self.highlighted_col
            if mouse_pressed and not self.pressed:
                self.pressed = True  # Mouse went down
            elif not mouse_pressed and self.pressed:
                self.pressed = False
                return True  # Mouse went up — click complete
        else:
            self.color = self.original_col
            if not mouse_pressed:
                self.pressed = False  # Reset if released off-button

        return False

def Audio(p):
    pygame.mixer.Sound(p).play()

rawt = Image("rawt.png")

knobs = []
std_effects = {'Delay in Seconds': 0.0, 
           'Delay Feedback': 50.0, 
           'Delay Mix': 100, 
           'Reverb Size': 0.0, 
           'Reverb Damping': 0.0, 
           'Dry Level': 100.0,
           'Wet Level': 0.0,
           'Reverb Width': 0.0,
           'Bitcrush Mix': 100.0,
           'Gain / Volume': 50.0, 
           'Highpass': 0.0,
           'Lowpass': 100.0,
            'Drive': 0.0, 
            'Pitch': 50.0,
            'Limiter DB': 100.0, 
            'Limiter Release': 0.0,
            'LFO Speed': 0.0, 
            'LFO Detune': 0.0, 
            'Base Delay': 0.0, 
            'Chorus Feedback': 0.0, 
            'Chorus Mix': 0.0,
            'Speed': 20.0,
            "Q": 70.7,
            "Pan": 50,
            }

effects = std_effects.copy()
tE = 0
short = {
    'Delay in Seconds': 'amt',
    'Delay Feedback': 'feed',
    'Delay Mix': 'mix',
    'Reverb Size': 'size',
    'Reverb Damping': 'damp',
    'Dry Level': "dry",
    'Wet Level': "wet",
    'Reverb Width': "width",
    'Bitcrush Mix': 'mix',
    'Gain / Volume': 'gain',
    'Highpass': 'high',
    'Lowpass': 'low',
    'Drive': 'drive',
    'Pitch': 'pitch',
    'Limiter DB': 'DB',
    'Limiter Release': 'rel',
    'LFO Speed': 'speed',
    'LFO Detune': 'detune',
    'Base Delay': 'delay',
    'Chorus Feedback': 'feed',
    'Chorus Mix': 'mix',
    'Sweep Speed': 'speed',
    'Sweep Detune': 'detune',
    'Sweep Delay': 'freq',
    'Sweep Feedback': 'feed',
    'Sweep Mix': 'mix',

    'Speed': 'speed',

    'Thresh': 'hold',
    'Comp Ratio': 'ratio',
    'Comp Attack': 'attack',
    'Comp Release': 'rel',

    'NG Thresh': 'hold',
    'NG Ratio': 'ratio',
    'NG Attack': 'attack',
    'NG Release': 'rel',

    'Invert': 'flip',

    'Wah Depth': 'depth',
    'Wah Drive': 'base',
    'Wah Rate': 'rate',
    'Wah q': 'wahness',


    'F Thresh': 'high mix',
    'F Ratio': 'low mix',
    'F Attack': 'boost lows',
    'F Release': 'boost highs',
    'Q': 'Q',

    "Pan": "pan",

}

class Knob(pygame.sprite.Sprite):
    def __init__(self, control, x, y):
        super().__init__()
        knobs.append(self)

        self.image = Image("knob.svg")
        self.original = self.image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.x, self.y = x, y
        self.ctrl = control

        self.min_angle = -135
        self.max_angle = 135
        if control in effects:
            self.angle = effects[control] * 0.01 * 270 - 135
        else:
            self.angle = self.min_angle
        self.image = pygame.transform.rotate(self.original, -self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        self.dragging = False
        self.last_mouse_y = 0
        self.sensitivity = 2.5  # Degrees per pixel moved

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.last_mouse_y = event.pos[1]

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

    def update(self):
        if self.dragging:
            mouse_y = pygame.mouse.get_pos()[1]
            dy = self.last_mouse_y - mouse_y  # Positive = move up
            self.last_mouse_y = mouse_y

            # Update angle
            self.angle += dy * self.sensitivity
            self.angle = max(self.min_angle, min(self.max_angle, self.angle))

            # Rotate image
            self.image = pygame.transform.rotozoom(self.original, -self.angle, 1)
            self.rect = self.image.get_rect(center=self.rect.center)
        self.value = 100 + ((self.angle + self.min_angle) / (abs(self.min_angle)+self.max_angle)) * 100
        effects[self.ctrl] = self.value
        # Draw to screen
        screen.blit(self.image, self.rect.topleft)
        p, q = pygame.mouse.get_pos()
        if self.rect.collidepoint((p,q)) or self.dragging:
            global highlighted_val
            highlighted_val = self.value

upbutton = Button(x=20, y=30, width=300, height=40,
                   color=WHITE, text="Upload Sound", font_name=fName, font_size=30, font_color=BLACK)

# Create button (place outside the main loop)
pibutton = Button(x=20, y=90, width=300, height=40,
                   color=WHITE, text="Play Input Sound", font_name=fName, font_size=30, font_color=BLACK)

pobutton = Button(x=20, y=HEIGHT-100-200-30, width=300, height=40,
                   color=WHITE, text="Play Output Sound", font_name=fName, font_size=30, font_color=BLACK)

applybutton = Button(x=20, y=HEIGHT-60, width=300, height=40,
                   color=WHITE, text="Apply Changes", font_name=fName, font_size=30, font_color=BLACK)

downbutton = Button(x=340, y=HEIGHT-60, width=300, height=40,
                   color=WHITE, text="Download .wav", font_name=fName, font_size=30, font_color=BLACK)

resetbutton = Button(x=660, y=HEIGHT-60, width=300, height=40,
                   color=WHITE, text="Stop All Sounds", font_name=fName, font_size=30, font_color=BLACK)

colors = [
    (255, 0, 0),       # Red
    (255, 85, 0),      # Orange Red
    (255, 170, 0),     # Orange
    (255, 255, 0),     # Yellow
    (170, 255, 0),     # Lime Yellow
    (85, 255, 0),      # Lime Green
    (0, 255, 0),       # Green
    (0, 255, 85),      # Spring Green
    (0, 255, 170),     # Aqua
    (0, 255, 255),     # Cyan
    (0, 170, 255),     # Sky Blue
    (0, 85, 255),      # Azure
    (0, 0, 255),       # Blue
    (85, 0, 255),      # Indigo
    (170, 0, 255),     # Purple
    (255, 0, 255),     # Magenta
    (255, 0, 170),     # Hot Pink
    (255, 0, 85),      # Neon Pink
    (255, 51, 102),    # Watermelon
    (255, 102, 153),   # Bubblegum Pink
    (204, 0, 102),     # Raspberry
    (255, 204, 0),     # Amber
    (255, 153, 51),    # Pumpkin
    (255, 102, 0),     # Carrot
    (102, 255, 102),   # Mint Green
    (0, 204, 102),     # Jungle Green
    (102, 255, 255),   # Light Cyan
    (102, 102, 255),   # Lavender Blue
    (153, 0, 255),     # Electric Purple
    (255, 102, 204),   # Carnation Pink
    (255, 204, 229),   # Pastel Pink
    (255, 255, 153),   # Light Yellow
    (204, 255, 153),   # Light Lime
    (153, 255, 204),   # Light Mint
    (204, 204, 255)    # Light Periwinkle
]
random.shuffle(colors)
plugins = []
def add_knob(name, x, y):
    Knob(name, x, y)

add_knob("Delay in Seconds", 400, 100)
add_knob("Delay Feedback", 460, 100)
add_knob("Delay Mix", 430, 140)
plugins.append(["delay", pygame.Rect(400, 100, 460, 140)])

add_knob("Reverb Size", 600, 100)
add_knob("Reverb Damping", 660, 100)
add_knob("Reverb Width", 720, 100)
add_knob("Wet Level", 630, 140)
add_knob("Dry Level", 690, 140)
plugins.append(["reverb", pygame.Rect(600, 100, 720, 140)])

add_knob("Bitcrush Mix", 860, 120)
plugins.append(["bitfield", pygame.Rect(860, 100, 860, 140)])

add_knob("Wah Depth", 1000, 90)
add_knob("Wah Drive", 1090, 90)
add_knob("Wah Rate", 1000, 140)
add_knob("Wah q", 1090, 140)

plugins.append(["wah wah", pygame.Rect(1000, 90, 1090, 140)])

add_knob("F Ratio", 1225, 120)
add_knob("F Thresh", 1335, 120)
add_knob("F Release", 1335, 215)
add_knob("F Attack", 1225, 215)
plugins.append(["quad shelf", pygame.Rect(1220, 90, 1340, 250)])


add_knob("Gain / Volume", 400, 250)
add_knob("Highpass", 460, 250)
add_knob("Lowpass", 520, 250)
add_knob("Pitch", 580, 250)
plugins.append(["essentials", pygame.Rect(400, 250, 580, 250)])

add_knob("Drive", 720, 250)
add_knob("Limiter DB", 760, 250)
add_knob("Limiter Release", 820, 250)
plugins.append(["distortion", pygame.Rect(720, 250, 820, 250)])

add_knob("LFO Speed", 400, 360)
add_knob("LFO Detune", 460, 360)
add_knob("Base Delay", 520, 360)
add_knob("Chorus Feedback", 430, 410)
add_knob("Chorus Mix", 490, 410)
plugins.append(["chorus", pygame.Rect(400, 360, 520, 410)])


add_knob("Sweep Speed", 400+260, 360)
add_knob("Sweep Detune", 460+260, 360)
add_knob("Sweep Delay", 520+260, 360)
add_knob("Sweep Feedback", 430+260, 410)
add_knob("Sweep Mix", 490+260, 410)
plugins.append(["phaser", pygame.Rect(400+260, 360, 520+260, 410)])

add_knob("Thresh", 920, 360)
add_knob("Comp Ratio", 980, 360)
add_knob("Comp Attack", 920, 410)
add_knob("Comp Release", 980, 410)
plugins.append(["dl compressor", pygame.Rect(920, 360, 980, 410)])

add_knob("NG Thresh", 1120, 360)
add_knob("NG Ratio", 1180, 360)
add_knob("NG Attack", 1120, 410)
add_knob("NG Release", 1180, 410)
plugins.append(["noise gate", pygame.Rect(1120, 360, 1180, 410)])

add_knob("Invert", 960, 250)
plugins.append(["flip", pygame.Rect(960, 250, 960, 250)])

add_knob("Speed", 1100, 250)
plugins.append(["speed", pygame.Rect(1100, 250, 1100, 250)])


add_knob("Pan", 1320, 385)
plugins.append(["pan", pygame.Rect(1320, 360, 1320, 410)])

pygame.display.set_icon(rawt)

def Getg():
    o = 100 - (effects["Bitcrush Mix"])
    if effects["Bitcrush Mix"] <= 20:
        o = effects['Bitcrush Mix'] * 5
    g = (effects["Drive"] + o + (100-effects["Limiter DB"]))/300
    return g

START = True
# === Main loop ===
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        for knob in knobs:
            knob.handle_event(event)

    screen.fill("#181d20")  # Dark gray background
    for i, plug in enumerate(plugins):
        r = pygame.Rect(plug[1].x-50, plug[1].y-75, plug[1].width-plug[1].x+102, plug[1].height-plug[1].y+100)
        pygame.draw.rect(screen, "#101214", r)
        pygame.draw.rect(screen, colors[i], r, 4, 3)
        draw_text(screen, plug[0], font, (plug[1].x-37, plug[1].y-63), WHITE)

    highlighted_val = None
    for knob in knobs:
        knob.update()
        text_surface = dfont.render(str(short[knob.ctrl]), True, WHITE)
        screen.blit(text_surface, (knob.x - text_surface.get_width() // 2, knob.y-30))
        # draw_text(screen, str(int(knob.value))+"%", font, (knob.x-34, knob.y-55), WHITE)
    if highlighted_val is not None:
        p, q = pygame.mouse.get_pos()
        pygame.draw.rect(screen, "#252a2f", pygame.Rect(p+20, q+20, 70, 20))
        pygame.draw.rect(screen, "#ffffff", pygame.Rect(p+20, q+20, 70, 20), 1)
        draw_text(screen, f"{int(highlighted_val)}%", dfont, (p+22,q+22), WHITE)

    pygame.draw.rect(screen, (0,0,0), (20, 140, 300, 200))
    pygame.draw.rect(screen, (188,188,188), (20, 140, 300, 200), 4, 3)

    draw_waveform(PATH, screen, color=(0, 255, 0), position=(20, 140), size=(300, 200))

    pygame.draw.rect(screen, (0,0,0), (20, HEIGHT - 100 - 180, 300, 200))
    pygame.draw.rect(screen, (188,188,188), (20, HEIGHT - 100 - 180, 300, 200), 4, 3)

    draw_waveform("output.wav", screen, color=(0, 255, 0), position=(20, HEIGHT - 100 - 180), size=(300, 200))

    g = Getg()


    pygame.draw.rect(screen, (0,0,0), (350, HEIGHT - 100 - 125, 500, 125))
    draw_gritty_sinewave(screen, 350, (HEIGHT - 100 - 125) + 40, 500, 125-80, g)
    pygame.draw.rect(screen, (188,188,188), (350, HEIGHT - 100 - 125, 500, 125), 4, 3)
    e = effects
    BOUND = edit.BOUND

    t = time.time()
    w = get_wah_value(t, depth=BOUND(e["Wah Depth"], 0.5, 1), rate=BOUND(e["Wah Rate"], 1, 6), base_freq=BOUND(e["Wah Drive"], 300, 500), q=BOUND(e["Wah q"], 0.5, 0.8))
    pygame.draw.rect(screen, (0,0,0), (870, HEIGHT - 100 - 125, 500, 125))
    draw_wah_visualizer(screen, 870, (HEIGHT - 100 - 125) + 40, 500, 125-80, w)
    pygame.draw.rect(screen, (188,188,188), (870, HEIGHT - 100 - 125, 500, 125), 4, 3)

    if upbutton.draw(screen): 
        PATH = upload()
    if pibutton.draw(screen): Audio(PATH)
    if pobutton.draw(screen): Audio("output.wav")
    if applybutton.draw(screen): 
        edit.apply(effects, PATH)

    if downbutton.draw(screen): 
        edit.dnld()

    if resetbutton.draw(screen):
        pygame.mixer.stop()

    screen.blit(rawt, (WIDTH-280, HEIGHT-90))
    draw_text(screen, "internet", font, (WIDTH-140, HEIGHT-75), WHITE)
    draw_text(screen, "synthesizer", font, (WIDTH-140, HEIGHT-45), WHITE)

    #     tE = 10
    # else: tE -= 1

    pygame.display.flip()
    clock.tick(60)

    if START:
        START = False
        edit.apply(effects, PATH)


# Cleanup
pygame.quit()
sys.exit()
