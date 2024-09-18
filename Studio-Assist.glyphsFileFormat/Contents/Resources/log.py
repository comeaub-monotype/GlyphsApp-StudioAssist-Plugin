###########################################################################################################
#
#
# File Filter Plugin
# Implementation of Log class to handle logging
#
#
###########################################################################################################


class Log:

    #
    #
    # Called when
    #
    # Todo: 
    #
    def __init__(self, sender, log_level="INFO"):
        self.log_level = log_level
        self.sender = sender


    #
    #
    # Called when 
    #
    # Todo:
    #
    def info(self, message):

        if self.log_level == "INFO":
            print(f"INFO: {message}")
            self.sender.set(message)

    #
    #
    # Called when 
    #
    # Todo:
    #
    def fontInfo(self, Font):
        print(f"INFO: {Font.familyName} {Font.versionMajor}.{Font.versionMinor}")
        print(f"INFO: {Font.upm} UPM  {Font.date}")

    #
    #
    # Called when 
    #
    # Todo:
    #
    def debug(self, message):

        if self.log_level == "INFO" or self.log_level == "DEBUG":
            print(f"DEBUG: {message}")


    #
    #
    # Called when 
    #
    # Todo:
    #
    def error(self, message):

        if self.log_level == "INFO" or self.log_level == "ERROR":
            print(f"ERROR: {message}")
            self.sender.set(message)


    #
    #
    # Called when 
    #
    # Todo:
    #
    def warning(self, message):

        if self.log_level == "INFO" or self.log_level == "WARNING":
            print(f"WARNING: {message}")
            self.sender.set(message)