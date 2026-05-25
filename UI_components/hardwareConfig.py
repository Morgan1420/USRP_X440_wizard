import pygame
from .portsConnectionDisplay import PortsConnectionDisplay, PartialOptionsBoxesDisplay


class HardwareConfigScreen:

    def __init__(self, font, width, height):
        self.font = font
        self.width = width
        self.height = height
        self.active = False
        self.fullscreen = False

        # Modal rectangle
        margin_x = 80
        margin_y = 60
        self.surface_rect = pygame.Rect(margin_x, margin_y, width - margin_x * 2, height - margin_y * 2)

        # Sample items (can be replaced/updated later)
        self.num_ports = 8
        self.ports = [f"P{i+1}" for i in range(self.num_ports)]
        self.connections = ["Ethernet", "USB", "PCIe", "Internal"]
        self.selected_ports = {p: False for p in self.ports}
        self.selected_connections = {c: False for c in self.connections}
        # Ports display helper
        self._ports_display_h = 72
        self.ports_display = PortsConnectionDisplay(pygame.Rect(self.surface_rect.left + 10, self.surface_rect.top + 48, self.surface_rect.w - 20, self._ports_display_h), num_ports=self.num_ports, labels=self.ports, font=self.font)
        # Partial options boxes display (populated when an option is provided)
        self.partials_display = PartialOptionsBoxesDisplay(pygame.Rect(self.surface_rect.left + 10, self.surface_rect.top + 48 + self._ports_display_h + 12, self.surface_rect.w - 20, 56), self.font)
        self.current_option = None
        # Connection state: port_idx -> box_idx (flattened partial_option index)
        self.port_to_box = {}
        # Reverse mapping: box_idx -> set(port_idx)
        self.box_to_ports = {}
        # Drag state for creating/removing cables
        self._dragging = False
        self._drag_from_type = None  # 'port' or 'partial'
        self._drag_from_index = None
        self._drag_current_pos = (0, 0)
        self._dragged = False
        # For double-drag deletion behaviour
        self._last_drag_action = None
        self._last_drag_count = 0

        # Layout
        self.section_padding = 20
        self._button_w = 160
        self._button_h = 40
        # Match OptionDetails close button size/style
        self._back_w = 100
        self._back_h = 34
        # Title font slightly larger than regular font
        try:
            title_size = int(self.font.get_linesize() * 1.5)
        except Exception:
            title_size = 40
        self.title_font = pygame.font.Font(None, title_size)
        self.capture_rect = pygame.Rect(
            self.surface_rect.centerx - self._button_w // 2,
            self.surface_rect.bottom - self.section_padding - self._button_h,
            self._button_w,
            self._button_h,
        )
        # Position the back button at the top-left of the screen (like OptionDetails)
        self.go_back_rect = pygame.Rect(12, 12, self._back_w, self._back_h)

    def open(self, initial=None, fullscreen=False):
        self.fullscreen = bool(fullscreen)
        # set rects depending on mode
        if self.fullscreen:
            self.surface_rect = pygame.Rect(0, 0, self.width, self.height)
        else:
            margin_x = 80
            margin_y = 60
            self.surface_rect = pygame.Rect(margin_x, margin_y, self.width - margin_x * 2, self.height - margin_y * 2)

        # recompute control rects relative to surface
        self.capture_rect = pygame.Rect(
            self.surface_rect.centerx - self._button_w // 2,
            self.surface_rect.bottom - self.section_padding - self._button_h,
            self._button_w,
            self._button_h,
        )
        # Keep back button at absolute top-left to match OptionDetails
        self.go_back_rect = pygame.Rect(12, 12, self._back_w, self._back_h)
        # Update ports display rect
        inner = self.surface_rect.inflate(-self.section_padding * 2, -self.section_padding * 2)
        ports_rect = pygame.Rect(inner.left + 10, inner.top + 48, inner.w - 20, self._ports_display_h)
        self.ports_display.set_rect(ports_rect)
        # sync visual selection with internal mapping
        for i, label in enumerate(self.ports):
            try:
                self.ports_display.selected[i] = bool(self.selected_ports.get(label, False))
            except Exception:
                pass
        # set current option (if any) and prepare partial boxes
        self.current_option = initial
        partials = []
        if isinstance(initial, dict):
            partials = initial.get('partial_options') or []
        self.partials_display.set_partial_options(partials)
        # compute partials area height (reserve reasonable space above capture button)
        cap_top = self.capture_rect.y
        available_space = max(24, cap_top - ports_rect.bottom - 18)

        # estimate minimal needed height based on partials and font metrics
        minimal_needed = 0
        pz = getattr(self.partials_display, 'zone_boxes', None) or []
        if pz and self.font:
            line_h = int(self.font.get_height())
            title_h = line_h + 4
            content_h = max(12, line_h * 2 + 4)
            # zones are side-by-side; need height to fit the tallest zone
            for z in pz:
                n = max(1, len(z))
                zone_h = title_h + 6 + n * content_h + (n - 1) * self.partials_display.padding + 8
                minimal_needed = max(minimal_needed, zone_h)
        else:
            # fallback: compute rows needed and estimate
            if self.font:
                line_h = int(self.font.get_height())
                content_h = max(12, line_h * 2 + 4)
            else:
                content_h = self.partials_display.box_h
            per_row = max(1, (inner.w + self.partials_display.padding) // (self.partials_display.box_w + self.partials_display.padding))
            rows = (max(1, len(self.partials_display.boxes)) + per_row - 1) // per_row
            minimal_needed = rows * content_h + max(0, rows - 1) * self.partials_display.padding + self.partials_display.padding * 2

        # choose available height: cannot exceed available_space, prefer minimal_needed
        chosen_h = min(available_space, max(minimal_needed, 32))
        self.partials_display.set_rect(pygame.Rect(inner.left + 10, ports_rect.bottom + 12, inner.w - 20, chosen_h))
        # Auto-connect each partial option box to a port (one-to-one) up to available ports
        # If there are exactly 2 partial option zones, split ports in half and assign
        # zone 0 -> first half ports, zone 1 -> second half ports.
        self.port_to_box.clear()
        self.box_to_ports.clear()
        zone_boxes = getattr(self.partials_display, 'zone_boxes', []) or []
        if len(zone_boxes) == 2:
            half = self.num_ports // 2
            # assign zone 0 boxes to ports 0..half-1
            for j, _ in enumerate(zone_boxes[0]):
                if j >= half:
                    break
                flat_idx = j
                port_idx = j
                self.port_to_box[port_idx] = flat_idx
                self.box_to_ports.setdefault(flat_idx, set()).add(port_idx)
                try:
                    self.ports_display.selected[port_idx] = True
                    self.selected_ports[self.ports[port_idx]] = True
                except Exception:
                    pass
            # assign zone 1 boxes to ports half..end
            offset = len(zone_boxes[0])
            for j, _ in enumerate(zone_boxes[1]):
                port_idx = half + j
                if port_idx >= self.num_ports:
                    break
                flat_idx = offset + j
                self.port_to_box[port_idx] = flat_idx
                self.box_to_ports.setdefault(flat_idx, set()).add(port_idx)
                try:
                    self.ports_display.selected[port_idx] = True
                    self.selected_ports[self.ports[port_idx]] = True
                except Exception:
                    pass
        else:
            n_boxes = len(self.partials_display.boxes)
            for i in range(min(n_boxes, self.num_ports)):
                self.port_to_box[i] = i
                self.box_to_ports.setdefault(i, set()).add(i)
                try:
                    self.ports_display.selected[i] = True
                    self.selected_ports[self.ports[i]] = True
                except Exception:
                    pass

        self.active = True

    def close(self):
        self.active = False
        self.fullscreen = False

    def _point_segment_distance_sq(self, px, py, ax, ay, bx, by):
        """Squared distance from point p(px,py) to segment a(ax,ay)-b(bx,by)."""
        vx = bx - ax
        vy = by - ay
        wx = px - ax
        wy = py - ay
        c1 = vx * wx + vy * wy
        if c1 <= 0:
            dx = px - ax
            dy = py - ay
            return dx * dx + dy * dy
        c2 = vx * vx + vy * vy
        if c2 <= c1:
            dx = px - bx
            dy = py - by
            return dx * dx + dy * dy
        b = c1 / c2
        projx = ax + b * vx
        projy = ay + b * vy
        dx = px - projx
        dy = py - projy
        return dx * dx + dy * dy

    def _zone_for_box(self, box_idx):
        """Return the zone index for a flattened box index, or None."""
        zb = getattr(self.partials_display, 'zone_boxes', None)
        if not zb:
            return None
        cum = 0
        for zi, boxes in enumerate(zb):
            if box_idx < cum + len(boxes):
                return zi
            cum += len(boxes)
        return None

    def handle_event(self, event):
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return 'cancel'
        # Mouse down: handle clicks, start possible drag
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Click outside closes modal only in non-fullscreen (modal) mode
            if (not self.fullscreen) and (not self.surface_rect.collidepoint(mx, my)):
                self.close()
                return 'cancel'

            # Go back button (top-left)
            if self.go_back_rect.collidepoint(mx, my):
                self.close()
                return 'cancel'

            # Capture button
            if self.capture_rect.collidepoint(mx, my):
                selected_ports = [p for p, v in self.selected_ports.items() if v]
                selected_connections = [c for c, v in self.selected_connections.items() if v]
                # build assignments: port label -> box index or None
                assignments = {}
                for i, label in enumerate(self.ports):
                    assignments[label] = self.port_to_box.get(i)
                # build reverse map box -> list of port labels
                box_map = {str(b): [self.ports[p] for p in sorted(list(ps))] for b, ps in self.box_to_ports.items()}
                cfg = {'ports': selected_ports, 'connections': selected_connections, 'assignments': assignments, 'box_map': box_map}
                self.close()
                return ('capture', cfg)

            # Prepare display rects for hit-testing
            inner = self.surface_rect.inflate(-self.section_padding * 2, -self.section_padding * 2)
            ports_rect = pygame.Rect(inner.left + 10, inner.top + 48, inner.w - 20, self._ports_display_h)
            self.ports_display.set_rect(ports_rect)
            partials_rect = pygame.Rect(inner.left + 10, ports_rect.bottom + 12, inner.w - 20, max(56, self.capture_rect.y - ports_rect.bottom - 18))
            self.partials_display.set_rect(partials_rect)

            # Check for direct click on a cable (line between port and partial dot)
            # find nearest mapping whose segment is within threshold
            best = None
            # threshold based on dot sizes, with extra tolerance
            thresh = max(12, getattr(self.ports_display, 'dot_radius', 8) + getattr(self.partials_display, 'dot_radius', 6) + 4)
            thresh2 = thresh * thresh
            for p_map, b_map in list(self.port_to_box.items()):
                p_center = self.ports_display.get_dot_center(p_map)
                b_center = self.partials_display.get_dot_center(b_map)
                if not p_center or not b_center:
                    continue
                d2 = self._point_segment_distance_sq(mx, my, p_center[0], p_center[1], b_center[0], b_center[1])
                if d2 <= thresh2:
                    if best is None or d2 < best[0]:
                        best = (d2, p_map, b_map)
            if best is not None:
                _, p_map, b_map = best
                # Delete mapping if rules allow (partial must remain connected to at least one port)
                if len(self.box_to_ports.get(b_map, set())) > 1:
                    # remove mapping for this port
                    old = self.port_to_box.pop(p_map, None)
                    if old is not None:
                        s = self.box_to_ports.get(old)
                        if s and p_map in s:
                            s.discard(p_map)
                            if len(s) == 0:
                                self.box_to_ports.pop(old, None)
                    try:
                        self.ports_display.selected[p_map] = False
                        self.selected_ports[self.ports[p_map]] = False
                    except Exception:
                        pass
                return None

            # Hit-test for drag start on a port or partial dot
            p_idx = self.ports_display.get_dot_index_at((mx, my))
            b_idx = self.partials_display.get_dot_index_at((mx, my))
            if p_idx is not None:
                self._dragging = True
                self._drag_from_type = 'port'
                self._drag_from_index = int(p_idx)
                self._drag_current_pos = (mx, my)
                self._dragged = False
                return None
            if b_idx is not None:
                self._dragging = True
                self._drag_from_type = 'partial'
                self._drag_from_index = int(b_idx)
                self._drag_current_pos = (mx, my)
                self._dragged = False
                return None

            # If not starting a drag, fall back to click handling
            toggled = self.ports_display.handle_event(event)
            if toggled is not None:
                label = self.ports[toggled]
                self.selected_ports[label] = not self.selected_ports.get(label, False)
                return None

            # Small gap between sections; start connections below ports display
            y = partials_rect.bottom + 12
            checkbox_size = 18
            for c in self.connections:
                rect = pygame.Rect(inner.left + 20, y, checkbox_size, checkbox_size)
                label_rect = pygame.Rect(rect.right + 8, y, 200, checkbox_size)
                if rect.collidepoint(mx, my) or label_rect.collidepoint(mx, my):
                    self.selected_connections[c] = not self.selected_connections[c]
                    return None
                y += 36

        # Mouse move: update drag position
        if event.type == pygame.MOUSEMOTION and self._dragging:
            self._drag_current_pos = event.pos
            self._dragged = True
            return None

        # Mouse up: finalize drag
        if event.type == pygame.MOUSEBUTTONUP and self._dragging:
            mx, my = event.pos
            # hit-test targets
            inner = self.surface_rect.inflate(-self.section_padding * 2, -self.section_padding * 2)
            ports_rect = pygame.Rect(inner.left + 10, inner.top + 48, inner.w - 20, self._ports_display_h)
            self.ports_display.set_rect(ports_rect)
            partials_rect = pygame.Rect(inner.left + 10, ports_rect.bottom + 12, inner.w - 20, max(56, self.capture_rect.y - ports_rect.bottom - 36))
            self.partials_display.set_rect(partials_rect)
            target_p = self.ports_display.get_dot_index_at((mx, my))
            target_b = self.partials_display.get_dot_index_at((mx, my))

            # Helper closures
            def connect_port_to_box(port_idx, box_idx):
                # Enforce 2-zone split rule: if there are exactly two zones,
                # ports in the first half can only connect to zone 0 and
                # ports in the second half can only connect to zone 1.
                zone_boxes = getattr(self.partials_display, 'zone_boxes', []) or []
                if len(zone_boxes) == 2:
                    zone_idx = self._zone_for_box(box_idx)
                    if zone_idx is not None:
                        half = self.num_ports // 2
                        if port_idx < half and zone_idx != 0:
                            return
                        if port_idx >= half and zone_idx != 1:
                            return

                # remove any previous mapping for this port
                old = self.port_to_box.get(port_idx)
                if old is not None and old == box_idx:
                    return
                if old is not None:
                    s = self.box_to_ports.get(old)
                    if s and port_idx in s:
                        s.discard(port_idx)
                        if len(s) == 0:
                            self.box_to_ports.pop(old, None)
                self.port_to_box[port_idx] = box_idx
                self.box_to_ports.setdefault(box_idx, set()).add(port_idx)
                try:
                    self.ports_display.selected[port_idx] = True
                    self.selected_ports[self.ports[port_idx]] = True
                except Exception:
                    pass

            def disconnect_port(port_idx):
                old = self.port_to_box.pop(port_idx, None)
                if old is not None:
                    s = self.box_to_ports.get(old)
                    if s and port_idx in s:
                        s.discard(port_idx)
                        if len(s) == 0:
                            self.box_to_ports.pop(old, None)
                try:
                    self.ports_display.selected[port_idx] = False
                    self.selected_ports[self.ports[port_idx]] = False
                except Exception:
                    pass

            # Apply drag result rules with double-drag deletion support
            # Normalize action to ('port', port_idx_or_None, 'partial', box_idx_or_None)
            norm_port = None
            norm_box = None
            if self._drag_from_type == 'port':
                norm_port = int(self._drag_from_index)
                if target_b is not None:
                    norm_box = int(target_b)
            elif self._drag_from_type == 'partial':
                norm_box = int(self._drag_from_index)
                if target_p is not None:
                    norm_port = int(target_p)

            norm_action = ('port', norm_port, 'partial', norm_box)

            # update last drag counters
            if norm_action == self._last_drag_action:
                self._last_drag_count += 1
            else:
                self._last_drag_action = norm_action
                self._last_drag_count = 1

            # Deletion: require two identical drag actions in a row
            performed_delete = False

            if norm_port is not None and norm_box is not None:
                # action connects port <-> box
                mapping_exists = (self.port_to_box.get(norm_port) == norm_box and norm_port in self.box_to_ports.get(norm_box, set()))
                if self._last_drag_count >= 2 and mapping_exists:
                    # attempt delete if not last connection
                    if len(self.box_to_ports.get(norm_box, set())) > 1:
                        disconnect_port(norm_port)
                        performed_delete = True
                        # reset last-drag state after deletion
                        self._last_drag_action = None
                        self._last_drag_count = 0
                if not performed_delete:
                    # perform normal connect (overwrites allowed)
                    if self._drag_from_type == 'port':
                        connect_port_to_box(norm_port, norm_box)
                    else:
                        # dragged from partial to port: ensure we don't orphan previous mapping for dst_port
                        dst_port = norm_port
                        old = self.port_to_box.get(dst_port)
                        if old is None or len(self.box_to_ports.get(old, set())) > 1 or old == norm_box:
                            connect_port_to_box(dst_port, norm_box)
                        else:
                            # cannot overwrite since it would orphan the previous box
                            pass

            else:
                # dropped to empty space (no target)
                if self._drag_from_type == 'port':
                    src_port = int(self._drag_from_index)
                    old = self.port_to_box.get(src_port)
                    if old is not None:
                        # require double-drag to delete
                        if self._last_drag_count >= 2:
                            if len(self.box_to_ports.get(old, set())) > 1:
                                disconnect_port(src_port)
                                performed_delete = True
                                self._last_drag_action = None
                                self._last_drag_count = 0
                            else:
                                # cannot remove last connection
                                pass
                        else:
                            # first drag to empty: do nothing (wait for confirmation drag)
                            pass
                else:
                    # dragging from partial to empty: do nothing
                    pass

            # reset drag state
            self._dragging = False
            self._drag_from_type = None
            self._drag_from_index = None
            self._drag_current_pos = (0, 0)
            self._dragged = False
            return None

        return None

    def draw(self, screen):
        if not self.active:
            return

        # Dim background only in modal mode
        if not self.fullscreen:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))

        # Modal / fullscreen box
        pygame.draw.rect(screen, (255, 255, 255), self.surface_rect, border_radius=6)
        pygame.draw.rect(screen, (200, 200, 200), self.surface_rect, 2, border_radius=6)

        # Title (centered horizontally, larger font)
        title = self.title_font.render("Hardware Configuration", True, (0, 0, 0))
        title_x = (self.width - title.get_width()) // 2
        title_y = self.surface_rect.top + 12
        screen.blit(title, (title_x, title_y))

        # Go back button (top-left) styled like OptionDetails
        pygame.draw.rect(screen, (200, 50, 50), self.go_back_rect)
        back_surf = self.font.render("Tornar", True, (255, 255, 255))
        screen.blit(back_surf, (self.go_back_rect.x + 8, self.go_back_rect.y + (self.go_back_rect.h - back_surf.get_height()) // 2))

        # Sections (stacked vertically) — move content down to avoid collisions
        inner = self.surface_rect.inflate(-self.section_padding * 2, -self.section_padding * 2)
        header_y = inner.top + 40
        ph = self.font.render("Ports", True, (0, 0, 0))
        screen.blit(ph, (inner.left + 10, header_y))

        # Ports display (dots)
        ports_rect = pygame.Rect(inner.left + 10, header_y + 24, inner.w - 20, self._ports_display_h)
        self.ports_display.set_rect(ports_rect)
        self.ports_display.draw(screen)

        # Partials display (small boxes) under ports
        cap_top = self.capture_rect.y
        available_space = max(24, cap_top - ports_rect.bottom - 36)

        # estimate minimal needed height similar to open()
        minimal_needed = 0
        pz = getattr(self.partials_display, 'zone_boxes', None) or []
        if pz and self.font:
            line_h = int(self.font.get_height())
            title_h = line_h + 4
            content_h = max(12, line_h * 2 + 4)
            for z in pz:
                n = max(1, len(z))
                zone_h = title_h + 6 + n * content_h + (n - 1) * self.partials_display.padding + 8
                minimal_needed = max(minimal_needed, zone_h)
        else:
            if self.font:
                line_h = int(self.font.get_height())
                content_h = max(12, line_h * 2 + 4)
            else:
                content_h = self.partials_display.box_h
            per_row = max(1, (inner.w + self.partials_display.padding) // (self.partials_display.box_w + self.partials_display.padding))
            rows = (max(1, len(self.partials_display.boxes)) + per_row - 1) // per_row
            minimal_needed = rows * content_h + max(0, rows - 1) * self.partials_display.padding + self.partials_display.padding * 2

        chosen_h = min(available_space, max(minimal_needed, 32))
        partials_rect = pygame.Rect(inner.left + 10, ports_rect.bottom + 12, inner.w - 20, chosen_h)
        self.partials_display.set_rect(partials_rect)
        self.partials_display.draw(screen)

        # Draw connection cables (green) for each mapped port -> box
        for p_idx, b_idx in list(self.port_to_box.items()):
            try:
                p_center = self.ports_display.get_dot_center(p_idx)
                b_center = self.partials_display.get_dot_center(b_idx)
                if p_center and b_center:
                    pygame.draw.line(screen, (20, 160, 20), p_center, b_center, 6)
                    # draw small caps so line meets dot nicely
                    pygame.draw.circle(screen, (20, 160, 20), p_center, 6)
                    pygame.draw.circle(screen, (20, 160, 20), b_center, 6)
            except Exception:
                pass

        # If dragging, draw transient cable
        if self._dragging and self._drag_from_type is not None:
            try:
                if self._drag_from_type == 'port':
                    src = self.ports_display.get_dot_center(self._drag_from_index)
                else:
                    src = self.partials_display.get_dot_center(self._drag_from_index)
                dst = self._drag_current_pos
                if src:
                    pygame.draw.line(screen, (30, 200, 30), src, dst, 4)
                    pygame.draw.circle(screen, (30, 200, 30), src, 6)
            except Exception:
                pass

        # Overlay partial dots to reflect connection state (connected=green, unconnected=gray)
        try:
            for i, center in enumerate(getattr(self.partials_display, 'dot_centers', []) or []):
                col = (20, 160, 20) if i in self.box_to_ports else (180, 180, 180)
                pygame.draw.circle(screen, (0, 0, 0), center, max(3, self.partials_display.dot_radius + 1))
                pygame.draw.circle(screen, col, center, self.partials_display.dot_radius)
        except Exception:
            pass

        # Connections header and checkboxes (below partials display)
        y = partials_rect.bottom + 12
        ch = self.font.render("Connections", True, (0, 0, 0))
        screen.blit(ch, (inner.left + 10, y))
        y += 24
        checkbox_size = 18
        for c in self.connections:
            rect = pygame.Rect(inner.left + 20, y, checkbox_size, checkbox_size)
            pygame.draw.rect(screen, (255, 255, 255), rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)
            if self.selected_connections[c]:
                pygame.draw.line(screen, (0, 120, 0), (rect.left + 3, rect.centery), (rect.centerx, rect.bottom - 3), 3)
                pygame.draw.line(screen, (0, 120, 0), (rect.centerx, rect.bottom - 3), (rect.right - 3, rect.top + 3), 3)
            label = self.font.render(c, True, (0, 0, 0))
            screen.blit(label, (rect.right + 8, y - 2))
            y += 36

        # Capture button
        pygame.draw.rect(screen, (0, 120, 200), self.capture_rect, border_radius=6)
        csurf = self.font.render("Capture", True, (255, 255, 255))
        screen.blit(csurf, (self.capture_rect.centerx - csurf.get_width() / 2, self.capture_rect.centery - csurf.get_height() / 2))
