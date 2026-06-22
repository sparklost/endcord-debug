# endcord - Copyright (C) 2025-2026 SparkLost. All Rights Reserved.
# Source-available under the Endcord License. See LICENSE for terms.
# Redistribution of modified versions is not permitted.

# USER SETTINGS

DEFAULT_REACTION_EMOJI = {
    1: ("emoji_id", ("wrapper", "uint64")),
    2: ("emoji_name", ("wrapper", "string")),
    3: ("animated", ("wrapper", "bool")),
}

TEXT_AND_IMAGES_SETTINGS = {
    11: ("gif_auto_play", ("wrapper", "bool")),
    12: ("render_embeds", ("wrapper", "bool")),
    33: ("default_reaction_emoji", DEFAULT_REACTION_EMOJI),
}

CUSTOM_STATUS = {
    1: ("text", "string"),
    2: ("emoji_id", "fixed64"),
    3: ("emoji_name", "string"),
    4: ("expires_at_ms", "fixed64"),
    5: ("created_at_ms", "fixed64"),
    6: ("label", ("wrapper", "string")),
}

STATUS_SETTINGS = {
    1: ("status", ("wrapper", "string")),
    2: ("custom_status", CUSTOM_STATUS),
    3: ("show_current_game", ("wrapper", "bool")),
    4: ("status_expires_at_ms", "fixed64"),
    5: ("status_created_at_ms", ("wrapper", "uint64")),
}

GUILD_FOLDER = {
    1: ("guild_ids", ("packed", "fixed64")),
    2: ("id", ("wrapper", "int64")),
    3: ("name", ("wrapper", "string")),
    4: ("color", ("wrapper", "uint64")),
}

GUILD_FOLDERS = {
    1: ("folders", ("repeated", GUILD_FOLDER)),
    2: ("guild_positions", ("packed", "fixed64")),
}

USER_SETTINGS = {
    6: ("text_and_images", TEXT_AND_IMAGES_SETTINGS),
    11: ("status", STATUS_SETTINGS),
    14: ("guild_folders", GUILD_FOLDERS),
}


# USER FRECENCY SETINGS

FAVORITE_GIF = {
    2: ("src", "string"),
    5: ("order", "uint32"),
}

FAVORITE_GIFS = {
    1: ("gifs", ("map", ("string", FAVORITE_GIF))),
}

FAVORITE_EMOJIS = {
    1: ("emojis", ("repeated_primitive", "string")),
}

USER_FRECENCY = {
    2: ("favorite_gifs", FAVORITE_GIFS),
    5: ("favorite_emojis", FAVORITE_EMOJIS),
}
