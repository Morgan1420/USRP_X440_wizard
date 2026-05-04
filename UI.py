import pygame
from UI_components.inputBox import InputBox

pygame.init()

WIDTH, HEIGHT = 1000, 800 
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("USRP X440 Wizard")

font = pygame.font.Font(None, 32)


def run_ui(callback):
    clock = pygame.time.Clock()
    
    # Input fields
    input_fc = InputBox(150, 50, 140, 32, "Fc:", "10e6")
    input_bw = InputBox(150, 100, 140, 32, "BW:", "5e6")
    input_time = InputBox(150, 150, 140, 32, "Time:", "1s")
    input_num_chan = InputBox(150, 150, 140, 32, "Time:", "1s")

    # Indicator fields
    
    # Indicador del: sample rate, mínim de samples, mida mínima del fitxer

    # Capture button
    button_capture_width = 150
    button_capture_height = 50
    button_rect = pygame.Rect(WIDTH/2 - button_capture_width/2, HEIGHT - 100 - button_capture_height, button_capture_width, button_capture_height)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            input_fc.handle_event(event)
            input_bw.handle_event(event)
            input_time.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    callback(input_fc.text, input_bw.text, input_time.text)

        screen.fill((255, 255, 255))

        input_fc.draw(screen)
        input_bw.draw(screen)
        input_time.draw(screen)

        pygame.draw.rect(screen, (0, 200, 0), button_rect)
        button_capture_text = font.render("Run", True, (255, 255, 255))
        screen.blit(button_capture_text, (button_rect.x + button_capture_width/2 - button_capture_text.get_width()/2, button_rect.y + button_capture_height/2 - button_capture_text.get_height()/2))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()