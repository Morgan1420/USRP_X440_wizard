import pygame


class PortsConnectionDisplay:
    """
Display a horizontal ports row as dots inside a rounded rectangle.
    Click a dot to toggle selection. Use `set_rect` to update layout.
    """

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

    def set_rect(self, rect):
        self.rect = rect if isinstance(rect, pygame.Rect) else pygame.Rect(rect)
        self._compute_layout()

    def _compute_layout(self):
        r = self.rect
        if r.w <= 0 or self.num_ports <= 0:
            self.centers = []
            self.dot_rects = []
            return
        inner_left = r.x + self.edge_padding + self.dot_radius
        inner_right = r.right - self.edge_padding - self.dot_radius
        available = max(0, inner_right - inner_left)
        num_gaps = max(1, self.num_ports - 1)
        gaps = [1.0] * num_gaps
        gap_index = max(0, min(num_gaps - 1, self.gap_after - 1))
        gaps[gap_index] = self.gap_multiplier
        total = sum(gaps)
        unit = available / total if total != 0 else 0
        centers = []
        cx = inner_left
        cy = r.y + r.h // 2
        centers.append((int(round(cx)), int(round(cy))))
        for g in gaps:
            cx += unit * g
            centers.append((int(round(cx)), int(round(cy))))
        self.centers = centers[: self.num_ports]
        self.dot_rects = [pygame.Rect(x - self.dot_radius, y - self.dot_radius, self.dot_radius * 2, self.dot_radius * 2) for x, y in self.centers]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            for i, drect in enumerate(self.dot_rects):
                if drect.collidepoint(pos):
                    self.selected[i] = not self.selected[i]
                    return i
        return None

    def get_dot_index_at(self, pos):
        """Return the nearest port index if `pos` is within tolerance, else None."""
        if not self.centers:
            return None
        mx, my = pos
        best = None
        best_dist2 = (self.dot_radius + self.hit_tolerance) ** 2
        for i, (cx, cy) in enumerate(self.centers):
            dx = mx - cx
            dy = my - cy
            d2 = dx * dx + dy * dy
            if d2 <= best_dist2:
                best = i
                best_dist2 = d2
        return best

    def get_dot_center(self, idx):
        try:
            return self.centers[int(idx)]
        except Exception:
            return None

    def get_selected_labels(self):
        return [self.labels[i] for i, s in enumerate(self.selected) if s]

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


class PartialBoxesDisplay:
    """Render a grid/list of small boxes representing partial options.

    Each partial option may expand into N sub-boxes (for multi-channel partials);
    each sub-box shows a small dot at left and two lines with start/end frequencies.
    """

    def __init__(self, rect, font, box_w=160, box_h=48, padding=8, dot_radius=6, hit_tolerance=12):
        self.rect = rect if isinstance(rect, pygame.Rect) else pygame.Rect(rect)
        self.font = font
        self.box_w = int(box_w)
        self.box_h = int(box_h)
        self.padding = int(padding)
        self.dot_radius = int(dot_radius)
        self.hit_tolerance = int(hit_tolerance)
        self.boxes = []  # list of (f_start, f_end)

    def set_rect(self, rect):
        self.rect = rect if isinstance(rect, pygame.Rect) else pygame.Rect(rect)

    def set_partials(self, partials):
        # Build the flattened list of sub-boxes from partials
        boxes = []
        if not partials:
            self.boxes = boxes
            return

        for p in partials:
            try:
                f0 = float(p.get('f_start', 0))
                f1 = float(p.get('f_end', 0))
            except Exception:
                continue

            # Determine number of sub-channels
            num_sub = 1
            if isinstance(p.get('channels'), list):
                num_sub = max(1, len(p.get('channels')))
            else:
                for k in ('num_channels', 'num_chans', 'chans', 'chans_needed', 'n_chans'):
                    if k in p:
                        try:
                            num_sub = max(1, int(p.get(k) or 1))
                        except Exception:
                            num_sub = 1
                        break

            span = f1 - f0
            if num_sub <= 1 or span <= 0:
                boxes.append((f0, f1))
            else:
                piece = span / num_sub
                for i in range(num_sub):
                    s = f0 + i * piece
                    e = f0 + (i + 1) * piece
                    boxes.append((s, e))

        self.boxes = boxes
        # compute layout now if rect is set
        self._compute_layout()

    def _format_freq(self, f):
        try:
            f = float(f)
        except Exception:
            return str(f)
        if f >= 1e9:
            return f"{f/1e9:.3f} GHz"
        if f >= 1e6:
            return f"{f/1e6:.3f} MHz"
        if f >= 1e3:
            return f"{f/1e3:.1f} kHz"
        return f"{int(f)} Hz"

    def draw(self, surface):
        r = self.rect
        pygame.draw.rect(surface, (250, 250, 250), r)
        # ensure layout computed
        if not getattr(self, 'box_rects', None):
            self._compute_layout()

        for idx, box_rect in enumerate(getattr(self, 'box_rects', [])):
            pygame.draw.rect(surface, (230, 230, 230), box_rect, border_radius=6)
            pygame.draw.rect(surface, (180, 180, 180), box_rect, 1, border_radius=6)

            # left dot
            dot_cx, dot_cy = self.dot_centers[idx]
            pygame.draw.circle(surface, (0, 0, 0), (dot_cx, dot_cy), self.dot_radius + 1)
            # indicate connected/unconnected in green/gray later by caller; default green
            pygame.draw.circle(surface, (0, 120, 0), (dot_cx, dot_cy), self.dot_radius)

            # texts
            txt_x = dot_cx + self.dot_radius + 10
            s, e = self.boxes[idx]
            top_txt = self.font.render(self._format_freq(s), True, (0, 0, 0))
            bot_txt = self.font.render(self._format_freq(e), True, (80, 80, 80))
            surface.blit(top_txt, (txt_x, box_rect.y + 6))
            surface.blit(bot_txt, (txt_x, box_rect.y + 6 + top_txt.get_height()))

    def _compute_layout(self):
        r = self.rect
        per_row = max(1, (r.w + self.padding) // (self.box_w + self.padding))
        x0 = r.x + self.padding
        y0 = r.y + self.padding
        box_rects = []
        dot_centers = []
        for idx, (s, e) in enumerate(self.boxes):
            row = idx // per_row
            col = idx % per_row
            x = x0 + col * (self.box_w + self.padding)
            y = y0 + row * (self.box_h + self.padding)
            box_rect = pygame.Rect(x, y, self.box_w, self.box_h)
            box_rects.append(box_rect)
            dot_cx = box_rect.x + 12
            dot_cy = box_rect.y + box_rect.h // 2
            dot_centers.append((int(dot_cx), int(dot_cy)))

        self.box_rects = box_rects
        self.dot_centers = dot_centers

    def get_dot_index_at(self, pos):
        for i, dcenter in enumerate(getattr(self, 'dot_centers', []) or []):
            dx = pos[0] - dcenter[0]
            dy = pos[1] - dcenter[1]
            if dx * dx + dy * dy <= (self.dot_radius + self.hit_tolerance) ** 2:
                return i
        return None

    def get_dot_center(self, idx):
        try:
            return self.dot_centers[int(idx)]
        except Exception:
            return None

