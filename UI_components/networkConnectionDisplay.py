import pygame
import ipaddress

from .input_box import InputBox


class NetworkConnectionsDisplay:
    """UI widget showing two network connection rows.

    Layout (columns):
    - Connection name (QSFP28_1 / QSFP28_2)
    - IP Address: two input boxes (primary and secondary)
    - Connected: clickable box (toggles)
    - Validated: read-only box set by the Validate button

    This class is purely a UI component: `handle_event` forwards events to
    the input boxes and handles clicks on the connected toggle and the
    per-row Validate button. Validation uses Python's `ipaddress` to check
    IPv4 addresses.
    """

    def __init__(self, rect, font, rows=2, padding=10, box_h=32):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.padding = int(padding)
        self.box_h = int(box_h)
        self.rows_count = int(rows)

        # each row: dict with name, ip_box, connected, validated, rects
        self.rows = []
        for i in range(self.rows_count):
            self.rows.append({
                'name': f'QSFP28_{i+1}',
                'ip_box': None,
                'connected': False,
                'validated': False,
                'connected_rect': None,
                'validated_rect': None,
            })
        # computed columns (set in set_rect)
        self._cols = {}
        self.set_rect(self.rect)

    def set_rect(self, rect):
        self.rect = pygame.Rect(rect)
        pad = self.padding
        inner_x = self.rect.x + pad
        inner_y = self.rect.y + pad
        total_w = max(0, self.rect.w - pad * 2)

        # Columns: name | ip | connected | validated
        name_w = max(120, int(total_w * 0.22))
        ip_w = max(160, int(total_w * 0.50))
        conn_w = max(72, int(total_w * 0.14))
        valid_w = total_w - (name_w + ip_w + conn_w)
        if valid_w < 60:
            extra = 60 - valid_w
            valid_w = 60
            ip_w = max(120, ip_w - extra)

        # store column x positions
        x_name = inner_x
        x_ip = x_name + name_w + pad
        x_conn = x_ip + ip_w + pad
        x_valid = x_conn + conn_w + pad

        self._cols = {
            'name': (x_name, name_w),
            'ip': (x_ip, ip_w),
            'connected': (x_conn, conn_w),
            'validated': (x_valid, valid_w),
        }

        # header and row metrics
        header_h = int(self.font.get_height()) + 6
        row_h = self.box_h

        # create or update input boxes for each row (preserve text if already created)
        for i, row in enumerate(self.rows):
            ry = inner_y + header_h + pad + i * (row_h + pad)
            # IP box: use InputBox with empty label and label_gap=0
            ip_x = self._cols['ip'][0]
            ip_w = self._cols['ip'][1]
            if row.get('ip_box') is None:
                ip_box = InputBox(ip_x, ry, ip_w, row_h, '', '0.0.0.0', self.font, multipliers=None, unit='', default_multiplier_index=0, label_gap=0)
                row['ip_box'] = ip_box
            else:
                # update rect to preserve existing text
                row['ip_box'].rect = pygame.Rect(ip_x, ry, ip_w, row_h)
                row['ip_box'].txt_surface = row['ip_box'].font.render(row['ip_box'].text, True, (0, 0, 0))

            # rectangles for connected / validated
            row['connected_rect'] = pygame.Rect(self._cols['connected'][0], ry, self._cols['connected'][1], row_h)
            valid_x = self._cols['validated'][0]
            valid_w = self._cols['validated'][1]
            indicator_w = min(32, int(valid_w * 0.35))
            row['validated_rect'] = pygame.Rect(valid_x, ry, indicator_w, row_h)

        # validate-all button rect: place it after the rows (below the table)
        btn_w = min(220, max(120, int(self.rect.w * 0.22)))
        btn_h = 28
        btn_x = self.rect.right - pad - btn_w
        # compute top of first row
        top_y = inner_y + header_h + pad
        # bottom of rows area
        bottom_rows = top_y + self.rows_count * row_h + max(0, (self.rows_count - 1) * pad)
        # place button below rows with a small gap; clamp inside rect
        btn_y = bottom_rows + pad
        max_btn_y = self.rect.bottom - pad - btn_h
        if btn_y > max_btn_y:
            btn_y = max_btn_y
        self.validate_all_button_rect = pygame.Rect(btn_x, int(btn_y), btn_w, btn_h)

    def handle_event(self, event):
        """Handle pygame events. Returns True if the event was consumed."""
        consumed = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            pad = self.padding
            header_h = int(self.font.get_height()) + 6
            top_y = self.rect.y + pad + header_h + pad
            row_stride = self.box_h + pad

            # Quick row index computation to avoid relying on possibly stale rects
            if my >= top_y and my <= top_y + self.rows_count * row_stride - 1:
                ridx = int((my - top_y) // row_stride)
                if ridx < 0:
                    ridx = 0
                if ridx >= self.rows_count:
                    ridx = self.rows_count - 1

                # column bounds
                x_ip, ip_w = self._cols['ip']
                x_conn, conn_w = self._cols['connected']

                # Click in IP column
                if mx >= x_ip and mx <= x_ip + ip_w:
                    row = self.rows[ridx]
                    ipb = row.get('ip_box')
                    if ipb:
                        # deactivate others
                        for r2 in self.rows:
                            if r2.get('ip_box') and r2['ip_box'] is not ipb:
                                r2['ip_box'].active = False
                        try:
                            ipb.handle_event(event)
                        except Exception:
                            pass
                        return True

                # Click in Connected column
                if mx >= x_conn and mx <= x_conn + conn_w:
                    row = self.rows[ridx]
                    row['connected'] = not row['connected']
                    return True

            # Check for global validate button (outside rows)
            try:
                if self.validate_all_button_rect and self.validate_all_button_rect.collidepoint(mx, my):
                    self._validate_all()
                    return True
            except Exception:
                pass

            return False

        if event.type == pygame.KEYDOWN:
            # Forward keys to the active input box (if any)
            for row in self.rows:
                ipb = row.get('ip_box')
                if ipb and getattr(ipb, 'active', False):
                    try:
                        ipb.handle_event(event)
                    except Exception:
                        pass
                    return True

        return False

    def _validate_all(self):
        """Validate each row's single IP field using `ipaddress`.

        Sets `validated` True for rows where the IP is a valid address.
        """
        for row in self.rows:
            a = (row['ip_box'].text or '').strip() if row.get('ip_box') else ''
            try:
                if a:
                    ipaddress.ip_address(a)
                    row['validated'] = True
                else:
                    row['validated'] = False
            except Exception:
                row['validated'] = False
        return [row['validated'] for row in self.rows]

    def desired_height(self):
        """Return the desired widget height to show rows plus space for the validate button."""
        pad = self.padding
        header_h = int(self.font.get_height()) + 6
        rows = self.rows_count
        row_h = self.box_h
        extra_btn_space = 44
        return pad + header_h + pad + rows * row_h + max(0, (rows - 1) * pad) + extra_btn_space

    def draw(self, surface):
        # background area
        pygame.draw.rect(surface, (250, 250, 250), self.rect)
        # compute header positions
        pad = self.padding
        x_name, name_w = self._cols['name']
        x_ip, ip_w = self._cols['ip']
        x_conn, conn_w = self._cols['connected']
        x_valid, valid_w = self._cols['validated']

        # Header
        header_y = self.rect.y + pad
        hdr_color = (0, 0, 0)
        h_name = self.font.render('Connection', True, hdr_color)
        surface.blit(h_name, (x_name + 4, header_y))
        h_ip = self.font.render('IP Address', True, hdr_color)
        surface.blit(h_ip, (x_ip + max(4, (ip_w - h_ip.get_width()) // 2), header_y))
        h_conn = self.font.render('Connected', True, hdr_color)
        surface.blit(h_conn, (x_conn + 4, header_y))
        h_val = self.font.render('Validated', True, hdr_color)
        surface.blit(h_val, (x_valid + 4, header_y))

        # Rows
        header_h = int(self.font.get_height()) + 6
        for i, row in enumerate(self.rows):
            ry = self.rect.y + pad + header_h + pad + i * (self.box_h + pad)
            # name
            name_s = self.font.render(row['name'], True, (0, 0, 0))
            surface.blit(name_s, (x_name + 4, ry + (self.box_h - name_s.get_height()) // 2))

            # draw input box
            try:
                row['ip_box'].draw(surface)
            except Exception:
                pass

            # connected indicator (clickable)
            crect = row['connected_rect']
            if row['connected']:
                pygame.draw.rect(surface, (0, 160, 0), crect)
            else:
                pygame.draw.rect(surface, (200, 200, 200), crect)
            pygame.draw.rect(surface, (0, 0, 0), crect, 1)

            # validated indicator (read-only)
            vrect = row['validated_rect']
            if row['validated']:
                pygame.draw.rect(surface, (0, 160, 0), vrect)
            else:
                pygame.draw.rect(surface, (220, 220, 220), vrect)
            pygame.draw.rect(surface, (0, 0, 0), vrect, 1)


        # draw global validate button
        try:
            brect = self.validate_all_button_rect
            pygame.draw.rect(surface, (200, 200, 200), brect, border_radius=6)
            pygame.draw.rect(surface, (0, 0, 0), brect, 1, border_radius=6)
            lab = self.font.render('Validate Connections', True, (0, 0, 0))
            surface.blit(lab, (brect.x + (brect.w - lab.get_width()) // 2, brect.y + (brect.h - lab.get_height()) // 2))
        except Exception:
            pass

    def get_config(self):
        """Return a list with current rows state (name, ip_a, ip_b, connected, validated)."""
        out = []
        for row in self.rows:
            a = row['ip_box'].text if row.get('ip_box') else ''
            out.append({'name': row['name'], 'ip': a, 'connected': bool(row['connected']), 'validated': bool(row['validated'])})
        return out
