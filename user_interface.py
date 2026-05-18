import pygame
import json
from processing_scripts.generate_options import generateCompleteOptions, generatePartialOptions, processInputs
from processing_scripts import filter_options as filter_mod


# Pygame things
pygame.init()

WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("USRP X440 Wizard")

font = pygame.font.Font(None, 32)

# Component classes moved to UI_components
from UI_components.input_box import InputBox
from UI_components.options_scroll_area import OptionsScrollArea
from UI_components.filter_pop_up import FilterPopUp


# Game main function
def run_ui(callback):
    clock = pygame.time.Clock()

    # ------- INPUTS
    # Multipliers
    fc_multipliers = [("M", 1e6), ("G", 1e9)]
    bw_multipliers = [("M", 1e6), ("G", 1e9)]
    time_multipliers = [("", 1), ("m", 1e-3)]

    # Graphics
    input_f_min = InputBox(150, 50, 140, 32, "F_min:", "1", font, multipliers=fc_multipliers, unit="Hz", default_multiplier_index=3)
    input_f_max = InputBox(150, 100, 140, 32, "F_max:", "2", font, multipliers=bw_multipliers, unit="Hz", default_multiplier_index=3) 
    input_time = InputBox(WIDTH/2 + 150, 50, 140, 32, "Temps:", "1", font, multipliers=time_multipliers, unit="s")
    # ------- "Genrar Opcions" button
    # Positioning
    inputs_bottom = max(input_f_min.rect.bottom, input_f_max.rect.bottom, input_time.rect.bottom)
    options_button_width = 200
    options_button_height = 40
    options_button_rect = pygame.Rect(WIDTH/2 - options_button_width/2, inputs_bottom + 20, options_button_width, options_button_height)

    # Filter button to the right of "Generar Opcions"
    filter_button_width = 120
    filter_button_rect = pygame.Rect(options_button_rect.right + 12, options_button_rect.y, filter_button_width, options_button_height)

    # After click text
    are_inputs_valid = False
    options_button_text = ""

    # ------- Options scroll area (80% of screen)
    area_w = int(0.8 * WIDTH)
    area_h = int(0.8 * HEIGHT)
    area_x = (WIDTH - area_w) // 2
    # place area start below potential button text; reserve margin
    area_y = options_button_rect.bottom + 60
    # shrink if overflowing
    if area_y + area_h + 80 > HEIGHT:
        area_h = max(100, HEIGHT - area_y - 80)

    options_area = OptionsScrollArea(area_x, area_y, area_w, area_h, font)
    options_area.refresh()

    # Filter popup
    filter_popup = FilterPopUp(font)

    # ------- Main loop
    running = True
    while running:
        # Events loop
        for event in pygame.event.get():
            # Quit event
            if event.type == pygame.QUIT:
                running = False

            # If popup active, let it handle events first (blocks underlying UI)
            if filter_popup.active:
                res = filter_popup.handle_event(event, screen)
                if res == 'ok':
                    # reload any filters if needed; nothing more to do here
                    pass
                continue

            # Handle input_boxes events
            input_f_min.handle_event(event)
            input_f_max.handle_event(event)
            input_time.handle_event(event)

            # Forward event to options area (handles clicks/scroll)
            options_area.handle_event(event)

            # Handle button clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                # "Generar Opcions" button click
                if options_button_rect.collidepoint(event.pos):
                    # Build numeric representations of inputs
                    try:
                        fmin_val = float(input_f_min.text) * input_f_min.get_multiplier_value()
                        fmax_val = float(input_f_max.text) * input_f_max.get_multiplier_value()
                        time_val = float(input_time.text) * input_time.get_multiplier_value()
                    except ValueError:
                        print("Error: Please enter valid numeric values.")
                        fmin_val = fmax_val = time_val = None

                    # Check if values are valid
                    are_inputs_valid, userInputs = processInputs(f_min=fmin_val, f_max=fmax_val, time=time_val)
                    if are_inputs_valid:
                        # Generate options
                        print("Generating options...")
                        p_ok = generatePartialOptions(userInputs["f_min"], userInputs["f_max"], './assistanceJSONs/mcr_converter_rates_table.json', './assistanceJSONs/partialOptions.json')
                        if p_ok:
                            c_ok = generateCompleteOptions(userInputs["f_min"], userInputs["f_max"], './assistanceJSONs/partialOptions.json')
                            if c_ok:
                                f_ok = filter_mod.filter_and_sort('./assistanceJSONs/completeOptions.json', './assistanceJSONs/filters.json')
                                
                                if f_ok:
                                    # Refresh the options area
                                    options_area.refresh()
                                else:
                                    options_button_text = "Error: No s'han pogut filtrar les opcions completes."
                            else:
                                options_button_text = "Error: No s'han pogut generar les opcions completes."
                        else:
                            options_button_text = "Error: No s'han pogut generar les opcions parcials."
                    else:
                        options_button_text = userInputs # User inputs contains the error message in this case
                # Filter button click
                if filter_button_rect.collidepoint(event.pos):
                    filter_popup.open()
                    
                    
                        
                        

        # ------- Graphics
        # Background
        screen.fill((255, 255, 255))

        # Input_boxes
        input_f_min.draw(screen)
        input_f_max.draw(screen)
        input_time.draw(screen)

        # "Genrar Opcions" button
        pygame.draw.rect(screen, (0, 120, 200), options_button_rect)
        options_text = font.render("Genrar Opcions", True, (255, 255, 255))
        screen.blit(options_text, (options_button_rect.x + options_button_width/2 - options_text.get_width()/2, options_button_rect.y + options_button_height/2 - options_text.get_height()/2))

        # Filter button (to the right)
        pygame.draw.rect(screen, (120, 120, 120), filter_button_rect)
        ftext = font.render("Filters", True, (255, 255, 255))
        screen.blit(ftext, (filter_button_rect.x + (filter_button_rect.w - ftext.get_width())/2, filter_button_rect.y + (filter_button_rect.h - ftext.get_height())/2))

        # Button text (error/warning)
        if not are_inputs_valid:
            text_color = (200, 0, 0) if options_button_text.startswith("Error") else (200, 100, 0)
            options_button_text_surf = font.render(options_button_text, True, text_color)
            screen.blit(options_button_text_surf, (WIDTH/2 - options_button_text_surf.get_width()/2, options_button_rect.bottom + 10))
        else:
            options_button_text_surf = font.render(options_button_text, True, (0, 150, 0))
            screen.blit(options_button_text_surf, (WIDTH/2 - options_button_text_surf.get_width()/2, options_button_rect.bottom + 10))
        # Draw options scroll area
        options_area.draw(screen)
        # Draw filter popup if active
        filter_popup.draw(screen)
        # Update display
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()