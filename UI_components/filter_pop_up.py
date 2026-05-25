import pygame
import json

from .input_box import InputBox
from .select_box import SelectBox


class FilterPopUp:
    
  '''
  This class implements a simple pop-up window to set filter options for the 
  options generation. It contains:
    - Two input boxes to set the minimum and maximum number of channels of the options.
    - A select box to choose the sorting option for the filtered results (max chan, min chan, min overlap)
  '''
    
    
  # Init function takes and parses all the parameters
  def __init__(self, font, json_path='./assistanceJSONs/filters.json'):
    self.font = font
    self.json_path = json_path
    self.width = 420
    self.height = 250
    self.active = False
    self.min_input = None
    self.max_input = None
    self.ok_rect = None
    self.cancel_rect = None

  # Open and close functions
  def open(self):
    self.active = True
    # Inputs will be positioned when drawing
    self.min_input = None
    self.max_input = None

  def close(self):
    self.active = False

  # Handle_event function:
  def handle_event(self, event, screen):
    # If not active, ignore events
    if not self.active:
      return None

    # ensure inputs positioned
    self._ensure_inputs(screen)
      
    # forward events to inputs
    self.min_input.handle_event(event)
    self.max_input.handle_event(event)
    self.sort_select.handle_event(event)
      
    # Handle button clicks for the OK and Cancel buttons
    if event.type == pygame.MOUSEBUTTONDOWN:
      if self.ok_rect and self.ok_rect.collidepoint(event.pos):
        self._save()
        self.close()
        return 'ok'
      if self.cancel_rect and self.cancel_rect.collidepoint(event.pos):
        self.close()
        return 'cancel'
    return None

  def _save(self):
    # Function in the function to parse integer values or None
    def parse_int(s):
      try:
        # The try is for weird inputs (squares, emojis...)
        s = s.strip()
        if s == '':
          return None
        return int(float(s))
      except Exception:
        return None
      
    # Build the object to save
    min_val = parse_int(self.min_input.text)
    max_val = parse_int(self.max_input.text)
    sort_val = self.sort_select.get_value()
    
    obj = {
        'min_channels': min_val,
        'max_channels': max_val,
        'sort_option': sort_val
    }
      
   
    with open(self.json_path, 'w') as f:
      json.dump(obj, f, indent=2)
    

  # Load function to read the current filter settings from the JSON file
  def _ensure_inputs(self, screen):
    # Get screen size and compute popup position
    sw, sh = screen.get_size()
    x = (sw - self.width) // 2
    y = (sh - self.height) // 2

    # Desired sizes
    input_w = 140
    input_h = 32
    btn_w = 80
    btn_h = 34
    desired_input_x = x + 120

    # Hardcoded label gap
    label_gap = 250

    # Compute allowed input x range so label (at input_x - label_gap) stays >= popup left + 8
    min_input_x = x + 8 + label_gap
    max_input_x = x + self.width - 8 - input_w

    # Resize the whole thing if there is not enough space for the label and inputs gap
    if min_input_x > max_input_x:
      # Calculate available width
      available_input_w = (x + self.width - 8) - (x + 8 + label_gap)
      min_width_allowed = 40 # Set a minimal width
      
      # If even with minimal width the layout doesn't fit, reduce the label gap
      if available_input_w < min_width_allowed:
        # fall back: reduce label_gap to fit minimal input width
        label_gap = max(8, (x + self.width - 8) - (x + 8) - min_width_allowed)
        available_input_w = (x + self.width - 8) - (x + 8 + label_gap)
      
      # Final input width after enforcing minimum and available space
      input_w = max(min_width_allowed, int(available_input_w))
      max_input_x = x + self.width - 8 - input_w

    # final input x clamped to allowable range
    input_x = max(min_input_x, min(desired_input_x, max_input_x))
    input_y1 = y + 40
    input_y2 = y + 90

    # Create or update inputs, passing the enforced label_gap
    if self.min_input is None:
      self.min_input = InputBox(input_x, input_y1, input_w, input_h, 'Min num of channels', '', self.font, label_gap=label_gap)
    else:
      self.min_input.rect.x = input_x
      self.min_input.rect.y = input_y1
      self.min_input.label_gap = label_gap

    if self.max_input is None:
      self.max_input = InputBox(input_x, input_y2, input_w, input_h, 'Max num of chanells', '', self.font, label_gap=label_gap)
    else:
      self.max_input.rect.x = input_x
      self.max_input.rect.y = input_y2
      self.max_input.label_gap = label_gap

    # Sorting select box placed below the inputs using the same vertical gap
    gap = input_y2 - input_y1
    select_y = input_y2 + gap
    # ensure it fits above buttons; clamp if necessary
    max_select_y = y + self.height - btn_h - 12 - input_h - 8
    if select_y > max_select_y:
        select_y = max_select_y
        # ensure select stays below input_y2
        min_select_y = input_y2 + 8
        if select_y < min_select_y:
            select_y = min_select_y

    # Create or update the select box, passing the enforced label_gap
    if getattr(self, 'sort_select', None) is None:
        self.sort_select = SelectBox(input_x, select_y, input_w, input_h, 'Sorting option', ['max chan', 'min chan', 'min overlap'], self.font, default_index=0, label_gap=label_gap)
    else:
        self.sort_select.rect.x = input_x
        self.sort_select.rect.y = select_y
        self.sort_select.rect.w = input_w
        self.sort_select.label_gap = label_gap

    # Decide whether the select should expand upwards or downwards
    if getattr(self, 'sort_select', None) is not None:
        n_opts = len(self.sort_select.options)
        needed_h = n_opts * (input_h + 2)
        available_below = (y + self.height - 8) - (self.sort_select.rect.bottom)
        available_above = (self.sort_select.rect.top) - (y + 8)
        # prefer below if it fits, otherwise use above if that fits, else pick larger space
        if available_below >= needed_h:
            self.sort_select.expand_up = False
        elif available_above >= needed_h:
            self.sort_select.expand_up = True
        else:
            self.sort_select.expand_up = (available_above > available_below)

    # OK / Cancel button positions
    btn_w = 80
    btn_h = 34
    self.ok_rect = pygame.Rect(x + self.width - btn_w - 16, y + self.height - btn_h - 12, btn_w, btn_h)
    self.cancel_rect = pygame.Rect(x + 16, y + self.height - btn_h - 12, btn_w, btn_h)

  def draw(self, screen):
    # If not active, ignore drawing
    if not self.active:
      return

    # Get screen size and compute popup position
    sw, sh = screen.get_size()
    x = (sw - self.width) // 2
    y = (sh - self.height) // 2

    # Draw semi-transparent overlay
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    screen.blit(overlay, (0, 0))

    # Popup background
    popup_rect = pygame.Rect(x, y, self.width, self.height)
    pygame.draw.rect(screen, (255, 255, 255), popup_rect)
    pygame.draw.rect(screen, (0, 0, 0), popup_rect, 2)

    # Title
    title_surf = self.font.render('Filter options', True, (0, 0, 0))
    screen.blit(title_surf, (x + (self.width - title_surf.get_width()) // 2, y + 8))

    # Ensure inputs positioned
    self._ensure_inputs(screen)

    # Draw inputs
    self.min_input.draw(screen)
    self.max_input.draw(screen)
    self.sort_select.draw(screen)

    # Draw buttons
    pygame.draw.rect(screen, (200, 200, 200), self.cancel_rect)
    pygame.draw.rect(screen, (0, 120, 200), self.ok_rect)

    cancel_s = self.font.render('Cancel', True, (0, 0, 0))
    ok_s = self.font.render('OK', True, (255, 255, 255))

    screen.blit(cancel_s, (self.cancel_rect.x + (self.cancel_rect.w - cancel_s.get_width()) // 2, self.cancel_rect.y + (self.cancel_rect.h - cancel_s.get_height()) // 2))
    screen.blit(ok_s, (self.ok_rect.x + (self.ok_rect.w - ok_s.get_width()) // 2, self.ok_rect.y + (self.ok_rect.h - ok_s.get_height()) // 2))
