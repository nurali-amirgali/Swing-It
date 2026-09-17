import pygame
import sys
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Double pendulum")

clock = pygame.time.Clock()
FPS = 60

#the mass of the weight thingies at the bottom of each pendulum
m1 = 1
m2 = 1

#the lengths of the pendulums
l1 = 0.4
l2 = 0.3

#angle of the pendulum. 0 is down. 1 is the top one and 2 is the bottom pendulum
t1 = math.radians(90)
t2 = 0

#angular velocity
w1 = w2 = 0

#angular acceleration 
a1 = a2 = 0

#self explanitory (gravity)
g = 9.81

#anchor point
x0 = WIDTH/2
y0 = HEIGHT * 0.3

SCALE = 300

def updateAngles(dt):
    global t1, t2, w1, w2, a1, a2, l1, l2, m1, m2
    delta = t1 - t2
        
    mass_term = 2 * m1 + m2
    coupling_term = m2 * math.cos(2 * delta)
    den = mass_term - coupling_term
    
    #top pendulum acceleration
    gravity_on_rod1 = -g * (2 * m1 + m2) * math.sin(t1)
    gravity_cross_term = -m2 * g * math.sin(t1 - 2 * t2)
    rod2_swing_effect = w2 ** 2 * l2
    rod1_swing_effect = w1 ** 2 * l1 * math.cos(delta)
    coupling_push = -2 * math.sin(delta) * m2 * (rod2_swing_effect + rod1_swing_effect)

    numerator_1 = gravity_on_rod1 + gravity_cross_term + coupling_push
    alpha1 = numerator_1 / (l1 * den)
    
    #bottom pendulum acceleration
    rod1_pull_from_swinging = w1 ** 2 * l1 * (m1 + m2)
    gravity_pull = g * (m1 + m2) * math.cos(t1)
    rod2_own_swing = w2 ** 2 * l2 * m2 * math.cos(delta)

    numerator_2 = 2 * math.sin(delta) * (rod1_pull_from_swinging + gravity_pull + rod2_own_swing)
    alpha2 = numerator_2 / (l2 * den)
    
    w1 += alpha1 * dt
    w2 += alpha2 * dt
    
    t1 += w1 * dt
    t2 += w2 * dt

running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    updateAngles(dt)
    
    x1 = x0 + (l1 * SCALE) * math.sin(t1)
    y1 = y0 + (l1 * SCALE) * math.cos(t1)
    x2 = x1 + (l2 * SCALE) * math.sin(t2)
    y2 = y1 + (l2 * SCALE) * math.cos(t2)
    
    screen.fill((30, 30, 30))
    
    pygame.draw.circle(screen, (255, 255, 255), (x0, y0), 10, width=0)
    pygame.draw.circle(screen, (86, 227, 5), (x1, y1), 10, width=0)
    pygame.draw.circle(screen, (227, 5, 5), (x2, y2), 10, width=0)
            
    pygame.display.flip()

pygame.quit()
sys.exit()
