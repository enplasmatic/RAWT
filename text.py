import pygame
import sys
import numpy as np

pygame.init()
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Parametric EQ Visualizer")
FONT = pygame.font.SysFont(None, 20)

# Define bands: each band has freq (Hz), gain (dB), Q
bands = [
    {'freq': 100, 'gain': 0, 'Q': 1},
    {'freq': 1000, 'gain': 0, 'Q': 1},
    {'freq': 5000, 'gain': 0, 'Q': 1},
]

# UI slider areas (for example)
slider_areas = [
    {'freq': pygame.Rect(50, 50, 120, 20),
     'gain': pygame.Rect(50, 80, 120, 20),
     'Q': pygame.Rect(50, 110, 120, 20)},
    {'freq': pygame.Rect(250, 50, 120, 20),
     'gain': pygame.Rect(250, 80, 120, 20),
     'Q': pygame.Rect(250, 110, 120, 20)},
    {'freq': pygame.Rect(450, 50, 120, 20),
     'gain': pygame.Rect(450, 80, 120, 20),
     'Q': pygame.Rect(450, 110, 120, 20)},
]

dragging = None

def draw_slider(rect, value, min_val, max_val):
    pygame.draw.rect(screen, (80, 80, 80), rect)
    # Draw filled portion
    filled_width = int((value - min_val) / (max_val - min_val) * rect.width)
    pygame.draw.rect(screen, (0, 150, 255), (rect.x, rect.y, filled_width, rect.height))
    # Draw text
    txt = FONT.render(f"{value:.2f}", True, (255, 255, 255))
    screen.blit(txt, (rect.x, rect.y - 20))

def freq_to_pos(freq):
    # Log scale: 20 Hz to 20000 Hz
    return np.interp(np.log10(freq), [np.log10(20), np.log10(20000)], [0, 1])

def pos_to_freq(pos):
    val = np.interp(pos, [0, 1], [np.log10(20), np.log10(20000)])
    return 10 ** val

def draw_freq_response():
    # Draw dummy frequency response combining bands
    w = WIDTH - 40
    h = 150
    top = HEIGHT - h - 50
    points = []
    for x in range(w):
        freq = pos_to_freq(x / w)
        # Sum simple peaks for visualization (not real filter calc)
        response = 0
        for b in bands:
            # Simple bell curve shape for visualization
            bw = b['Q'] * 100
            response += b['gain'] * np.exp(-0.5 * ((np.log(freq) - np.log(b['freq'])) / (bw/1000))**2)
        y = top + h/2 - response * 5  # scale response visually
        points.append((40 + x, int(y)))
    pygame.draw.lines(screen, (0, 255, 0), False, points, 2)
    # Axes
    pygame.draw.line(screen, (255,255,255), (40, top), (40, top + h))
    pygame.draw.line(screen, (255,255,255), (40, top + h/2), (40 + w, top + h/2))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            for i, area in enumerate(slider_areas):
                for param in ['freq', 'gain', 'Q']:
                    if area[param].collidepoint(mx, my):
                        dragging = (i, param)

        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = None

        elif event.type == pygame.MOUSEMOTION and dragging:
            i, param = dragging
            area = slider_areas[i][param]
            rel_x = max(0, min(area.width, event.pos[0] - area.x))
            val_ratio = rel_x / area.width
            if param == 'freq':
                bands[i]['freq'] = pos_to_freq(val_ratio)
            elif param == 'gain':
                bands[i]['gain'] = val_ratio * 24 - 12  # -12 to +12 dB
            elif param == 'Q':
                bands[i]['Q'] = val_ratio * 9.9 + 0.1  # 0.1 to 10

    screen.fill((30, 30, 30))

    # Draw sliders
    for i, area in enumerate(slider_areas):
        draw_slider(area['freq'], bands[i]['freq'], 20, 20000)
        draw_slider(area['gain'], bands[i]['gain'], -12, 12)
        draw_slider(area['Q'], bands[i]['Q'], 0.1, 10)
        # Labels
        y = area['freq'].y + 30
        screen.blit(FONT.render(f"Band {i+1}", True, (255,255,255)), (area['freq'].x, y - 40))
        screen.blit(FONT.render("Freq (Hz)", True, (180,180,180)), (area['freq'].x, y))
        screen.blit(FONT.render("Gain (dB)", True, (180,180,180)), (area['gain'].x, y))
        screen.blit(FONT.render("Q", True, (180,180,180)), (area['Q'].x, y))

    # Draw frequency response graph
    draw_freq_response()

    pygame.display.flip()
