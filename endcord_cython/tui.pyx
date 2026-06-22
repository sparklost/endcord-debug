# endcord - Copyright (C) 2025-2026 SparkLost. All Rights Reserved.
# Source-available under the Endcord License. See LICENSE for terms.
# Redistribution of modified versions is not permitted.

# cython: boundscheck=False, wraparound=False, freethreading_compatible=True

import curses
import threading
cimport cython


cpdef inline bint in_any_range(short x, list ranges):
    """Check if x is in any of given ranges"""
    cdef tuple r
    cdef short a, b
    for r in ranges:
        a = <short>r[0]
        b = <short>r[1]
        if a <= x <= b:
            return True
    return False


cpdef void draw_chat(
    object win_chat,
    int h, int w,
    list chat_buffer,
    list chat_format,
    int chat_index,
    int chat_selected,
    list attrib_map,
    int color_default,
    list exclude_selection,
):
    cdef int num, pos
    cdef int line_idx
    cdef object line, line_format, format_part
    cdef int default_color_id
    cdef unsigned int color, color_ready
    cdef object character, format_slice
    cdef int start, end
    cdef int fill_len

    cdef int y = h

    # drawing from down to up
    chat_format = chat_format[chat_index:]
    for num in range(len(chat_buffer) - chat_index):
        line_idx = chat_index + num
        if line_idx >= len(chat_buffer):
            break
        y = h - (num + 1)
        if y < 0 or y >= h:
            break

        line = chat_buffer[line_idx]
        if num == chat_selected - chat_index and not in_any_range(chat_selected, exclude_selection):
            fill_len = w - len(line)
            win_chat.insstr(y, 0, line + (" " * fill_len) + "\n", curses.color_pair(16))
        else:
            line_format = chat_format[num]
            default_color_id = line_format[0][0]
            # filled with spaces so background is drawn all the way
            default_color = curses.color_pair(default_color_id) | attrib_map[default_color_id]
            win_chat.insstr(y, 0, (line[:w]).ljust(w) + "\n", default_color)

            for format_part in line_format[1:]:
                color = format_part[0]
                start = format_part[1]
                end = format_part[2]
                if end > w:
                    end = w
                if start >= end:
                    continue
                # assuming never to have id > 65536, if value is that large its definitely attribute
                if color >= 0x00010000:
                    # using base color because it is in message content anyway
                    color_ready = (<unsigned int>curses.color_pair(default_color_id)) | (<unsigned int>color)
                else:
                    if color > 255:   # set all colors after 255 to default color
                        color = color_default
                    color_ready = (<unsigned int>curses.color_pair(color)) | (<unsigned int>attrib_map[color])
                win_chat.chgat(y, start, end - start, color_ready)

    # fill empty lines with spaces so background is drawn all the way
    y -= 1
    while y >= 0:
        win_chat.insstr(y, 0, "\n", curses.color_pair(0))
        y -= 1
