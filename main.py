import asyncio
import pygame
from pygame import gfxdraw
import sys
import math
import random
from collections import deque

pygame.init()

WIDTH, HEIGHT = 800, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Double pendulum")

clock = pygame.time.Clock()
FPS = 60
BG_COLOR = (30, 30, 30)
DARK_OVERLAY = (0, 0, 0, 200)
TRANSPARENT = (0, 0, 0, 0)

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

regularFriction = 0.05
friction = regularFriction

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

font = pygame.font.SysFont(None, 35)
introFont = pygame.font.SysFont(None, 50)

draggingTop = False
dragLastW1 = 0
lastTopDragAngle = t1
alpha1 = 0
circleRadius = 20
lineWidth = 16

OFF = 0
FADE_IN = 1
ON = 2
FADE_OUT = 3

textOpacity = 0
opacityState = OFF
timeSinceFaded = 0
fadeInSpeed = 2
fadeOutSpeed = 2
showTime = 1

W1_SMOOTHING = 0.35
ALPHA1_SMOOTHING = 0.25
MAX_W1 = 25
MAX_ALPHA1 = 300

INTOR_OFF = 0
SHOW_CIRCLE = 1
SHOW_CONTROLS = 2

introTimes = [1, 5, 5, 2]
introPhase = 0
introTimer = 0
controlTexts = [
    "C/H = controls",
    "P = pause",
    "UP = increase sim speed",
    "DOWN = decrease sim speed",
    "R = reset simulation",
    "L = apply random force",
    "B = apply braking"
]

introHighlightOpacity = 0
introHighlightFadeSpeed = 2
introTextOpacity = 0
introTextFadeSpeed = 3.4

ControlsTextOpacity = 0
ControlsTextFadeSpeed = 2
showControls = False

points = deque(maxlen=200)
paused = False
simSpeed = 1

# these get set on the first frame before they're read
x1 = y1 = x2 = y2 = 0

async def main():
    global animationDt, dt, running, paused, simSpeed, opacityState, timeSinceFaded
    global draggingTop, dragLastW1, lastTopDragAngle, alpha1, points, t1, t2, w1, w2
    global friction, showControls, x1, y1, x2, y2
    global introTimer, introPhase, introHighlightOpacity, introTextOpacity, ControlsTextOpacity
    global textOpacity

    running = True
    while running:
        animationDt = clock.tick(FPS) / 1000.0
        dt = animationDt * simSpeed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    if introPhase != 1 and introPhase != 2 and introPhase != 0:
                        paused = not paused
                elif event.key == pygame.K_r:
                    if introPhase != 1 and introPhase != 2 and introPhase != 0:
                        t1 = t2 = 0
                        w1 = w2 = 0
                        draggingTop = False
                        dragLastW1 = 0
                        lastTopDragAngle = t1
                        alpha1 = 0
                        points = deque(maxlen=200)
                        simSpeed = 1
                        paused = False

                elif event.key == pygame.K_UP:
                    if introPhase != 1 and introPhase != 2 and introPhase != 0:
                        if simSpeed < 20:
                            simSpeed += 0.5
                            if opacityState == OFF or opacityState == FADE_OUT:
                                opacityState = FADE_IN
                                timeSinceFaded = 0

                elif event.key == pygame.K_DOWN:
                    if introPhase != 1 and introPhase != 2 and introPhase != 0:
                        if simSpeed > 0.5:
                            simSpeed -= 0.5
                            if opacityState == OFF or opacityState == FADE_OUT:
                                opacityState = FADE_IN
                                timeSinceFaded = 0

                elif event.key == pygame.K_c or event.key == pygame.K_h:
                    if introPhase != 1 and introPhase != 2 and introPhase != 0:
                        showControls = not showControls

                elif event.key == pygame.K_l:
                    if w1 > 0:
                        w1 += random.randint(0, 10)
                    else:
                        w1 += random.randint(-10, 0)

            keys = pygame.key.get_pressed()
            if keys[pygame.K_b]:
                friction = 0.99
            else:
                friction = regularFriction

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not paused:
                    mouseX, mouseY = pygame.mouse.get_pos()
                    distanceCircleTop = math.dist((x1, y1), (mouseX, mouseY))
                    increaseRadius = min(20 * abs(w1), 200)
                    if distanceCircleTop <= (circleRadius + increaseRadius):
                        draggingTop = True

        if not paused:
            mouseButtons = pygame.mouse.get_pressed()
            if draggingTop:
                mouseX, mouseY = pygame.mouse.get_pos()
                dx = mouseX - x0
                dy = mouseY - y0

                radians = math.atan2(dx, dy)
                diff = radians - lastTopDragAngle
                diff = (diff + math.pi) % (2 * math.pi) - math.pi
                angleChange = -diff / dt if dt > 0 else 0
                lastTopDragAngle = radians
                t1 = radians

                rawW1 = -angleChange / 2
                w1 = w1 + W1_SMOOTHING * (rawW1 - w1)
                w1 = max(-MAX_W1, min(MAX_W1, w1))

                rawAlpha1 = -(w1 - dragLastW1) / dt if dt > 0 else 0
                alpha1 = alpha1 + ALPHA1_SMOOTHING * (rawAlpha1 - alpha1)
                dragLastW1 = w1
                alpha1 = max(-MAX_ALPHA1, min(MAX_ALPHA1, alpha1))
                dragLastW1 = w1

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

        screen.fill(BG_COLOR)

        if len(points) > 1:
            line_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

            for i in range(len(points) - 1):
                alpha = int(255 * i / max(1, len(points) - 2))

                pygame.draw.line(
                    line_surface,
                    (143, 31, 156, alpha),
                    points[i],
                    points[i + 1],
                    width=7
                )

            screen.blit(line_surface, (0, 0))
        pygame.draw.line(screen, (255, 255, 255), (x0, y0), (x1, y1), width=lineWidth)
        pygame.draw.line(screen, (255, 255, 255), (x1, y1), (x2, y2), width=lineWidth)

        gfxdraw.filled_circle(screen, round(x0), round(y0), circleRadius, (74, 73, 73))
        gfxdraw.aacircle(screen, round(x0), round(y0), circleRadius, (74, 73, 73))

        topPendulumColor = (86, 227, 5) if not draggingTop else (68, 168, 10)
        gfxdraw.filled_circle(screen, round(x1), round(y1), circleRadius, topPendulumColor)
        gfxdraw.aacircle(screen, round(x1), round(y1), circleRadius, topPendulumColor)

        gfxdraw.filled_circle(screen, round(x2), round(y2), circleRadius, (227, 5, 5))
        gfxdraw.aacircle(screen, round(x2), round(y2), circleRadius, (227, 5, 5))

        if paused:
            pygame.draw.rect(screen, (255, 255, 255), (10, 10, 15, 40), border_radius=0)
            pygame.draw.rect(screen, (255, 255, 255), (35, 10, 15, 40), border_radius=0)

        if opacityState != OFF:
            if opacityState == FADE_IN:
                textOpacity += fadeInSpeed * animationDt
                textOpacity = min(textOpacity, 1)
                if textOpacity >= 1:
                    opacityState = ON
            elif opacityState == FADE_OUT:
                textOpacity -= fadeOutSpeed * animationDt
                textOpacity = max(textOpacity, 0)
                if textOpacity <= 0:
                    opacityState = OFF
            elif opacityState == ON:
                timeSinceFaded += animationDt
                if timeSinceFaded >= showTime:
                    opacityState = FADE_OUT
            width, _ = font.size(f"Speed set to: {round(simSpeed, 2)}X")
            text = font.render(f"Speed set to: {round(simSpeed, 2)}X", True, (255, 255, 255))
            text.set_alpha(255 * textOpacity)
            screen.blit(text, ((WIDTH / 2) - (width / 2), 10))

        if introPhase != len(introTimes) - 1:
            introTimer += animationDt
            introPhaseDuration = introTimes[introPhase]
            if introTimer >= introPhaseDuration:
                introTimer = 0
                introPhase += 1

        if introPhase == 1:
            introPhaseDuration = introTimes[introPhase]
            timeLeft = introPhaseDuration - introTimer
            if timeLeft <= (1 / introHighlightFadeSpeed) + 0.5:
                introHighlightOpacity -= introHighlightFadeSpeed * animationDt
                introHighlightOpacity = max(introHighlightOpacity, 0)

                introTextOpacity -= introTextFadeSpeed * animationDt
                introTextOpacity = max(introTextOpacity, 0)
            else:
                introHighlightOpacity += introHighlightFadeSpeed * animationDt
                introHighlightOpacity = min(introHighlightOpacity, 0.7)

                introTextOpacity += introTextFadeSpeed * animationDt
                introTextOpacity = min(introTextOpacity, 1)
            circle_pos = (x1, y1)

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 255 * introHighlightOpacity))

            pygame.draw.circle(overlay, TRANSPARENT, circle_pos, circleRadius)

            screen.blit(overlay, (0, 0))

            text1 = introFont.render("drag the green handle around", True, (255, 255, 255))
            text2 = introFont.render("to swing the pendulum", True, (255, 255, 255))

            text1.set_alpha(255 * introTextOpacity)
            text2.set_alpha(255 * introTextOpacity)

            startY = 75
            screen.blit(text1, ((WIDTH / 2) - (text1.get_width() / 2), startY))
            screen.blit(text2, ((WIDTH / 2) - (text2.get_width() / 2), startY + 35))

        if introPhase == 2:
            introPhaseDuration = introTimes[introPhase]
            timeLeft = introPhaseDuration - introTimer
            if timeLeft <= (1 / ControlsTextFadeSpeed) + 0.5:
                showControls = False
            else:
                showControls = True

        if showControls:
            ControlsTextOpacity += ControlsTextFadeSpeed * animationDt
            ControlsTextOpacity = min(ControlsTextOpacity, 1)
        else:
            ControlsTextOpacity -= ControlsTextFadeSpeed * animationDt
            ControlsTextOpacity = max(ControlsTextOpacity, 0)

        if ControlsTextOpacity:
            startY = 200
            changeY = 30
            x = 5
            for i, control in enumerate(controlTexts):
                width, _ = font.size(control)
                text = font.render(control, True, (255, 255, 255))
                text.set_alpha(255 * ControlsTextOpacity)
                screen.blit(text, (x, startY + (changeY * i)))

        pygame.display.flip()

        # hand control back to the browser each frame - REQUIRED for pygbag
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())