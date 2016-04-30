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


class _Vec3(Vec3):
    """A Vec3 that is hashable"""

    def __hash__(self):
        """Return the hash."""
        return hash((self.x, self.y, self.z))


class _GenericBot:
    """A generic bot."""

    def __init__(self, pos, inventory=None):
        """Initialize with an empty inventory.

        pos should be a Vec3.
        inventory is a dictionary. If None, an empty one will be used."""
        if inventory is None:
            self._inventory = {}
        else:
            self._inventory = deepcopy(inventory)
        self._pos = pos

    def take_action(self, action):
        """Take the action (acquired from _get_legal_actions)."""
        pass #todo

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
        return self._get_move_actions() + self._get_mine_actions() + \
            self._get_placement_actions(block)

    def contains(self, block):
        """Return whether or not the bot contains the block id."""
        return block in self._inventory

    def _get_move_actions(self):
        """Return a list of legal movement actions."""
        return [] #todo

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

    def get_block(self, pos):
        """Get the block at the position. pos is a _Vec3 object."""
        raise NotImplementedError

    def _move(self, pos):
        """Move there. pos should be a Vec3."""
        self._pos = pos


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
        self._changes[pos] = block

    def get_block(self, pos):
        """Get the block at the position.

        pos is a _Vec3 object."""
        if pos in self._changes:
            return self._changes[pos]
        else:
            return self._mc.getBlock(pos)


class Bot(_GenericBot):
    """The real bot.

    All vector arguments are Vec3s."""

    _BOT_BLOCK = block.IRON.id

    def __init__(self):
        """Create a bot next to the player."""
        pos = _MINECRAFT.player.getTilePos() + Vec3(2, 0, 0)
        while _MINECRAFT.getBlock(pos) == _AIR:
            pos.y -= 1
        while _MINECRAFT.getBlock(pos) != _AIR:
            pos.y += 1
        _GenericBot.__init__(self, pos)
        self._move(pos)

    def fetch(self, block_name):
        """Mine and return a block to the player."""
        imag_bot = _ImaginaryBot(self._pos, self._inventory)
        block_id = getattr(block, block_name).id
        block_loc = self._get_block_loc(block_id)
        mine_prob = _MineProblem(imag_bot, block_loc)
        mine_actions = astar(mine_prob, mine_heuristic)
        imag_bot.take_actions(mine_actions)
        return_prob = _ReturnProblem(imag_bot, block_id)
        return_actions = astar(return_prob, return_heuristic)
        actions = mine_actions + return_actions
        #todo: Place the block mined next to the player

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
        self._set_block(self._pos + Vec3(0, 1, 0), _AIR)
        self._set_block(pos, self._BOT_BLOCK)
        self._set_block(pos + Vec3(0, 1, 0), self._BOT_BLOCK)
        self._pos = pos


class _MineProblem(SearchProblem):
    """The problem of finding the block and mining it (not returning
    it)."""

    def __init__(self, imag_bot, block):
        """Initialize the problem with an _ImaginaryBot.

        block is a block id."""
        self._bot = imag_bot
        self._block = block

    def get_block(self):
        """Return the block."""
        return self._block

    def getStartState(self):
        """Return the bot passed in."""
        return self._bot

    def isGoalState(self, state):
        """Return whether or not the bot has the block."""
        return state.contains(self._block)

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

    def __init__(self, imag_bot, block):
        """Initialized the problem with an _ImaginaryBot.

        block is a block id."""
        self._bot = image_bot
        self._block = block
        self._player_loc = _MINECRAFT.player.getTilePos()

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


def mine_heuristic(bot, problem):
    """Return the mining heuristic.

    bot is an _ImaginaryBot.
    """
    return 0 #todo


def return_heurist(bot, problem):
    """Return the return heuristic.

    bot is an _ImaginaryBot.
    """
    return 0 #todo

