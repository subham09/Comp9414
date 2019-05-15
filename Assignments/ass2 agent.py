#!/usr/bin/python

# agent.py
# By Sean Batongbacal
# Agent for Text-Based Adventure Game
# Assignment 3
# http://www.cse.unsw.edu.au/~cs3411/16s1/hw3/index.html
# COMP3411 Artificial Intelligence
# UNSW Session 1, 2016

# The agent stores a selection of data in order to function. A representation
# of the environment is stored as a dictionary where the keys are tuples 
# representing xy coordinates relative to the starting location, which is (0,0).
# The locations of points of interest (pois), i.e. axes, keys, stones, trees
# and doors, are stored as sets of tuples, and the location of the gold is
# stored as a single tuple. What the agent currently possseses are stored as
# booleans, except for stones which is stored as an integer. The situation
# of the agent is stored via x and y coordinates as well as a compass which
# represents its current direction. Whether the agent will plan ahead in order
# to correctly place stones is stored as a boolean. Finally, its current path
# and sequence of moves to move along it are stored as lists.

# The view is stored as a dict where keys are coordinates relative to the
# agent similar to the environment. The agent takes the sent view and uses
# it to update its stored representation of the environment. It then considers
# a series of targets in priority order: winning (i.e. returning to to the
# start with the gold), getting the gold, getting tools (by going to the pois)
# and exploring. It searches for paths for each of these in priority order.
# Pathfinding uses A* search, with the Manhattan distance as a heuristic,
# implemented using a priority queue with lower costs being higher priority.
# If a path is found, it replaces its current path with it. If it reaches
# its previous target (i.e. no paths to anything of higher priority), it
# checks whether the previous path is still valid, and if it is continues
# with that rather than search for a new path. Otherwise, it tries to find a
# new path, and failing that continues checking the other targets. The tools
# are sorted by proximity to the agent so it tries to get ones closest to it
# first. If none of the targets have paths, then the agent tries to explore.
# It does this by performing a breadth-first search on the known environment
# from its current position, looking for points where it can see unmapped
# areas (and thus map them), including those outside known borders, and goes
# to the first it finds. If there are no unmapped areas it can can explore,
# it switches to planning ahead. In this mode, it still performs A* searches
# to pathfind but when it reaches a junction point e.g. placing a stone or
# getting tools, it searches again but using the state the world would be in
# at that time, simulating what would happen if the agent actually did that by
# pathfinding to the same place but from the "future" location. In this way,
# it eliminates any possiblities which would not achieve its goal of getting
# the gold, such as placing stones in bad places, by predicting the future
# consequences of actions. This is why Agent.pathfind and Agent.valid have
# so many parameters: so they can be provided a future state. Additionally,
# the agent is not allowed to place stones until it has fully explored the
# environment to such an extent that it cannot progress without placing stones,
# preventing it from making any naive decisions about stone placement which
# could prevent it from winning later. i.e. it acts naively when it can
# afford to, in the hopes of winning quicker, but plans ahead when it can't.

import sys, socket, heapq

class Compass:
    def __init__(self, start = 'n'):
        self.directions = ['n', 'e', 's', 'w']
        if start in self.directions:
            self.i = self.directions.index(start)
        else:
            self.i = 0 # "north" is default starting direction
    def left(self):
        self.i = (self.i-1) % len(self.directions)
    def right(self):
        self.i = (self.i+1) % len(self.directions)
    def curr(self):
        return self.directions[self.i]

class Agent:
    def __init__(self):
        self.env = {} # dict mapping relative co-ordinates to tile types

        # env borders (mainly for show())
        self.border_n = 0
        self.border_e = 0
        self.border_s = 0
        self.border_w = 0

        self.compass = Compass()

        # poi locations relative to start (as tuples)
        self.axe = set()
        self.key = set()
        self.stone = set()
        self.gold = None
        self.trees = set()
        self.doors = set()

        # need to store what agent has
        self.has_axe = False
        self.has_key = False
        self.num_stones = 0
        self.has_gold = False

        self.plan_ahead = False

        self.path = []
        self.moves = []

        # agent loc
        self.x = 0
        self.y = 0

    def set_path(self, path):
        self.path = path
        self.moves = self.get_moves(path)

    def clear_path(self):
        self.path = []
        self.moves = []

    def get_action(self):
        if self.has_gold:
            if not self.moves:
                path = self.pathfind((0,0))
                self.set_path(path)
            else:
                # check current path is still valid
                for step in self.path:
                    if not self.valid(step):
                        path = self.pathfind((0,0))
                        self.set_path(path)
                        break
            return self.moves.pop(0)

        # search for path to gold
        if self.gold:
            self.check_gold()

        # if no path to gold, search for paths to pois
        if not self.moves or self.path[-1] != self.gold:
            self.check_pois(0 if not self.plan_ahead else self.num_stones)

        # if no paths to pois have been found, explore
        if not self.moves:
            path = self.explore()
            if path:
                self.set_path(path)
            else:
                # enable planning ahead to deploy stones
                # this should only ever happen once
                self.plan_ahead = True
                return self.get_action()

        if self.moves[0] == 'f':
            next_tile = self.path[1]
            # remove obstacles if necessary
            if self.env[next_tile] == 'T':
                return 'c'
            elif self.env[next_tile] == '-':
                return 'u'
            # update path
            self.path.pop(0)
        return self.moves.pop(0)

    def check_gold(self):
        if self.path and self.path[-1] == self.gold:
            # current path is to gold
            # so need to check path is still valid
            valid = True
            num_stones = self.num_stones
            for step in self.path:
                if not self.valid(step, num_stones):
                    valid = False
                    break
                elif self.env[step] == 'o':
                    num_stones += 1
            if valid:
                # previous path is still valid, just continue with it
                return
            else:
                # previous path is no longer valid so clear it
                self.clear_path()
        # first check for definite path
        path = self.pathfind(self.gold, 0 if not self.plan_ahead else self.num_stones, False) 
        if not path:
            # else check for path with unknowns
            path = self.pathfind(self.gold)
        if path:
            self.set_path(path)

    def check_pois(self, num_stones = 0):
        # create a poi list in priority order
        pois = list(self.stone)
        if not self.has_key:
            pois += list(self.key)
        if not self.has_axe:
            pois += list(self.axe)
        pois = sorted(pois, key = lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y))

        # go out of way to cut down doors since traditionally more interesting?
        # (even though mechanically the same as trees)
        if self.has_key:
            pois += sorted(self.doors, key = lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y))
        # dont go out of way to cut down trees since often just obstacles
        if self.has_axe:
            pois += sorted(self.trees, key = lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y))

        # search for paths to each poi in priority order
        while pois:
            pos = pois.pop(0)
            if self.path and pos == self.path[-1]:
                # this poi was the previous target and there were no paths to pois of higher priority
                # check that the previous path is still valid
                valid = True
                for step in self.path:
                    if not self.valid(step):
                        valid = False
                        break
                if valid:
                    # previous path is still valid, just continue with it
                    return
                else:
                    # previous path is no longer valid so clear it
                    self.clear_path()
            path = self.pathfind(pos, num_stones)
            if path:
                self.set_path(path)
                return # a path has been found so use it

    def explore(self):
        seen = {}
        queue = [(self.x, self.y)]
        while len(queue) > 0:
            pos = queue.pop(0)
            a, b = pos
            
            # expand n
            x = a
            y = b + 1
            if (x,y) not in seen and self.valid((x,y)):
                seen[(x,y)] = (a,b)
                for x1 in range(x-2,x+3):
                    if (x1,y+2) not in self.env or self.env[(x1,y+2)] == '?':
                        step = (x,y)
                        path = [step]
                        while step != (self.x,self.y):
                            step = seen[step]
                            path.append(step)
                        path.reverse()
                        return path
                queue.append((x,y))

            # expand e
            x = a + 1
            y = b
            if (x,y) not in seen and self.valid((x,y)):
                seen[(x,y)] = (a,b)
                for y1 in range(y-2,y+3):
                    if (x+2, y1) not in self.env or self.env[(x+2,y1)] == '?':
                        step = (x,y)
                        path = [step]
                        while step != (self.x,self.y):
                            step = seen[step]
                            path.append(step)
                        path.reverse()
                        return path
                queue.append((x,y))

            # expand s
            x = a
            y = b - 1
            if (x,y) not in seen and self.valid((x,y)):
                seen[(x,y)] = (a,b)
                for x1 in range(x-2,x+3):
                    if (x1, y-2) not in self.env or self.env[(x1,y-2)] == '?':
                        step = (x,y)
                        path = [step]
                        while step != (self.x,self.y):
                            step = seen[step]
                            path.append(step)
                        path.reverse()
                        return path
                queue.append((x,y))

            # expand w
            x = a - 1
            y = b
            if (x,y) not in seen and self.valid((x,y)):
                seen[(x,y)] = (a,b)
                for y1 in range(y-2,y+3):
                    if (x-2, y1) not in self.env or self.env[(x-2,y1)] == '?':
                        step = (x,y)
                        path = [step]
                        while step != (self.x,self.y):
                            step = seen[step]
                            path.append(step)
                        path.reverse()
                        return path
                queue.append((x,y))

        return [] # no path

    def get_moves(self, path):
        # convert path to sequence of moves
        moves = []
        compass = Compass(self.compass.curr())
        for i, curr_tile in enumerate(path):
            if i + 1 >= len(path):
                break # end of path
            next_tile = path[i+1]
            # compare direction and relative positions
            x, y = curr_tile
            a, b = next_tile
            direction = compass.curr()
            if a == x and b == y + 1:
                # go north
                if direction == 'e':
                    compass.left()
                    moves.append('l')
                elif direction == 's':
                    compass.left()
                    compass.left()
                    moves.append('l')
                    moves.append('l')
                elif direction == 'w':
                    compass.right()
                    moves.append('r')
            elif a == x + 1 and b == y:
                # go east
                if direction == 's':
                    compass.left()
                    moves.append('l')
                elif direction == 'w':
                    compass.left()
                    compass.left()
                    moves.append('l')
                    moves.append('l')
                elif direction == 'n':
                    compass.right()
                    moves.append('r')
            elif a == x and b == y - 1:
                # go south
                if direction == 'w':
                    compass.left()
                    moves.append('l')
                elif direction == 'n':
                    compass.left()
                    compass.left()
                    moves.append('l')
                    moves.append('l')
                elif direction == 'e':
                    compass.right()
                    moves.append('r')
            elif a == x - 1 and b == y:
                # go west
                if direction == 'n':
                    compass.left()
                    moves.append('l')
                elif direction == 'e':
                    compass.left()
                    compass.left()
                    moves.append('l')
                    moves.append('l')
                elif direction == 's':
                    compass.right()
                    moves.append('r')
            else:
                # bad path
                # print('Bad path')
                return False
            if self.env[next_tile] == '-' and self.has_key:
                moves.append('u')
            elif self.env[next_tile] == 'T' and self.has_axe:
                moves.append('c')
            moves.append('f')
        return moves

    def pathfind(self, target, num_stones = 0, optimistic = True, start = None, env = None, has_axe = None, has_key = None):
        c, d = target
        start = start or (self.x, self.y)
        env = env or self.env
        has_axe = has_axe or self.has_axe
        has_key = has_key or self.has_key

        seen = set([start])

        queue = [(0, start, [])]
        # insert nodes into queue based on mdist + prev cost
        # first val is est cost to goal, second is pos, third is list of prior nodes i.e. path ending in pos
        # first val being 0 is dummy since will immediately be popped

        while len(queue) > 0:
            _ , pos, path = heapq.heappop(queue)

            if pos == target:
                return [start] + path

            # if num_stones < 0:
            #     print('This shouldnt happen')
            #     continue

            prev = len(path)
            a, b = pos
            expansions = [(a,b+1), (a+1,b), (a,b-1), (a-1,b)] # nesw
            
            for exp in expansions:
                if exp not in seen and self.valid(exp, num_stones, optimistic, env, has_axe, has_key):
                    if self.plan_ahead and env[exp] == '~':
                        next_env = env.copy()
                        next_env[exp] = 'O'
                        next_path = self.pathfind(target, num_stones - 1, False, exp, next_env, has_axe, has_key)
                        if next_path:
                            return [start] + path + next_path
                    elif self.plan_ahead and env[exp] == 'o':
                        next_env = env.copy()
                        next_env[exp] = ' '
                        next_path = self.pathfind(target, num_stones + 1, False, exp, next_env, has_axe, has_key)
                        if next_path:
                            return [start] + path + next_path
                    elif self.plan_ahead and env[exp] == 'a' and not has_axe:
                        next_env = env.copy()
                        next_env[exp] = ' '
                        next_path = self.pathfind(target, num_stones, False, exp, next_env, True, has_key)
                        if next_path:
                            return [start] + path + next_path
                    elif self.plan_ahead and env[exp] == 'k' and not has_key:
                        next_env = env.copy()
                        next_env[exp] = ' '
                        next_path = self.pathfind(target, num_stones, False, exp, next_env, has_axe, True)
                        if next_path:
                            return [start] + path + next_path
                    else:
                        dist = abs(x - c) + abs(y - d) + prev # manhattan distance + cost to get to exp from (a,b)
                        heapq.heappush(queue, (dist, exp, path + [exp]))
                    seen.add(exp)

        return [] # no path

    def valid(self, pos, num_stones = 0, optimistic = True, env = None, has_axe = None, has_key = None):
        env = env or self.env
        has_axe = has_axe or self.has_axe
        has_key = has_key or self.has_key
        if pos not in env:
            return False # out of borders
        tile = env[pos]
        if not optimistic and tile == '?':
            return False
        elif tile == '*':
            return False
        elif tile == '.':
            return False
        elif tile == 'T' and has_axe == False:
            return False
        elif tile == '-' and has_key == False:
            return False
        elif tile == '~' and num_stones == 0:
            return False
        else:
            return True

    def check(self, pos):
        if self.env[pos] == 'a' and pos not in self.axe:
            self.axe.add(pos)
        elif self.env[pos] == 'k' and pos not in self.key:
            self.key.add(pos)
        elif self.env[pos] == 'o' and pos not in self.stone:
            self.stone.add(pos)
        elif self.env[pos] == '$'and self.gold != pos:
            self.gold = pos
        elif self.env[pos] == 'T' and pos not in self.trees:
            self.trees.add(pos)
        elif self.env[pos] == '-' and pos not in self.doors:
            self.doors.add(pos)

    def on_poi(self):
        pos = (self.x, self.y)
        curr = self.env[pos]
        if curr == 'a':
            self.axe.remove(pos)
            self.has_axe = True
        elif curr == 'k':
            self.key.remove(pos)
            self.has_key = True
        elif curr == 'o':
            self.stone.remove(pos)
            self.num_stones += 1
        elif curr == '$':
            self.gold = False
            self.has_gold = True
        elif curr == '~':
            # place stone
            self.env[pos] = 'O'
            self.num_stones -= 1
            # if self.num_stones < 0:
            #     ded
        elif curr == '*' or curr == 'T' or curr == '-':
            raise RuntimeError("I'm inside an obstacle!")

    def update(self, view, action):
        direction = self.compass.curr()
        if not self.env: # just spawned
            self.env = view
            self.env[(0,0)] = ' '
            self.border_n =  2
            self.border_e =  2
            self.border_s = -2
            self.border_w = -2
            for y in range(2, -3, -1):
                for x in range(-2, 3):
                    self.check((x,y))
        elif action == 'f':
            # add new stuff to env if moved
            if direction == 'n':
                self.y += 1
                curr = self.env[(self.x, self.y)]
                if curr == '*' or curr == 'T' or curr == '-':
                    self.y -= 1
                    return # tried to walk into a wall, nothing happened
                # top row is new
                for x in range(-2, 3):
                    self.env[(self.x + x, self.y + 2)] = view[(x,2)]
                    self.check((self.x + x, self.y + 2))
                # update tile you just stepped off
                self.env[(self.x, self.y - 1)] = view[(0,-1)]
                if self.y + 2 > self.border_n:
                    self.border_n = self.y + 2
                    for x in range(self.border_w, self.border_e + 1):
                        if (x, self.border_n) not in self.env:
                            self.env[(x, self.border_n)] = '?'
            elif direction == 'e':
                self.x += 1
                curr = self.env[(self.x, self.y)]
                if curr == '*' or curr == 'T' or curr == '-':
                    self.x -= 1
                    return # tried to walk into a wall, nothing happened
                # right col is new
                for x in range(-2, 3):
                    self.env[(self.x + 2, self.y - x)] = view[(x,2)]
                    self.check((self.x + 2, self.y - x))
                # update tile you just stepped off
                self.env[(self.x - 1, self.y)] = view[(0,-1)]
                if self.x + 2 > self.border_e:
                    self.border_e = self.x + 2
                    for y in range(self.border_s, self.border_n + 1):
                        if (self.border_e, y) not in self.env:
                            self.env[(self.border_e, y)] = '?'
            elif direction == 's':
                self.y -= 1
                curr = self.env[(self.x, self.y)]
                if curr == '*' or curr == 'T' or curr == '-':
                    self.y += 1
                    return # tried to walk into a wall, nothing happened
                # bottom row is new
                for x in range(-2, 3):
                    self.env[(self.x - x, self.y - 2)] = view[(x,2)]
                    self.check((self.x - x, self.y - 2))
                # update tile you just stepped off
                self.env[(self.x, self.y + 1)] = view[(0,-1)]
                if self.y - 2 < self.border_s:
                    self.border_s = self.y - 2
                    for x in range(self.border_w, self.border_e + 1):
                        if (x, self.border_s) not in self.env:
                            self.env[(x, self.border_s)] = '?'
            elif direction == 'w':
                self.x -= 1
                curr = self.env[(self.x, self.y)]
                if curr == '*' or curr == 'T' or curr == '-':
                    self.x += 1
                    return # tried to walk into a wall, nothing happened
                # left col is new
                for x in range(-2, 3):
                    self.env[(self.x - 2, self.y + x)] = view[(x,2)]
                    self.check((self.x - 2, self.y + x))
                # update tile you just stepped off
                self.env[(self.x + 1, self.y)] = view[(0,-1)]
                if self.x - 2 < self.border_w:
                    self.border_w = self.x - 2
                    for y in range(self.border_s, self.border_n + 1):
                        if (self.border_w, y) not in self.env:
                            self.env[(self.border_w, y)] = '?'
            self.on_poi()
        elif action == 'l':
            self.compass.left()
        elif action == 'r':
            self.compass.right()
        elif action == 'c' or action == 'u':
            # update right in front since tree or door gone
            x = None
            y = None
            if direction == 'n':
                x = self.x
                y = self.y + 1
            elif direction == 'e':
                x = self.x + 1
                y = self.y
            elif direction == 's':
                x = self.x
                y = self.y - 1
            elif direction == 'w':
                x = self.x - 1
                y = self.y
            self.env[(x, y)] = view[(0,1)]
            self.trees.discard((x,y))
            self.doors.discard((x,y))

    def show(self):
        line = '+'
        for x in range(self.border_w, self.border_e + 1):
            line += '-'
        line += '+'
        print(line)
        direction = self.compass.curr()
        for y in range(self.border_n, self.border_s - 1, -1):
            line = '|'
            for x in range(self.border_w, self.border_e + 1):
                if (x == self.x and y == self.y):
                    if direction == 'n':
                        line += '^'
                    elif direction == 'e':
                        line += '>'
                    elif direction == 's':
                        line += 'v'
                    elif direction == 'w':
                        line += '<'
                elif (x == 0 and y == 0):
                    line += 'X' # Start/End
                elif (x,y) in self.env:
                    line += self.env[(x, y)]
                else:
                    line += '/' # should never be printed
            line += '|'
            print(line)
        line = '+'
        for x in range(self.border_w, self.border_e + 1):
            line += '-'
        line += '+'
        print(line)
        print('axe: ' + str(self.axe))
        print('key: ' + str(self.key))
        print('stone: ' + str(self.stone))
        print('gold: ' + str(self.gold))
        print('has_axe: ' + str(self.has_axe))
        print('has_key: ' + str(self.has_key))
        print('num_stones: ' + str(self.num_stones))
        print('has_gold: ' + str(self.has_gold))
        print('trees: ' + str(self.trees))
        print('doors: ' + str(self.doors))

def print_view(view):
    print("+-----+")
    for y in range(2, -3, -1):
        line = '|'
        for x in range(-2, 3):
            if not (x == 0 and y == 0): # skip agent location
                line += view[(x, y)]
            else:
                line += '^'
        line += '|'
        print(line)
    print("+-----+")

if len(sys.argv) < 3:
    print("Usage: %s -p <port>" % sys.argv[0])
    sys.exit()

# open socket to Game Engine
sd = socket.create_connection(('localhost', sys.argv[2]))
in_stream = sd.makefile('r')
out_stream = sd.makefile('w')

action = ''
agent = Agent()

while True:
    # scan 5-by-5 window around curr loc
    view = {}
    for y in range(2, -3, -1):
        for x in range(-2, 3):
            if not (x == 0 and y == 0): # skip agent location
                ch = in_stream.read(1) # read 1 char at a time
                if ch == -1:
                    exit()
                view[(x, y)] = ch
    # print_view(view)
    agent.update(view, action)
    # agent.show()
    action = agent.get_action()
    out_stream.write(action)
    out_stream.flush()
