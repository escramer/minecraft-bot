"""Module for the bot"""

from copy import deepcopy
from time import sleep

import mcpi.minecraft as minecraft
from mcpi.vec3 import Vec3
import mcpi.block as block

from search import SearchProblem, astar, bfs

_MINECRAFT = minecraft.Minecraft.create()

_AIR = block.AIR.id
_WATER = block.WATER.id
_LAVA = block.LAVA.id
_BEDROCK = block.BEDROCK.id

_DROP = 2 # It can drop at most this many
_DROP_PLUS_1 = _DROP + 1
_DELAY = 1


class _Vec3(Vec3):
    """A Vec3 that is hashable. Everything in this program should use this
    class."""

    def __hash__(self):
        """Return the hash."""
        return hash((self.x, self.y, self.z))


class _GenericBot:
    """A generic bot."""

    def __init__(self, pos, inventory=None):
        """Initialize with an empty inventory.

        inventory is a dictionary. If None, an empty one will be used."""
        if inventory is None:
            self._inventory = {}
        else:
            self._inventory = deepcopy(inventory)
        self._pos = deepcopy(pos)

    def take_action(self, action):
        """Take the action (acquired from _get_legal_actions)."""
        getattr(self, action['func'])(
            *action.get('args', ()), 
            **action.get('kwargs', {})
        )

    def take_actions(self, actions, seconds=None):
        """Take these actions. If seconds is not None, sleep 'seconds' 
        seconds.
        """
        if not actions:
            return

        self.take_action(actions[0])
        for action in actions[1:]:
            if seconds is not None:
                sleep(seconds)
            self.take_action(action)

    def get_pos(self):
        """Return the position."""
        return deepcopy(self._pos)

    def get_legal_actions(self, block=None):
        """Return a list of legal actions.

        If block is None, return all legal actions. Otherwise, return all
        legal actions that don't involve placing the block."""
        return self._get_move_actions(block) + self._get_mine_actions() + \
            self._get_placement_actions(block)

    def contains(self, block):
        """Return whether or not the bot contains the block id."""
        return block in self._inventory

    def _get_block(self, pos):
        """Get the block at the position. pos is a _Vec3 object."""
        raise NotImplementedError

    def _place(self, loc, exclude=None, block=None):
        """Place a block from the inventory only.

        loc is a _Vec3.
        If exclude is not None, place a block that is not 'exclude'.
        If block is not None, place that block only.
        """
        if not self._inventory:
            raise Exception('Inventory empty')

        if block is None:
            for key in self._inventory:
                if key != exclude:
                    block = key
                    break
            else:
                raise Exception((
                    'You requested not to place %s, but it is the only '
                    'block in the inventory.' % exclude
                ))

        if self._inventory[block] == 1:
            del self._inventory[block]
        else:
            self._inventory[block] -= 1

        self._set_block(loc, block)
            

    def _move_down(self):
        """Move and mine the block below."""
        new_pos = self._pos + _Vec3(0, -1, 0)
        block = self._get_block(new_pos)
        if block != _WATER:
            self._add_to_inv(block)
        self._move(new_pos)
        
    def _add_to_inv(self, block):
        """Add the block to the inventory."""
        if block in self._inventory:
            self._inventory[block] += 1
        else:
            self._inventory[block] = 1

    def _move_up(self, exclude=None):
        """Move and place a block below.

        If exclude is not None, place a block that is not 'exclude'.
        """
        self._move(self._pos + _Vec3(0, 1, 0))
        self._place(self._pos + _Vec3(0, -1, 0), exclude)

    def _mine(self, loc):
        """Mine the block. loc is a _Vec3."""
        block = self._get_block(loc)
        self.add_to_inv(block)
        self._set_block(loc, _AIR)

    def _get_move_actions(self, exclude=None):
        """Return a list of legal movement actions.

        exclude is the block to exclude.
        """
        rtn = []

        # Check for moving up
        can_move_up = self._get_block(self._pos + _Vec3(0, 2, 0)) in {_AIR, _WATER}
        if can_move_up:
            if self._surrounded():
                rtn.append({
                    'func': '_move',
                    'args': (self._pos + _Vec3(0, 1, 0),)
                })
            else:
                rtn.append({
                    'func': '_move_up',
                    'args': (exclude,)
                })

        # Check for moving down
        hidden_block = self._get_block(self._pos + _Vec3(0, -2, 0))
        if hidden_block == _WATER or hidden_block not in {_AIR, _LAVA}:
            rtn.append({'func': '_move_down'})

        # Check for side moves        
        for dir_ in _adj_dirs():
            rtn.extend(self._side_moves(dir_, can_move_up))

        return rtn

    def _side_moves(self, dir_, can_move_up):
        """Return the list of side moves.

        dir_ is an adjacent direction.
        can_move_up is a boolean for whether or not the bot can move up.
        """
        rtn = []
        base_pos = self._pos + dir_
        base_block = self._get_block(base_pos)
        empty_blocks = {_AIR, _WATER}

        # Check if it can move up
        if can_move_up and base_block not in {_AIR, _LAVA, _WATER}:
            for vert_dir in [_Vec3(0, 1, 0), _Vec3(0, 2, 0)]:
                if self._get_block(base_pos + vert_dir) not in empty_blocks:
                    break
            else:
                rtn.append({
                    'func': '_move',
                    'args': (base_pos + _Vec3(0, 1, 0),)
                })

        # Check if it can move in that direction
        for vert_dir in [_Vec3(), _Vec3(0, 1, 0)]:
            if self._get_block(base_pos + vert_dir) not in empty_blocks:
                break

        # Fall
        else:
            pos = base_pos + _Vec3(0, -1, 0)
            for _ in xrange(_DROP_PLUS_1):
                block = self._get_block(pos)
                if block != _AIR:
                    if block != _LAVA:
                        rtn.append({
                            'func': '_move',
                            'args': (pos + _Vec3(0, 1, 0),)
                        })
                    break
                pos.y -= 1  
            
    def _surrounded(self):
        """Return whether or not the bot is surrounded by water."""
        for dir in _adj_dirs():
            if self._get_block(self._pos + dir) != _WATER:
                return False
        return True

    def _get_mine_actions(self):
        """Return a list of legal mining actions (that only involve mining
        and not moving)."""
        rtn = []
        dont_mine = {_AIR, _WATER, _LAVA}
        # Mine above.
        pos_above = self._pos + _Vec3(0, 2, 0)
        if self._get_block(pos_above) not in dont_mine:
            rtn.append({
                'func': '_mine',
                'args': (pos_above,)
            })

        for dir in _adj_dirs():
            pos = self._pos + dir
            for _ in xrange(2):
                if self._get_block(pos) not in dont_mine:
                    rtn.append({
                        'func': '_mine',
                        'args': (pos,)
                    })
                pos = pos + _Vec3(0, 1, 0)

        return rtn

    def _get_placement_actions(self, block=None):
        """Return a list of legal actions that only involve placing a block
        from the inventory.

        block is a block id. It is the block that should not be placed. If None,
        any block can be placed."""
        if not self._has_blocks_to_place(exclude=block):
            return []

        dirs = [_Vec3(0, 2, 0)]
        for dir in _adj_dirs():
            dirs.extend([dir, dir + _Vec3(0, 1, 0)])
            if self._get_block(self._pos + dir) in [_AIR, _WATER]:
                dirs.append(dir + _Vec3(0, -1, 0))

        rtn = []
        for dir in dirs:
            if self._can_place(self._pos + dir):
                rtn.append({
                    'func': '_place',
                    'args': (self._pos + dir,),
                    'kwargs': {'exclude': block}
                })

        return rtn

    def _can_place(self, loc):
        """Return whether or not the bot can place a block at that location
        independent of what it has in its inventory."""
        non_blocks = [_AIR, _WATER, _LAVA]
        player = [self._pos, self._pos + _Vec3(0, 1, 0)]
        for dir in _adj_dirs + [_Vec3(0, 1, 0), _Vec3(0, -1, 0)]:
            new_loc = loc + dir
            if new_loc not in player and self._get_block(new_loc) \
                    not in non_blocks:
                return True
        return False

    def _has_blocks_to_place(self, exclude=None):
        """Return whether or not the bot can place a block from the
        inventory. If exclude is None, any block can be placed."""
        for block in self._inventory:
            if block != exclude:
                return True
        return False

    def _set_block(self, pos, block):
        """Set a block. block is the block id. pos is a _Vec3 object."""
        raise NotImplementedError

    def _move(self, pos):
        """Move there only."""
        self._pos = deepcopy(pos)


class _ImaginaryBot(_GenericBot):
    """A bot used for finding paths that doesn't actually change blocks
    in the world."""

    def __init__(self, pos, inventory=None):
        """Create a new bot."""
        _GenericBot.__init__(self, pos, inventory)
        self._changes = {} # Changes to the world

    def _set_block(self, pos, block):
        """Set a block. block is the block id. pos is a _Vec3 object."""
        self._changes[deepcopy(pos)] = block

    def _get_block(self, pos):
        """Get the block at the position.

        pos is a _Vec3 object."""
        if pos in self._changes:
            return self._changes[pos]
        else:
            return _MINECRAFT.getBlock(pos)

    def get_block(self, pos):
        """The public version."""
        return self._get_block(pos)

    def _key_vals(self, dict_):
        """Return a list of key-val tuples."""
        return [(key, val) for key, val in dict_.iteritems()]

    def __hash__(self):
        """Return the hash."""
        return hash(frozenset([self._pos] + \
                 self._key_vals(self._inventory) + \
                 self._key_vals(self._changes)
        ))


class Bot(_GenericBot):
    """The real bot.

    All vector arguments are Vec3s."""

    _BOT_BLOCK = block.IRON.id

    def __init__(self):
        """Create a bot next to the player."""
        pos = _MINECRAFT.player.getTilePos() + Vec3(2, 0, 0)
        pos = _Vec3(pos.x, pos.y, pos.z)
        while _MINECRAFT.getBlock(pos) == _AIR:
            pos.y -= 1
        while _MINECRAFT.getBlock(pos) != _AIR:
            pos.y += 1
        _GenericBot.__init__(self, pos)
        self._pos = pos
        self._move(self._pos)

    def fetch(self, block_name):
        """Mine and return a block to the player."""
        imag_bot = _ImaginaryBot(self._pos, self._inventory)
        block_id = getattr(block, block_name).id
        block_loc = self._get_block_loc(block_id)
        mine_prob = _MineProblem(imag_bot, block_loc, block_id)
        mine_actions = astar(mine_prob, mine_heuristic)
        self.take_actions(mine_actions, _DELAY)
        imag_bot = _ImaginaryBot(self._pos, self._inventory)
        player_loc = _player_loc()
        return_prob = _ReturnProblem(imag_bot, block_id, player_loc)
        return_actions = astar(return_prob, return_heuristic)
        imag_bot.take_actions(return_actions)
        return_actions.append({
            'func': '_place',
            'args': (imag_bot.get_pos() + player_loc) / 2,
            'kwargs': {'block': block_id}
        })
        self.take_actions(return_actions, _DELAY)

    def _get_block_loc(self, block_id):
        """Return the location of the block."""
        find_prob = FindProblem(self._pos, block_id)
        dirs = bfs(find_prob)
        return self._pos + sum(dirs)

    def _set_block(self, pos, block):
        """Place an actual block in the world.

        block is a block id."""
        _MINECRAFT.setBlock(pos, block)

    def _get_block(self, pos):
        """Get the block at the position."""
        return _MINECRAFT.getBlock(pos)

    def _move(self, pos):
        """Move there, and set the appropriate blocks."""
        self._set_block(self._pos, _AIR)
        self._set_block(self._pos + _Vec3(0, 1, 0), _AIR)
        self._set_block(pos, self._BOT_BLOCK)
        self._set_block(pos + Vec3(0, 1, 0), self._BOT_BLOCK)
        self._pos = pos


class FindProblem(SearchProblem):
    """Problem for finding the location of a block in the world.

    A state in this problem is a location.
    """

    _DIRS = _adj_dirs() + 

    def __init__(self, start_loc, block_id):
        """Initialize."""
        self._start_loc = start_loc
        self._block_id = block_id

    def getStartState(self):
        """Return the starting location."""
        return self._start_loc

    def isGoalState(self, state):
        return _MINECRAFT.getBlock(state) == self._block_id

    def getSuccessors(self, state):
        """Return the successors."""
        rtn = []
        for dir in _all_dirs():
            successor = state + dir
            if successor.y <= _MINECRAFT.getHeight(successor.x, successor.z) \
                    and _MINECRAFT.getBlock(successor) != _BEDROCK:
                rtn.append((successor, dir, 1))
        return rtn


class _MineProblem(SearchProblem):
    """The problem of finding the block and mining it (not returning
    it)."""

    def __init__(self, imag_bot, block_loc, block_id):
        """Initialize the problem with an _ImaginaryBot.

        block_loc is a Vec3.
        """
        self._bot = imag_bot
        self._block_loc = deep_copy(block_loc)
        self._block_id = block_id

    def get_block_loc(self):
        """Return the block location."""
        return deepcopy(self._block_loc)

    def get_block_id(self):
        """Return the block it's trying to mine."""
        return self._block_id

    def getStartState(self):
        """Return the bot passed in."""
        return self._bot

    def isGoalState(self, state):
        """Return whether or not the bot has the block."""
        return state.contains(self._block_id)

    def getSuccessors(self, state):
        """Return the successors."""
        rtn = []
        for action in state.get_legal_actions():
            successor = deepcopy(state)
            successor.take_action(action)
            rtn.append((successor, action, 1))
        return rtn


class _ReturnProblem(SearchProblem):
    """The problem of returning to the player. This does not place the block
    next to the player."""

    def __init__(self, imag_bot, block, player_loc):
        """Initialized the problem with an _ImaginaryBot.

        block is a block id."""
        self._bot = image_bot
        self._block = block
        self._player_loc = player_loc

    def get_player_loc(self):
        """Return the player location."""
        return deepcopy(self._player_loc)

    def getStartState(self):
        """Return the bot passed in."""
        return self._bot

    def isGoalState(self, state):
        """Return whether or not the bot is next to the player."""
        diff = state.get_pos() - self._player_loc
        return diff.y == 0 and (diff.x == 0 or diff.z == 0) and \
            abs(diff.x) + abs(diff.z) == 2 and \
            state.get_block(self._player_loc + diff/2 + _Vec3(0, -1, 0)) not in \
            (_AIR, _LAVA, _WATER)

    def getSuccessors(self, state):
        """Return the successors."""
        rtn = []
        for action in state.get_legal_actions(self._block):
            successor = deepcopy(state)
            successor.take_action(action)
            rtn.append((successor, action, 1))
        return rtn


def _mine_heuristic(bot, problem):
    """Return the mining heuristic.

    bot is an _ImaginaryBot.
    """
    if bot.contains(problem.get_block_id()):
        return 0

    bot_pos = bot.get_pos()
    dest_pos = problem.get_block_loc()

    # If man == dy: return man + 1
    # If man > dy: return man
    # If man < dy: return dy?
    man_dist = _manhattan((bot_pos.x, bot_pos.z), (dest_pos.x, dest_pos.z))
    y_diff = bot_pos.y - dest_pos.y
    if y_diff < 0:
        y_diff += 1

    if y_diff == 0:
        return man_dist

    # Transform so that it's only dropping
    drop = _DROP if y_diff > 0 else 1
    y_diff = abs(y_diff)

    drops = _drops(y_diff, drop)

    if man_dist > drops:
        return man_dist
    if man_dist == drops:
        return man_dist + 1
    if drop == 1:
        return drops
    if y_diff % drop == 1:
        return drops
    return drops + 1
    

def _drops(dist, drop):
    """Return the number of times it takes to drop a distance dist. drop is the
    length of one drop. Both are assumed positive."""
    rtn = dist / drop
    if dist % drop != 0:
        rtn += 1
    return rtn
    

def _return_heuristic(bot, problem):
    """Return the return heuristic.

    bot is an _ImaginaryBot.
    """
    bot_pos = bot.get_pos()
    player_pos = problem.get_player_loc()
    bot_plane_pos = (bot.x, bot.z)

    y_diff = bot_pos.y - player_pos.y

    drop = _DROP if y_diff > 0 else 1
    y_diff = abs(y_diff)
    drops = _drops(y_diff, drop)
    min_man = float('inf')
    for dir in _adj_dirs():
        loc = player_pos + 2 * dir
        man_dist = _manhattan(bot_plane_pos, (loc.x, loc.z))
        if man_dist < min_man:
            min_man = man_dist
        if man_dist < drops:
            return drops
    return min_man


def _to_my_vec3(vec):
    """Return the _Vec3 alternative of the Vec3."""
    return _Vec3(vec.x, vec.y, vec.z)


def _player_loc():
    """Return the player's location."""
    return _to_my_vec3(_MINECRAFT.player.getTilePos())


def _adj_dirs():
    """Return the adjacent directions."""
    return [_Vec3(1, 0, 0), _Vec3(-1, 0, 0), _Vec3(0, 0, 1), _Vec3(0, 0, -1)]


def _all_dirs():
    """Return all adjacent directions."""
    return _adj_dirs + [_Vec3(0, 1, 0), _Vec3(0, -1, 0)]


def _manhattan(pos1, pos2):
    """Return the manhattan distance. pos1 and pos2 should be iterable."""
    return sum(abs(val1 - val2) for val1, val2 in zip(pos1, pos2))
