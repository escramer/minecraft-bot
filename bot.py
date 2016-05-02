"""Module for the bot"""

from copy import deepcopy
from time import sleep

import mcpi.minecraft as minecraft
from mcpi.vec3 import Vec3
import mcpi.block as block

from search import SearchProblem, astar

_MINECRAFT = minecraft.Minecraft.create()

_AIR = block.AIR.id
_WATER = block.WATER.id
_LAVA = block.LAVA.id

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

    def get_block(self, pos):
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
            max_height = 3 # It can drop at most this many spaces - 1.
            pos = base_pos + _Vec3(0, -1, 0)
            for _ in xrange(max_height):
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
        return False #todo

    def _get_mine_actions(self):
        """Return a list of legal mining actions."""
        return [] #todo

    def _get_placement_actions(self, block=None):
        """Return a list of legal actions that only involve placing a block
        from the inventory.

        block is a block id. It is the block that should not be placed. If None,
        any block can be placed."""
        return [] #todo

    def _set_block(self, pos, block):
        """Set a block. block is the block id. pos is a _Vec3 object."""
        raise NotImplementedError

    def _move(self, pos):
        """Move there only. pos should be a Vec3."""
        self._pos = deepcopy(pos)


class _ImaginaryBot(_GenericBot):
    """A bot used for finding paths that doesn't actually change blocks
    in the world."""

    def __init__(self, pos, inventory=None):
        """Create a new bot.

        pos should be a Vec3."""
        _GenericBot.__init__(self, pos, inventory)
        self._changes = {} # Changes to the world

    def _set_block(self, pos, block):
        """Set a block. block is the block id. pos is a _Vec3 object."""
        self._changes[deepcopy(pos)] = block

    def get_block(self, pos):
        """Get the block at the position.

        pos is a _Vec3 object."""
        if pos in self._changes:
            return self._changes[pos]
        else:
            return _MINECRAFT.getBlock(pos)

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
        return _Vec3() #todo

    def _set_block(self, pos, block):
        """Place an actual block in the world.

        block is a block id."""
        _MINECRAFT.setBlock(pos, block)

    def get_block(self, pos):
        """Get the block at the position."""
        return _MINECRAFT.getBlock(pos)

    def _move(self, pos):
        """Move there, and set the appropriate blocks."""
        self._set_block(self._pos, _AIR)
        self._set_block(self._pos + _Vec3(0, 1, 0), _AIR)
        self._set_block(pos, self._BOT_BLOCK)
        self._set_block(pos + Vec3(0, 1, 0), self._BOT_BLOCK)
        self._pos = pos


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
        """Return the block."""
        return deepcopy(self._block_loc)

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

    def getStartState(self):
        """Return the bot passed in."""
        return self._bot

    def isGoalState(self, state):
        """Return whether or not the bot is next to the player."""
        diff = state.get_pos() - self._player_loc
        return diff.y == 0 and (diff.x == 0 or diff.z == 0) and \
            abs(diff.x) + abs(diff.z) == 2 and \
            state.get_block(self._player_loc + diff/2 + Vec3(0, -1, 0)) not in \
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
    return 0 #todo


def _return_heurist(bot, problem):
    """Return the return heuristic.

    bot is an _ImaginaryBot.
    """
    return 0 #todo


def _to_my_vec3(vec):
    """Return the _Vec3 alternative of the Vec3."""
    return _Vec3(vec.x, vec.y, vec.z)


def _player_loc():
    """Return the player's location."""
    return _to_my_vec3(_MINECRAFT.player.getTilePos())


def _adj_dirs():
    """Return the adjacent directions."""
    return [_Vec3(1, 0, 0), _Vec3(-1, 0, 0), _Vec3(0, 0, 1), _Vec3(0, 0, -1)]
