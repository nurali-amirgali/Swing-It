import pygame
from pygame import gfxdraw
import sys
import math
import random
from collections import deque

pygame.init()

WIDTH, HEIGHT = 800, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED, vsync=1)
pygame.display.set_caption("Double pendulum")

clock = pygame.time.Clock()
FPS = 60

#the mass of the weight thingies at the bottom of each pendulum
m1 = 1
m2 = 1

#the lengths of the pendulums
l1 = 0.6
l2 = 0.4

#angle of the pendulum. 0 is down. 1 is the top one and 2 is the bottom pendulum
t1 = 0 #math.radians(170)
t2 = 0

#angular velocity
w1 = w2 = 0

#self explanitory (gravity)
g = 9.81

#anchor point
x0 = WIDTH/2
y0 = HEIGHT * 0.5

friction = 0.01

SCALE = 300

def compute_accelerations(t1, t2, w1, w2):
    delta = t1 - t2
    mass_term = 2 * m1 + m2
    coupling_term = m2 * math.cos(2 * delta)
    den = mass_term - coupling_term

    gravity_on_rod1 = -g * (2 * m1 + m2) * math.sin(t1)
    gravity_cross_term = -m2 * g * math.sin(t1 - 2 * t2)
    rod2_swing_effect = w2 ** 2 * l2
    rod1_swing_effect = w1 ** 2 * l1 * math.cos(delta)
    coupling_push = -2 * math.sin(delta) * m2 * (rod2_swing_effect + rod1_swing_effect)
    numerator_1 = gravity_on_rod1 + gravity_cross_term + coupling_push
    alpha1 = numerator_1 / (l1 * den)

    rod1_pull_from_swinging = w1 ** 2 * l1 * (m1 + m2)
    gravity_pull = g * (m1 + m2) * math.cos(t1)
    rod2_own_swing = w2 ** 2 * l2 * m2 * math.cos(delta)
    numerator_2 = 2 * math.sin(delta) * (rod1_pull_from_swinging + gravity_pull + rod2_own_swing)
    alpha2 = numerator_2 / (l2 * den)

    return alpha1, alpha2


def updateAngles(dt):
    global t1, t2, w1, w2
    dt = min(dt, 0.05)
    substeps = 32
    h = dt / substeps

    for _ in range(substeps):
        k1_dt1, k1_dt2 = w1, w2
        k1_dw1, k1_dw2 = compute_accelerations(t1, t2, w1, w2)

        k2_dt1, k2_dt2 = w1 + h/2 * k1_dw1, w2 + h/2 * k1_dw2
        k2_dw1, k2_dw2 = compute_accelerations(t1 + h/2 * k1_dt1, t2 + h/2 * k1_dt2, w1 + h/2 * k1_dw1, w2 + h/2 * k1_dw2)

        k3_dt1, k3_dt2 = w1 + h/2 * k2_dw1, w2 + h/2 * k2_dw2
        k3_dw1, k3_dw2 = compute_accelerations(t1 + h/2 * k2_dt1, t2 + h/2 * k2_dt2, w1 + h/2 * k2_dw1, w2 + h/2 * k2_dw2)

        k4_dt1, k4_dt2 = w1 + h * k3_dw1, w2 + h * k3_dw2
        k4_dw1, k4_dw2 = compute_accelerations(t1 + h * k3_dt1, t2 + h * k3_dt2, w1 + h * k3_dw1, w2 + h * k3_dw2)

        t1 += (h/6) * (k1_dt1 + 2 * k2_dt1 + 2 * k3_dt1 + k4_dt1)
        t2 += (h/6) * (k1_dt2 + 2 * k2_dt2 + 2 * k3_dt2 + k4_dt2)
        w1 += (h/6) * (k1_dw1 + 2 * k2_dw1 + 2 * k3_dw1 + k4_dw1)
        w2 += (h/6) * (k1_dw2 + 2 * k2_dw2 + 2 * k3_dw2 + k4_dw2)

        w1 *= 1 - friction * h
        w2 *= 1 - friction * h

def updateBottomWhileDragging(dt, alpha1):
    global t2, w2
    dt = min(dt, 0.05)
    substeps = 32
    h = dt / substeps
    for _ in range(substeps):
        Ax = l1 * (alpha1 * math.cos(t1) - w1**2 * math.sin(t1))
        Ay = l1 * (-alpha1 * math.sin(t1) - w1**2 * math.cos(t1))
        alpha2 = -(g / l2) * math.sin(t2) - (Ax * math.cos(t2) - Ay * math.sin(t2)) / l2
        w2 += alpha2 * h
        t2 += w2 * h
        w2 *= 1 - friction * h
        
draggingTop = False
dragLastW1 = 0
lastTopDragAngle = t1
alpha1 = 0
circleRadius = 20
lineWidth = 16

W1_SMOOTHING = 0.35      
ALPHA1_SMOOTHING = 0.25
MAX_W1 = 25           
MAX_ALPHA1 = 300

points = deque(maxlen=200)
running = True
while running:
    dt = clock.tick(FPS) / 1000.0 * 1
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouseX, mouseY = pygame.mouse.get_pos()
            distanceCircleTop = math.dist((x1,y1), (mouseX, mouseY))
            if distanceCircleTop <= (circleRadius + 50):
                draggingTop = True
                print("drag start")
    
    mouseButtons = pygame.mouse.get_pressed()
    if draggingTop:
        mouseX, mouseY = pygame.mouse.get_pos()
        dx = mouseX - x0
        dy = mouseY - y0
        
        radians = math.atan2(dx, dy)
        angleChange = (lastTopDragAngle - radians) / dt if dt > 0 else 0
        lastTopDragAngle = radians
        t1 = radians

        rawW1 = -angleChange
        w1 = w1 + W1_SMOOTHING * (rawW1 - w1)

        rawAlpha1 = -(w1 - dragLastW1) / dt if dt > 0 else 0
        alpha1 = alpha1 + ALPHA1_SMOOTHING * (rawAlpha1 - alpha1)
        dragLastW1 = w1

        w1 = max(-MAX_W1, min(MAX_W1, w1))
        alpha1 = max(-MAX_ALPHA1, min(MAX_ALPHA1, alpha1))

        updateBottomWhileDragging(dt, alpha1)

        if not mouseButtons[0]:
            draggingTop = False
    else:
        updateAngles(dt)
    
    x1 = x0 + (l1 * SCALE) * math.sin(t1)
    y1 = y0 + (l1 * SCALE) * math.cos(t1)
    x2 = x1 + (l2 * SCALE) * math.sin(t2)
    y2 = y1 + (l2 * SCALE) * math.cos(t2)
    
    points.append((x2, y2))
    
    screen.fill((30, 30, 30))
    
    if len(points) > 1:
        pygame.draw.lines(screen, (143, 31, 156), False, points, width=7)
    pygame.draw.line(screen, (255,255,255), (x0, y0), (x1, y1), width=lineWidth)
    pygame.draw.line(screen, (255,255,255), (x1, y1), (x2, y2), width=lineWidth)
    #pygame.draw.circle(screen, (74, 73, 73), (x0, y0), circleRadius, width=0)
    #pygame.draw.circle(screen, (86, 227, 5), (x1, y1), circleRadius, width=0)
    #pygame.draw.circle(screen, (227, 5, 5), (x2, y2), circleRadius, width=0)
    
    #top pendulum circle
    gfxdraw.filled_circle(screen, round(x0), round(y0), circleRadius, (74, 73, 73))
    gfxdraw.aacircle(screen, round(x0), round(y0), circleRadius, (74, 73, 73))
    
    #top pendulum circle
    gfxdraw.filled_circle(screen, round(x1), round(y1), circleRadius, (86, 227, 5))
    gfxdraw.aacircle(screen, round(x1), round(y1), circleRadius, (86, 227, 5))
    
    #bottom pendulum circle
    gfxdraw.filled_circle(screen, round(x2), round(y2), circleRadius, (227, 5, 5))
    gfxdraw.aacircle(screen, round(x2), round(y2), circleRadius, (227, 5, 5))
            
    pygame.display.flip()

pygame.quit()
sys.exit()
