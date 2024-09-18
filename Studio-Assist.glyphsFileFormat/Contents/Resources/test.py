###########################################################################################################
#
#
# File Filter Plugin
# Implementation of Test class to check font file
#
#
###########################################################################################################



from __future__ import division, print_function
import urllib

from GlyphsApp import *
from GlyphsApp.plugins import *


#
#
# Called when
#
# Todo:
#
class Test:
    @objc.python_method
    def __init__(self, font):

        self.font = font
        self.master_count = 0
        self.characters_to_check = [
            "H",
            "a",
            "m",
            "b",
            "u",
            "r",
            "g",
            "e",
            "F",
            "O",
            "N",
            "T",
        ]

        self.master_count = self.calculateMasters()
        self.missing_characters = self.calculateMissingCharacters()
        self.characters_without_outlines = self.calculateMissingOutlines
        self.font_has_missing_characters = False
        self.font_has_missing_outlines = False

    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def __str__(self):
        return f"Test(font={self.font}, master_count={self.master_count}, missing_characters={self.missing_characters}, missing_outlines={self.calculateMissingOutlines})"

    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def calculateMasters(self):
        # calculate how many masters are in the font file

        return len(self.font.masters)
    
    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def calculateMissingCharacters(self):
        missing_characters = []

        # Loop through each character to check if its in the font
        for char in self.characters_to_check:
            glyph = self.font.glyphs[char]
            if not glyph:
                missing_characters.append(char)

        return missing_characters

    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def calculateMissingOutlines(self):
        missing_outlines = []

        # Loop through each character to check if its in the font
        for char in self.characters_to_check:
            glyph = self.font.glyphs[char]
            if glyph:  # if the glyph exists in the font
                has_outline = False
                for layer in glyph.layers:
                    if layer.isMasterLayer:  # only check master layer
                        if len(layer.paths) > 0:
                            has_outline = True
                            break
                if not has_outline:
                    missing_outlines.append(char)
            else:
                missing_outlines.append(char)

        return missing_outlines
