class f(str):
    def format(self, *args):
        s = self
        for d in args:
            if isinstance(d, dict):
                for k in d:
                    s = s.replace("{" + k + "}", d[k])
        return s

def makeone(commands):
    if len(commands) == 1:
        cp = COMMAND_DEFAULT.copy()
        cp.update(commands[0])
        return command_format.format(cp)
    else:
        next_command = makeone(commands[1:])
        # command_param = commands[0] + (FACE_UP, next_command)
        cp = COMMAND_DEFAULT.copy()
        cp["psgs"] = next_command
        cp.update(commands[0])
        return command_format.format(cp)

def a(l):
    queue = []
    r = []
    s = 0
    for c in l:
        queue.append(c)
        if len(queue) == HIEGHT_LIMIT:
            cp = BASE_DEFAULT.copy()
            cp["z"] = str(s)
            cp["psgs"] = makeone(queue)
            summon = base_format.format(cp)
            s += 1

            cp = COMMAND_DEFAULT
            cp["cmd"] = summon
            cp["block"] = NORMAL
            r.append(cp)
            queue.clear()
    if len(queue) > 0:
        cp = BASE_DEFAULT.copy()
        cp["z"] = str(s)
        cp["psgs"] = makeone(queue)
        summon = base_format.format(cp)
        s += 1
        
        cp = COMMAND_DEFAULT
        cp["cmd"] = summon
        cp["block"] = NORMAL
        r.append(cp)
        queue.clear()

    cp = BASE_DEFAULT.copy()
    cp["psgs"] = makeone(r)
    print(r)
    return base_format.format(cp)

base_format = f("summon falling_block ~{x} ~5 ~{z} {Time:1, DropItem:0, Block:stone_slab, Data:8, Passengers:[{psgs}]}")

command_format = f("""{id:falling_block, Time:1, auto:{auto}, DropItem:0, TileEntityData:{Command: {cmd}}, \
Block:{block}, Data:{face}, Passengers:[{psgs}]}""")

top = f("{id:falling_block, Time:1, DropItem:0, Block:stone_slab, Data:0}")

FACE_DOWN = 0 # y-
FACE_UP = 1 # y+
FACE_NORTH = 2 # z-
FACE_SOUTH = 3 # z+
FACE_WEST = 4 # x-
FACE_EAST = 5 # x+

NORMAL = "command_block"
REPEAT = "repeating_command_block"
CHAIN = "chain_command_block"

HIEGHT_LIMIT = 6

BASE_DEFAULT = {"x": "1", "z": "0", "psgs": ""}
COMMAND_DEFAULT = {"auto": "0", "cmd": "", "block": "dirt", "face": "0", "psgs": ""}

commands = [
{"cmd": "/say 0", "block": CHAIN},
{"cmd": "/say 1", "block": CHAIN},
{"cmd": "/say 2", "block": CHAIN},
{"cmd": "/say 3", "block": CHAIN},
{"cmd": "/say 4", "block": CHAIN},
{"cmd": "/say 5", "block": CHAIN},
{"cmd": "/say 6", "block": CHAIN},
{"cmd": "/say 7", "block": CHAIN},
{"cmd": "/say 8", "block": CHAIN},
{"cmd": "/say 9", "block": CHAIN},
{"cmd": "/say 10", "block": CHAIN},
{"cmd": "/say 11", "block": CHAIN},
{"cmd": "/say 12", "block": CHAIN},
{"cmd": "/say 13", "block": CHAIN},
{"cmd": "/say 14", "block": CHAIN},
{"cmd": "/say 15", "block": CHAIN},
{"cmd": "/say 16", "block": CHAIN},
{"cmd": "/say 17", "block": CHAIN},
{"cmd": "/say 18", "block": CHAIN},
{"cmd": "/say 19", "block": CHAIN},
{"cmd": "/say 20", "block": CHAIN},
]

(a(commands))