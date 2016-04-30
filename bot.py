"""Module for the bot"""

from copy import deepcopy
from time import sleep

import mcpi.minecraft as minecraft
from mcpi.vec3 import Vec3
import mcpi.block as block

from search import SearchProblem

_MINECRAFT = minecraft.Minecraft.create()


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
            self.__inventory = {}
        else:
            self.__inventory = deepcopy(inventory)
        self._pos = pos

    def take_action(self, action):
        """Take the action (acquired from _get_legal_actions)."""
        pass #todo

    def get_legal_actions(self, block=None):
        """Return a list of legal actions.

        If block is None, return all legal actions. Otherwise, return all
        legal actions that don't involve placing the block."""
        return self._get_move_actions() + self._get_mine_actions() + \
            self._get_placement_actions(block)

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

    def contains(self, block):
        """Return whether or not the bot contains the block id."""
        return block in self.__inventory

    def _set_block(self, pos, block):
        """Set a block. block is the block id. pos is a _Vec3 object."""
        raise NotImplementedError

    def _get_block(self, pos):
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

    def _get_block(self, pos):
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
        while _MINECRAFT.getBlock(pos) == block.AIR.id:
            pos.y -= 1
        while _MINECRAFT.getBlock(pos) != block.AIR.id:
            pos.y += 1
        _GenericBot.__init__(self, pos)
        self._move(pos)

    def fetch(self, block_name):
        """Mine and return a block to the player."""
        pass #todo

    def _set_block(self, pos, block):
        """Place an actual block in the world.

        block is a block id."""
        _MINECRAFT.setBlock(pos, block)

    def _get_block(self, pos):
        """Get the block at the position."""
        return _MINECRAFT.getBlock(pos)

    def _move(self, pos):
        """Move there, and set the appropriate blocks."""
        self._set_block(self._pos, block.AIR.id)
        self._set_block(self._pos + Vec3(0, 1, 0), block.AIR.id)
        self._set_block(pos, self._BOT_BLOCK)
        self._set_block(pos + Vec3(0, 1, 0), self._BOT_BLOCK)
        self._pos = pos

    def _take_actions(self, actions):
        """Take these actions with a delay inbetween."""
        if actions:
            self._take_action(actions[0])
            for action in actions[1:]:
                sleep(1)
                self._take_action(action)


class _MineProblem(SearchProblem):
    """The problem of finding the block and mining it (not returning
    it)."""

    def __init__(self, imag_bot, block):
        """Initialize the problem with an _ImaginaryBot.

        block is a block id."""
        pass #todo

    def getStartState(self):
        """Return the bot passed in."""
        return self._bot

    def isGoalState(self, state):
        """Return whether or not the bot has the block."""
        return True #todo

    def getSuccessors(self, state):
        """Return the successors."""
        return [] #todo


class _ReturnProblem(SearchProblem):
    """The problem of returning to the player. This does not place the block
    next to the player."""

    def __init__(self, imag_bot, block):
        """Initialized the problem with an _ImaginaryBot.

        block is a block id."""
        pass #todo

    def getStartState(self):
        """Return the bot passed in."""
        return self._bot

    def isGoalState(self, state):
        """Return whether or not the bot is next to the player."""
        return True #todo

    def getSuccessors(self, state):
        """Return the successors."""
        return [] #todo

