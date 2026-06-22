# endcord - Copyright (C) 2025-2026 SparkLost. All Rights Reserved.
# Source-available under the Endcord License. See LICENSE for terms.
# Redistribution of modified versions is not permitted.

# cython: boundscheck=False, wraparound=False, freethreading_compatible=True

from libc.string cimport strlen


cdef inline char lower_c(char character) noexcept nogil:
    if b"A" <= character <= b"Z":
        return character | 32
    return character


cdef inline int fuzzy_match_score_single(const char* query, int qlen, const char* candidate, int clen) noexcept nogil:
    cdef int qpos = 0, cpos = 0
    cdef int score = 0
    cdef int last_match_pos = -1

    while qpos < qlen and cpos < clen:
        if lower_c(query[qpos]) == lower_c(candidate[cpos]):
            if cpos == last_match_pos + 1:
                score += 10   # consecutive match
            else:
                score += 1    # match after gap
            last_match_pos = cpos
            qpos += 1
        cpos += 1

    if qpos == qlen:
        score += (10 - last_match_pos) if (10 - last_match_pos) > 0 else 0
        return score
    return 0


cpdef int fuzzy_match_score(str query, str candidate):
    cdef bytes query_bytes = query.encode("utf-8")
    cdef bytes candidate_bytes = candidate.encode("utf-8")
    cdef const char* query_ptr = query_bytes
    cdef const char* candidate_ptr = candidate_bytes
    cdef int clen = strlen(candidate_ptr)
    cdef int score = 0, total_score = 0
    cdef int i = 0
    cdef int word_start = 0, word_len = 0

    while True:
        if query_ptr[i] == b" " or query_ptr[i] == b"\0":
            word_len = i - word_start
            if word_len > 0:
                score = fuzzy_match_score_single(query_ptr + word_start, word_len, candidate_ptr, clen)
                if score == 0:
                    return 0
                total_score += score
            if query_ptr[i] == b"\0":
                break
            word_start = i + 1
        i += 1

    return total_score
