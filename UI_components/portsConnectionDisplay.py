import pygame


class PortsConnectionDisplay:
    '''
        Display a horizontal ports row as dots inside a rounded rectangle.
        Click a dot to toggle selection. Use `set_rect` to update layout.
    '''

    # Init function
    def __init__(self, rect, num_ports=8, labels=None, font=None, edge_padding=28, gap_after=4, gap_multiplier=1.3, dot_radius=8, hit_tolerance=12):
        self.rect = rect if isinstance(rect, pygame.Rect) else pygame.Rect(rect)
        self.num_ports = int(num_ports)
        if labels and len(labels) >= self.num_ports:
            self.labels = labels[: self.num_ports]
        else:
            labels = labels or []
            self.labels = list(labels) + [f"P{i+1}" for i in range(len(labels), self.num_ports)]
        self.font = font
        self.edge_padding = int(edge_padding)
        self.gap_after = int(gap_after)
        self.gap_multiplier = float(gap_multiplier)
        self.dot_radius = int(dot_radius)
        self.hit_tolerance = int(hit_tolerance)
        self.selected = [False] * self.num_ports
        self.centers = []
        self.dot_rects = []
        self._compute_layout()

    # Callable function to update layout when rect or num_ports changes
    def set_rect(self, rect):
        self.rect = rect if isinstance(rect, pygame.Rect) else pygame.Rect(rect)
        self._compute_layout()

    


    # Assistance function to compute layout of ports based on current rect and num_ports
    def _compute_layout(self):
        # Get the rectangle for layout
        r = self.rect
        
        # If width is too small or there are no ports, clear centers and rects
        if r.w <= 0 or self.num_ports <= 0:
            self.centers = []
            self.dot_rects = []
            return
        
        # Compute the inner boundaries for port placement
        inner_left = r.x + self.edge_padding + self.dot_radius
        inner_right = r.right - self.edge_padding - self.dot_radius
        
        # Calculate available width and distribute ports with optional gap multiplier 
        available = max(0, inner_right - inner_left)        
        num_gaps = max(1, self.num_ports - 1)
        gaps = [1.0] * num_gaps
        gap_index = max(0, min(num_gaps - 1, self.gap_after - 1))
        gaps[gap_index] = self.gap_multiplier
        
        # Calculate total gap units and unit width
        total = sum(gaps)
        unit = available / total if total != 0 else 0
        
        # Compute center positions for each port based on gaps
        centers = []
        cx = inner_left
        cy = r.y + r.h // 2 # vertical center of the rectangle
        centers.append((int(round(cx)), int(round(cy))))
        for g in gaps:
            cx += unit * g 
            centers.append((int(round(cx)), int(round(cy))))
        self.centers = centers[: self.num_ports]
        
        # Compute rectangles for hit detection around each dot
        self.dot_rects = [pygame.Rect(x - self.dot_radius, y - self.dot_radius, self.dot_radius * 2, self.dot_radius * 2) for x, y in self.centers]

    # Handle function:º
    def handle_event(self, event):
        # Mouse click
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Find if click is within any dot rect and return the index of the toggled port
            pos = event.pos
            for i, drect in enumerate(self.dot_rects):
                if drect.collidepoint(pos):
                    self.selected[i] = not self.selected[i]
                    return i
        return None

    # Get the index of the port at a given position
    def get_dot_index_at(self, pos):
        # If there are no centers this is pointless
        if not self.centers:
            return None
        
        # Examine each center to see if the positon is within the hit tolerance of the dot
        mx, my = pos # click position
        best_dist2 = (self.dot_radius + self.hit_tolerance) ** 2
        for i, (cx, cy) in enumerate(self.centers):
            dx = mx - cx # horizontal distance from click to center
            dy = my - cy # vertical distance from click to center
            d2 = dx * dx + dy * dy # squared distance from click to center
            
            # Is this dot is within the hit tolerance we assume it's a hit and return the index
            if d2 <= best_dist2:
                return i 
        return None

    # Get the center coordinates of a dot by index
    def get_dot_center(self, idx):
        return self.centers[int(idx)]
        

    # Get the labels of the currently selected ports
    def get_selected_labels(self):
        return [self.labels[i] for i, s in enumerate(self.selected) if s]

    # Draw function:
    def draw(self, surface):
        r = self.rect
        pygame.draw.rect(surface, (240, 240, 240), r, border_radius=6)
        pygame.draw.rect(surface, (200, 200, 200), r, 2, border_radius=6)
        for i, (cx, cy) in enumerate(self.centers):
            sel = self.selected[i]
            inner_color = (0, 120, 0) if sel else (255, 255, 255)
            pygame.draw.circle(surface, (0, 0, 0), (cx, cy), self.dot_radius + 2)
            pygame.draw.circle(surface, inner_color, (cx, cy), self.dot_radius)
            pygame.draw.circle(surface, (0, 0, 0), (cx, cy), self.dot_radius, 1)
            if self.font:
                lbl = self.font.render(self.labels[i], True, (0, 0, 0))
                surface.blit(lbl, (cx - lbl.get_width() // 2, cy + self.dot_radius + 6))


class PortsController:
    """High-level controller that owns a PortsConnectionDisplay and port selection state.

    This moves simple port-selection state and event handling out of HardwareConfigScreen
    so the component encapsulates its own behaviour.
    """
    def __init__(self, rect, num_ports=8, labels=None, font=None, **display_kwargs):
        self.display = PortsConnectionDisplay(rect, num_ports=num_ports, labels=labels or [], font=font, **display_kwargs)
        self.num_ports = self.display.num_ports
        self.ports = list(self.display.labels)
        self.selected_ports = {p: False for p in self.ports}

    def set_rect(self, rect):
        self.display.set_rect(rect)

    def handle_event(self, event):
        """Forward event to the underlying display and toggle selection state.

        Returns the toggled port index or None.
        """
        idx = self.display.handle_event(event)
        if idx is not None:
            idx = int(idx)
            label = self.ports[idx]
            self.selected_ports[label] = not self.selected_ports.get(label, False)
            # Ensure visual state matches
            try:
                self.display.selected[idx] = self.selected_ports[label]
            except Exception:
                pass
            return idx
        return None

    def set_selected_by_index(self, idx, value):
        try:
            idx = int(idx)
            self.display.selected[idx] = bool(value)
            self.selected_ports[self.ports[idx]] = bool(value)
        except Exception:
            pass

    def get_selected_labels(self):
        return [p for p, v in self.selected_ports.items() if v]

    def get_dot_index_at(self, pos):
        return self.display.get_dot_index_at(pos)

    def get_dot_center(self, idx):
        try:
            return self.display.get_dot_center(idx)
        except Exception:
            return None

    def draw(self, surface):
        self.display.draw(surface)


class PartialOptionsBoxesDisplay:
    '''
        Render a grid/list of small boxes representing partial_option options.

        Each partial_option option may expand into N sub-boxes (for multi-channel partial_options);
        each sub-box shows a small dot at left and two lines with start/end frequencies.
    '''
    # Init function
    def __init__(self, rect, font, box_w=160, box_h=48, padding=8, dot_radius=6, hit_tolerance=12):
        self.rect = rect if isinstance(rect, pygame.Rect) else pygame.Rect(rect)
        self.font = font
        self.box_w = int(box_w)
        self.box_h = int(box_h)
        self.padding = int(padding)
        self.dot_radius = int(dot_radius)
        self.hit_tolerance = int(hit_tolerance)
        self.partial_options = [] # Grouped partial_options: list of partial_option dicts passed via `set_partial_options()`
        self.zone_boxes = [] # zone-wise boxes: list of lists [[(s,e), ...], ...]
        self.zone_titles = [] # titles for each zone
        self.boxes = []  # flattened list of (f_start, f_end)
        self.box_rects = []
        self.dot_centers = []
        self.zone_rects = []
        self.zone_box_rects = []

    # Callable function to update layout when rect changes
    def set_rect(self, rect):
        self.rect = rect if isinstance(rect, pygame.Rect) else pygame.Rect(rect)
        self._compute_layout()

    # Callable function to set partial_options and compute zones and boxes
    def set_partial_options(self, partial_options):
        # Get the partial_options
        self.partial_options = list(partial_options) if partial_options else []
        zones = []
        titles = []

        # For each partial, determine its frequency range and how many sub-channels it has (if any).
        for i, p in enumerate(self.partial_options):
            # Get frequency range for this partial
            f0 = float(p.get('f_start', 0))
            f1 = float(p.get('f_end', 0))
            
            # CHANNELS
            num_sub = 1
            if isinstance(p.get('channels'), list):
                # If 'channels' is a list, we assume each entry corresponds to a sub-channel
                num_sub = max(1, len(p.get('channels')))
            else:
                # Otherwise, look for common keys that might indicate the number of channels (e.g., 'num_channels', 'chans', etc.)
                for k in ('num_channels', 'num_chans', 'chans', 'chans_needed', 'n_chans'):
                    if k in p:
                        try:
                            num_sub = max(1, int(p.get(k) or 1))
                        except Exception:
                            num_sub = 1
                        break
            
            # ZONES
            zone = []
            span = f1 - f0
            if num_sub <= 1 or span <= 0:
                # If there are no sub-chanels 
                zone.append((f0, f1))
            else:
                # If there are sub-channels, divide the frequency range into equal parts for each sub-channel
                piece = span / num_sub
                for j in range(num_sub):
                    s = f0 + j * piece
                    e = f0 + (j + 1) * piece
                    zone.append((s, e))

            zones.append(zone)

            # Title: prefer explicit title field, otherwise use formatted range
            t = p.get('title') or p.get('name')
            if not t:
                t = f"partial_option {i+1}: {self._format_freq(f0)}–{self._format_freq(f1)}"
            titles.append(t)

        self.zone_boxes = zones
        self.zone_titles = titles

        # Build flattened boxes for compatibility
        flat = []
        for z in zones:
            for bb in z:
                flat.append(bb)

        self.boxes = flat
        # compute layout now that boxes are available
        self._compute_layout()

    # Assistance function to format frequencies
    def _format_freq(self, f):
        f = float(f)
        
        if f >= 1e9:
            return f"{f/1e9:.3f} GHz"
        if f >= 1e6:
            return f"{f/1e6:.3f} MHz"
        if f >= 1e3:
            return f"{f/1e3:.1f} kHz"
        return f"{int(f)} Hz"

    # Draw function:
    def draw(self, surface):
        # Draw background
        r = self.rect
        pygame.draw.rect(surface, (250, 250, 250), r)

        # Ensure layout computed
        if not getattr(self, 'box_rects', None):
            self._compute_layout()

        # Draw zones horizontally
        for zi, zrect in enumerate(getattr(self, 'zone_rects', [])):
            # zone background and border
            pygame.draw.rect(surface, (245, 245, 245), zrect, border_radius=6)
            pygame.draw.rect(surface, (200, 200, 200), zrect, 1, border_radius=6)

            # title
            title = self.zone_titles[zi] if zi < len(self.zone_titles) else f"partial_option {zi+1}"
            if self.font:
                ttl = self.font.render(title, True, (0, 0, 0))
                tx = zrect.x + max(8, (zrect.w - ttl.get_width()) // 2)
                ty = zrect.y + 6
                surface.blit(ttl, (tx, ty))

            # draw boxes for this zone
            for box_rect in (self.zone_box_rects[zi] if zi < len(self.zone_box_rects) else []):
                pygame.draw.rect(surface, (230, 230, 230), box_rect, border_radius=6)
                pygame.draw.rect(surface, (180, 180, 180), box_rect, 1, border_radius=6)

            # draw dots and text using flattened rects (preserves previous ordering)
        for idx, box_rect in enumerate(getattr(self, 'box_rects', [])):
            # left dot
            dot_cx, dot_cy = self.dot_centers[idx]
            pygame.draw.circle(surface, (0, 0, 0), (dot_cx, dot_cy), self.dot_radius + 1)
            pygame.draw.circle(surface, (0, 120, 0), (dot_cx, dot_cy), self.dot_radius)

            # texts
            txt_x = dot_cx + self.dot_radius + 10
            s, e = self.boxes[idx]
            if self.font:
                top_txt = self.font.render(self._format_freq(s), True, (0, 0, 0))
                bot_txt = self.font.render(self._format_freq(e), True, (80, 80, 80))
                surface.blit(top_txt, (txt_x, box_rect.y + 6))
                surface.blit(bot_txt, (txt_x, box_rect.y + 6 + top_txt.get_height()))


    def _append_flat_box(self, brect):
        self.box_rects.append(brect)
        dot_cx = brect.x + 12
        dot_cy = brect.y + brect.h // 2
        self.dot_centers.append((int(dot_cx), int(dot_cy)))

    def _compute_layout(self):
        r = self.rect
        self.box_rects = []
        self.dot_centers = []
        self.zone_rects = []
        self.zone_box_rects = []

        if not self.zone_boxes:
            # fallback to simple grid if there are no zones
            per_row = max(1, (r.w + self.padding) // (self.box_w + self.padding))
            x0 = r.x + self.padding
            y0 = r.y + self.padding
            
            # compute minimal content height from font
            box_h_layout = 50
            
            for idx, (s, e) in enumerate(self.boxes):
                row = idx // per_row
                col = idx % per_row
                x = x0 + col * (self.box_w + self.padding)
                y = y0 + row * (box_h_layout + self.padding)
                box_rect = pygame.Rect(x, y, self.box_w, box_h_layout)
                self._append_flat_box(box_rect)
            return

        # Compute equal-width zones across available width
        num_z = max(1, len(self.zone_boxes))
        total_w = max(0, r.w - 2 * self.padding)
        zone_w = total_w / num_z if num_z > 0 else total_w
        x0 = r.x + self.padding
        y0 = r.y + self.padding
        available_h = max(0, r.h - 2 * self.padding)

        flat_index = 0
        for zi, zboxes in enumerate(self.zone_boxes):
            zx = int(round(x0 + zi * zone_w))
            # ensure last zone reaches right edge to avoid gaps from rounding
            if zi == num_z - 1:
                zw = int(round(r.x + r.w - self.padding - zx))
            else:
                zw = int(round(zone_w))
            zrect = pygame.Rect(zx, y0, zw, available_h)
            self.zone_rects.append(zrect)

            # title area height (use get_height which excludes extra leading)
            title_h = (self.font.get_height() + 4) if self.font else 16
            inner_y = zrect.y + title_h + 6
            
            box_h_zone = 50 #desired_h if desired_h <= per_box_available else per_box_available
            zone_box_rects = []
            for j, (s, e) in enumerate(zboxes):
                bx = zrect.x + self.padding
                bw = max(24, zrect.w - 2 * self.padding)
                by = inner_y + j * (box_h_zone + self.padding)
                brect = pygame.Rect(bx, int(by), int(bw), int(box_h_zone))
                zone_box_rects.append(brect)
                self._append_flat_box(brect)
                flat_index += 1

            self.zone_box_rects.append(zone_box_rects)

    # Get dot functions: for the index and the center coordinates
    def get_dot_index_at(self, pos):
        for i, dcenter in enumerate(getattr(self, 'dot_centers', []) or []):
            dx = pos[0] - dcenter[0]
            dy = pos[1] - dcenter[1]
            if dx * dx + dy * dy <= (self.dot_radius + self.hit_tolerance) ** 2:
                return i
        return None
    def get_dot_center(self, idx):
        return self.dot_centers[int(idx)]
        

