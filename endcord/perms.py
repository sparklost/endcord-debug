# endcord - Copyright (C) 2025-2026 SparkLost. All Rights Reserved.
# Source-available under the Endcord License. See LICENSE for terms.
# Redistribution of modified versions is not permitted.

def decode_flag(flags, flag_num):
    """Return value for specified flag number (int)"""
    flag = (1 << flag_num)
    return (flags & flag) == flag


def decode_permission(permission, flag):
    """
    Return value for specified permission flag (binary shifted)
    Some useful flags:
    ADMINISTRATOR   0x8 (1 << 3)
    MANAGE_MESSAGES 0x10 (1 << 4)
    ADD_REACTIONS   0x40 (1 << 6)
    VIEW_CHANNEL    0x400 (1 << 10)
    SEND_MESSAGES   0x800 (1 << 11)
    EMBED_LINKS     0x4000 (1 << 14)
    ATTACH_FILES    0x8000 (1 << 15)
    MENTION_EVERYONE    0x20000 (1 << 17)
    USE_EXTERNAL_EMOJIS 0x40000 (1 << 18)
    CONNECT (VOICE)     0x100000 (1 << 20)
    SPEAK (VOICE)       0x200000 (1 << 21)
    BYPASS_SLOWMODE     0x10000000000000 (1 << 52)
    """
    return (permission & flag) == flag


def compute_permissions(guilds, this_guild_roles, this_guild_id, my_roles, my_id):
    """Read channel permissions and add permitted and allowed_embeds to each channel"""
    # select guild
    for guild in guilds:
        if guild["guild_id"] == this_guild_id:
            break
    else:
        return guilds

    # check if this user is admin
    admin = False
    if not guild["owned"]:   # if im not owner check if im admin
        base_permissions = int(guild["base_permissions"])
        for role in this_guild_roles:
            if role["id"] in my_roles and decode_permission(int(role["permissions"]), 0x8):
                admin = True
                break

    # check if this user is owner
    if guild["owned"] or admin:
        for num, channel in enumerate(guild["channels"]):
            guild["channels"][num]["permitted"] = True
            guild["channels"][num]["allow_manage"] = True
            guild["channels"][num]["allow_attach"] = True
            guild["channels"][num]["allow_write"] = True
            guild["channels"][num].get("permission_overwrites", None)
        guild["admin"] = True
        return guilds

    # base permissions
    base_permissions = int(guild["base_permissions"])
    for role in this_guild_roles:
        if role["id"] in my_roles:
            base_permissions |= int(role["permissions"])

    for num, channel in enumerate(guild["channels"]):

        # check if channel is already parsed
        if "permitted" in channel:
            continue

        # replace get with pop if uses lots of ram, but it will break live role updates and member list
        permission_overwrites = guild["channels"][num].get("permission_overwrites", [])

        # @everyone role overwrite
        permissions = base_permissions
        for overwrite in permission_overwrites:
            if overwrite["id"] == this_guild_id:
                permissions &= ~int(overwrite["deny"])
                permissions |= int(overwrite["allow"])
                break
        allow = 0
        deny = 0

        # role overwrites
        for overwrite in permission_overwrites:
            if overwrite["type"] == 0 and overwrite["id"] in my_roles:
                allow |= int(overwrite["allow"])
                deny |= int(overwrite["deny"])
        permissions &= ~deny
        permissions |= allow

        # member overwrites
        for overwrite in permission_overwrites:
            if overwrite["type"] == 1 and overwrite["id"] == my_id:
                permissions &= ~int(overwrite["deny"])
                permissions |= int(overwrite["allow"])

        # read and store selected permissions
        guild["channels"][num]["perms_computed"] = permissions
        guild["channels"][num]["allow_manage"] = decode_permission(permissions, 0x10)   # MANAGE_MESSAGES
        guild["channels"][num]["permitted"] = decode_permission(permissions, 0x400)    # VIEW_CHANNEL
        guild["channels"][num]["allow_write"] = decode_permission(permissions, 0x800)    # SEND_MESSAGES
        guild["channels"][num]["allow_attach"] = decode_permission(permissions, 0x8000)   # ATTACH_FILES
        if decode_permission(permissions, 0x10000000000000):   # BYPASS_SLOWMODE
            guild["channels"][num]["bypass_slowmode"] = True
        if channel["type"] == 2 and not decode_permission(permissions, 0x100000):   # CONNECT (VOICE)
            guild["channels"][num]["allow_voice"] = False
        if channel["type"] == 2 and not decode_permission(permissions, 0x200000):   # SPEAK (VOICE)
            guild["channels"][num]["allow_speak"] = False
    return guilds


def compute_command_permissions(commands, all_app_perms, this_channel_id, this_guild_id, my_roles, my_id, admin, my_this_channel_perms):
    """Check app commands permissions and return bool mask of all commands that can be executed"""
    # admin can do it all
    if admin:
        return [True] * len(commands)

    done_perms = []
    for command in commands:
        all_perms = command.get("permissions", {})
        app_perms = {}
        for app in all_app_perms:
            if app["app_id"] == command["app_id"]:
                app_perms = app["perms"]
                break
        if not (all_perms or app_perms):
            done_perms.append(True)
            continue
        skip = False

        # channel perms - command
        for channel, value in all_perms.get("channels", {}).items():
            if channel == this_channel_id or channel == this_guild_id:   # this_guild_id is base channel
                if not value:
                    skip = True
                break

        # channel perms - app
        else:
            for channel, value in app_perms.get("channels", {}).items():
                if channel == this_channel_id or channel == this_guild_id:   # this_guild_id is base channel
                    if not value:
                        skip = True
                    break
        if skip:
            done_perms.append(False)
            continue

        # user perms - command
        for user, value in all_perms.get("users", {}).items():
            if user == my_id:
                skip = True
                if not value:
                    done_perms.append(False)
                else:
                    done_perms.append(True)
                break
        if skip:
            continue

        # role perms - command
        for role, value in all_perms.get("roles", {}).items():
            if role in my_roles or role == this_guild_id:   # this_guild_id is base role
                skip = True
                if not value:
                    done_perms.append(False)
                else:
                    done_perms.append(True)
                break
        if skip:
            continue

        # user perms - app
        for user, value in app_perms.get("users", {}).items():
            if user == my_id:
                if not value:
                    skip = True
                    done_perms.append(False)
                break
        if skip:
            continue

        # role perms - app
        for role, value in app_perms.get("roles", {}).items():
            if role in my_roles or role == this_guild_id:   # this_guild_id is base role
                if not value:
                    skip = True
                    done_perms.append(False)
                break
        if skip:
            continue

        # default_member_permissions check
        default_member_permissions = command.get("default_member_permissions")
        if default_member_permissions is None:   # everyone
            done_perms.append(True)
        elif default_member_permissions == 0:   # only admins
            done_perms.append(False)
        else:   # if user has all these or more permissions in current channel
            decoded_default_perms = []
            default_member_permissions = int(default_member_permissions)
            for i in list(range(47)) + [49, 50]:   # all perms
                decoded_default_perms.append(decode_flag(default_member_permissions, i))
            # get my perms in this channel
            decoded_my_perms = []
            my_this_channel_perms = int(my_this_channel_perms)
            for i in list(range(47)) + [49, 50]:   # all perms
                decoded_my_perms.append(decode_flag(my_this_channel_perms, i))
            if all(not a or b for a, b in zip(decoded_default_perms, decoded_my_perms)):
                done_perms.append(True)
            else:
                done_perms.append(False)
    return done_perms


def compute_member_list_id(permission_overwrites):
    """
    Calculate channel member list id from its permission_overwrites.
    The format before hashing is: allow:ID1,allow:ID2,deny:ID3,deny:ID4.
    'Deny' and 'allow' are grouped so 'allow' is first, ids are sorted ascending in the groups.
    """
    allow = []
    deny = []
    if not permission_overwrites:
        return "everyone"
    for overwrite in permission_overwrites:
        allow_bits = int(overwrite["allow"])
        deny_bits = int(overwrite["deny"])
        if allow_bits & 1024:
            allow.append(str(overwrite["id"]))
        if deny_bits & 1024:
            deny.append(str(overwrite["id"]))
    if not allow and not deny:
        return "everyone"
    allow.sort(key=int)
    deny.sort(key=int)
    parts = []
    for overwrite_id in allow:
        parts.append(f"allow:{overwrite_id}")
    for overwrite_id in deny:
        parts.append(f"deny:{overwrite_id}")
    # return mmh3.hash(",".join(parts), seed=0, signed=False)
    return murmurhash3(",".join(parts))


def murmurhash3(key, seed=0):
    """Calculate unsingned murmur3 32bit hash on given key"""
    if isinstance(key, str):
        key = key.encode("utf-8")
    length = len(key)
    c1 = 0xcc9e2d51
    c2 = 0x1b873593
    h1 = seed

    # body in 4-byte chunks
    blocks_num = length // 4
    for i in range(blocks_num):
        k1 = key[i * 4] | (key[i * 4 + 1] << 8) | (key[i * 4 + 2] << 16) | (key[i * 4 + 3] << 24)   # extract 4 bytes
        k1 = (k1 * c1) & 0xffffffff   # to prevent python from expanding it over 32 bits
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xffffffff  # rotate left 15
        k1 = (k1 * c2) & 0xffffffff
        h1 ^= k1
        h1 = ((h1 << 13) | (h1 >> 19)) & 0xffffffff  # rotate left 13
        h1 = (h1 * 5 + 0xe6546b64) & 0xffffffff

    # tail is remaining 1-3 bytes
    k1 = 0
    tail_index = blocks_num * 4
    remainder = length & 3
    if remainder >= 3:
        k1 ^= key[tail_index + 2] << 16
    if remainder >= 2:
        k1 ^= key[tail_index + 1] << 8
    if remainder >= 1:
        k1 ^= key[tail_index]
        k1 = (k1 * c1) & 0xffffffff
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xffffffff  # rotate left 15
        k1 = (k1 * c2) & 0xffffffff
        h1 ^= k1

    # mix block length and hash code
    h1 ^= length
    h1 ^= h1 >> 16
    h1 = (h1 * 0x85ebca6b) & 0xffffffff
    h1 ^= h1 >> 13
    h1 = (h1 * 0xc2b2ae35) & 0xffffffff
    h1 ^= h1 >> 16
    return h1
