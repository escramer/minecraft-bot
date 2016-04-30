"""Module for the bot"""

from copy import deepcopy

import mcpi.minecraft as minecraft
from mcpi.vec3 import Vec3

from search import SearchProblem

_MINECRAFT = minecraft.Minecraft.create()


class _Vec3(Vec3):
    """A Vec3 that is hashable"""

    def __hash__(self):
        """Return the hash."""
        return hash((self.x, self.y, self.z))


class _GenericBot:
    """A generic bot"""

    def __init__(self, pos, inventory=None):
        """Initialize with an empty inventory.

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
        return [] #todo

    def contains(self, block):
        """Return whether or not the bot contains the block id."""
        return block in self.__inventory

    def _set_block(self, block, pos):
        """Set a block. block is the block id. pos is a Vec3 object."""
        raise NotImplementedError

    def _get_block(self, pos):
        """Get the block at the position."""
        raise NotImplementedError

    def _move(self, pos):
        """Move there."""
        self._pos = pos


class _ImaginaryBot(_GenericBot):
    """A bot used for finding paths that doesn't actually change blocks
    in the world."""

    def __init__(self, pos, inventory=None):
        """Create a new bot."""
        _GenericBot.__init__(self, pos, inventory)
        self._changes = {} # Changes to the world

    def _set_block(self, block, pos):
        """Set a block. block is the block id. pos is a Vec3 object."""
        self._changes[pos] = block

    def _get_block(self, pos):
        """Get the block at the position."""
        if pos in self._changes:
            return self._changes[pos]
        else:
            return self._mc.getBlock(pos)


class Bot(_GenericBot):
    """The real bot."""

    def __init__(self):
        """Create a bot next to the player."""
        pass #todo

    def fetch(self, block_name):
        """Mine and return a block to the player."""
        pass #todo

    def _set_block(self, block, pos):
        """Place an actual block in the world."""
        pass #todo

    def _get_block(self, pos):
        """Get the block at the position."""
        return 0 #todo

    def _move(self, pos):
        """Move there, and set the appropriate blocks."""
        self._pos = pos
        # Set the blocks

    def _take_actions(self, actions):
        """Take these actions with a delay inbetween."""
        pass #todo


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

