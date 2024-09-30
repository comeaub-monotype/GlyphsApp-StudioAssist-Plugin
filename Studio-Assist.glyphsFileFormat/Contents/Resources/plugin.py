###########################################################################################################
#
#
# File Filter Plugin
# Implementation of a Glyphs App plugin that shows up in the Filter menu dropdown.
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
import os
import test
from log import Log
from rest import Api
import re


from GlyphsApp import *
from GlyphsApp.plugins import *
from vanilla import *

from urllib.parse import urljoin
import zipfile
import unicodedata

from Foundation import NSURL
from AppKit import NSAffineTransform



#
#
# Called when
#
# Todo:
#
class StudioAssist(FilterWithDialog):

    # In this method you set all attributes that describe the plug-in, such as its name etc.
    @objc.python_method
    def settings(self):

        self.gen_ai_plugin_version = "1.0.4"

        self.menuName = Glyphs.localize(
            {
                "en": f"Monotype Studio Assist {self.gen_ai_plugin_version}",
                "de": f"Monotype Studioassistent {self.gen_ai_plugin_version}",
                "fr": f"Monotype Assistance Studio {self.gen_ai_plugin_version}",
                "es": f"Monotype Asistente de estudio {self.gen_ai_plugin_version}",
                "pt": f"Monotype Assistência de estúdio {self.gen_ai_plugin_version}",
                "jp": f"Monotype スタジオアシスト {self.gen_ai_plugin_version}",
                "ko": f"Monotype 스튜디오 어시스트 {self.gen_ai_plugin_version}",
                "zh": f"Monotype 工作室协助 {self.gen_ai_plugin_version}",
            }
        )


        # The base URL for the GenAI POST
        self.gen_ai_base_url            = "https://glyphgenai-pp.monotype.com"     
        self.gen_ai_POST_font_url       = "/v1/font-outline/outline"
        self.gen_ai_GET_status_url      = "/v1/font-outline/outline/{font_id}/status"
        self.gen_ai_GET_zip_file_url    = "/v1/font-outline/outline/{font_id}"
        self.gen_ai_GET_engine_status   = "/v1/font-outline/engine-status"

        self.root_path = "~/Desktop/MonotypeGenAI/"
        self.export_path = ""
    

        # Build the UI
        width = 700
        height = 275

        GenAI_UI_start_x_position = 5
        GenAI_UI_sart_y_position = 50

        Kerning_UI_start_x_position = 5
        Kerning_UI_sart_y_position = 50

        self.w = Window((width, height))

        # (left, top, width, height)
        self.w.tabs = Tabs((20, 10, -10, -10), ["Glyph Generation", "Kerning"])


        # Outline Generation Tab
        self.genAITab = self.w.tabs[0]
        
        self.genAITab.UnicodeRangeLabel = TextBox(
            (GenAI_UI_start_x_position, GenAI_UI_sart_y_position, 375, 25),
            "Enter hexidecimal unicode values or range to generate",
        )

        self.genAITab.UnicodeRangeEdit = EditText(
            (GenAI_UI_start_x_position, GenAI_UI_sart_y_position + 25, 400, 25),
            callback=self.unicodeRangeCallback,
            placeholder="example: 0041-004f, 0054, 0056",
            continuous=True,  # call the callback on each key stroke
        )

        # Be very careful about the position of buttons
        # In some cases button events wont happen if for
        # example label is placed over a button
        self.genAITab.generateButton = Button(
            (GenAI_UI_start_x_position, GenAI_UI_sart_y_position + 60, 150, 50), "Generate Outlines", callback=self.generateOutlinesButton
        )

        self.genAITab.progressSpinner = ProgressSpinner(
            (525, 50, 50, 50), displayWhenStopped=False
        )
        
        # Progress Label
        # used to communcate the status of the plugin to the end user
        self.genAITab.progressLabelBox = Box((GenAI_UI_start_x_position, GenAI_UI_sart_y_position + 125, 600, 25))
        self.genAITab.progressLabel = TextBox((GenAI_UI_start_x_position, GenAI_UI_sart_y_position + 127, 600, 25), "")


        self.genAITab.diagnosticLabelBox = Box((GenAI_UI_start_x_position, GenAI_UI_sart_y_position + 160, 600, 25))
        self.genAITab.diagnosticLabel = TextBox((GenAI_UI_start_x_position, GenAI_UI_sart_y_position + 162, 600, 25), "")
        self.diagnosticStatus = True


        # Kerning Tab
        self.kerningTab = self.w.tabs[1]
        self.kerningTab.text = TextBox((10, 10, -10, -10), "TBD")

        self.dialog = self.w.tabs.getNSTabView()
     
     

    #
    #
    # Called when the plug-in gets initialized upon Glyphs.app startup
    #
    # Todo:
    #
    @objc.python_method
    def start(self):

        # reset the diagnostic status
        self.diagnosticStatus = True

        # Your init code goes here...
        self.progressLog    = Log(self.genAITab.progressLabel)
        self.diagnosticLog  = Log(self.genAITab.diagnosticLabel)
        self.network        = Api(self.progressLog)


        self.progressLog.info(f"Studio Assist Plugin Version {self.gen_ai_plugin_version} Starting...")
        self.genAITab.generateButton.enable(False)
        self.font = Glyphs.font
        self.export_path = os.path.expanduser(self.root_path + self.font.familyName)
        self.progressLog.fontInfo(self.font)
        self.list_of_unicodes = []
        self.list_of_AI_generated_outlines = []

        # This method is called when a user generates glyphs which
        # triggers the plugin to export the active font file to 
        # be POSTED back to the genAI service
        Glyphs.addCallback(self.exportCallback, DOCUMENTEXPORTED)
       

        # Run the diagnostic tests on the font to make sure it is
        # properly configured to work with the GenAI service
        self.runDiagnosticTests()


        if self.diagnosticStatus:
            self.progressLog.info(f"Studio Assist Plugin Version {self.gen_ai_plugin_version} Ready...")
            
            # pre-populate the unicode range with the selected glyphs
            self.genAITab.UnicodeRangeEdit.set(self.getSelectedLayers())
            

        else:
            self.progressLog.error(f"Studio Assist Plugin Version {self.gen_ai_plugin_version} Not Ready...")



        
    #
    #
    # Called when
    #
    # Todo: Figure out how to use this 
    #
    @objc.python_method
    def filter(self, layer, inEditView, customParameters):
        return
        # Apply your filter code here


    #
    #
    # Called when
    #
    # Todo:  
    #
    @objc.python_method
    def getSelectedLayers(self):
        selectedLayers = self.font.selectedLayers
        unicodes = []

        for layer in selectedLayers:
            u = str(int(layer.parent.unicode,16))
            x = hex(int(u)).split('x')
            unicodes.append(x[1])
        
        comma_seperated = ', '.join(map(str, unicodes))

        return comma_seperated
        

    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def generateOutlinesButton(self, sender):
        
        self.genAITab.progressSpinner.start()
        
        self.progressLog.info("Generating Outlines")
        self.generateOutlines()

        self.genAITab.generateButton.enable(False)
        self.genAITab.progressSpinner.stop()



    #
    #
    # Called when
    #
    # Todo:
    # Fix familyname issue on export
    #
    @objc.python_method
    def generateOutlines(self):

        self.list_of_AI_generated_outlines.clear()

        post_url = urljoin(self.gen_ai_base_url, self.gen_ai_POST_font_url)
        poll_url = urljoin(self.gen_ai_base_url, self.gen_ai_GET_status_url)
        get_font_url = urljoin(self.gen_ai_base_url, self.gen_ai_GET_zip_file_url)

        self.progressLog.info(f"Exporting the font here {self.export_path}")

        if self.exportOTFFontFile(self.export_path):
        
            # the full path to the exported font file is retrieved
            # after the font is exported by a callback 
            parts = self.full_export_font_path.split(".")
            myTuple = (parts[0], "GENERATED.zip")
            self.full_path_to_zip = ".".join(myTuple)

            #
            # Plugin POSTs the font  
            # Server responds with 202 and font_id
            # Plugin receives 202

            # Plugin enters continuous loop for 10 minutes
            # Plugin GETs the status using the font_id
            #  if Server responds with 503
            #  Plugin waits 1 minute goes to top of loop
            #  else Server responds with 200
            # Plugin advances to next step

            # Plugin GETs the zipf ile
            # Plugin imports images
            # etc...

            # post the font so that the service can do the fine tuning
            self.progressLog.info(f"Posting the font to {post_url}")
            post_status, font_id = self.network.post_font(
                post_url, self.full_export_font_path
            )

            #
            if post_status == 202:
                self.progressLog.info(f"Polling {poll_url} for completion")
                poll_url = poll_url.replace("{font_id}", font_id)
                poll_status = self.network.poll_for_completion(poll_url, font_id)       
            
            
            # 
            elif post_status == 503:
                self.progressLog.error(f"Error: {post_status} return code {font_id}")
                return


            #
            elif post_status == 200:
                self.progressLog.info(f"POST completed font_id is {font_id}")
                get_font_url = get_font_url.replace("{font_id}", font_id)
                self.progressLog.info(f"GETing the zip file {get_font_url}")

                list_of_characters = []

                #                 
                for decimal_code in self.list_of_unicodes:
                    character_code = chr(decimal_code)
                    list_of_characters.append(character_code)
                    unicode_string = ''.join(list_of_characters)

            
                # during this step the plugin will retrieve a zip file that has the 
                # AI generated outlines for the requested characters
                #
                get_font_status = self.network.get_genai_font_zip(
                    get_font_url,
                    self.full_path_to_zip,
                    font_id,
                    unicode_string
                 )


                # unpack the images and verify there is one image for each unicode requested
                #
                if get_font_status == 200:
                    self.progressLog.info(f"Unpacking the zip file {self.full_path_to_zip}")
                    extraction_folder = os.path.join(self.export_path, "Extracted")
                                            
                    if not os.path.exists(extraction_folder):
                        os.makedirs(extraction_folder)
                                        
                    with zipfile.ZipFile(self.full_path_to_zip, "r") as zip_ref:
                        zip_ref.extractall(extraction_folder)

                    self.progressLog.info(f"Importing the oulines from {extraction_folder}")
                    self.import_glyph_outlines(extraction_folder)
                
                else:
                    self.progressLog.error(f"Error: {get_font_status}")

            
            else:
                self.progressLog.error(f"Error: POST failed with a {post_status}")
                return


     
    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def import_glyph_outlines(self, directory):

        # Import any of the AI generated outlines that were received
        missing_files = self.checkAllGenAISVGFilesReceived(directory)

        if missing_files:
            self.progressLog.error(f"Error: Missing requested AI generated outline image files")
        
        self.importRequestedGlyhs()


    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def checkAllGenAISVGFilesReceived(self, directory):
        missing_files = 0

        self.progressLog.info(f"Checking for AI generated outlines from {directory}")
        
        for decimal_value in self.list_of_unicodes:
            zero_filleda_pattern = hex(decimal_value)[2:].upper().zfill(4)
            filename = zero_filleda_pattern + ".svg"
            self.progressLog.info(f"Searching {directory} for {filename}")

            path = self.searchFiles(directory, filename)

            if path:
                self.progressLog.info(f"File found {path}")
                self.list_of_AI_generated_outlines.append(path)
            else:
                self.progressLog.error(f"Error: File {filename} not found")
                missing_files = missing_files + 1

        return missing_files



    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def searchFiles(self, dir_path, filename):

        for entry in os.scandir(dir_path):
            if entry.is_file() and entry.name == filename:
                return entry.path
            elif entry.is_dir():
                result = self.searchFiles(entry.path, filename)
                if result:
                    return result

        return None
    



    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def importRequestedGlyhs(self):
        for unicode_filename in self.list_of_AI_generated_outlines:
            # the list of AI generated outlines is in unicode format
            # for example the files are labeled as 0041.svg, 0042.svg etc
            # when importing the outline the filename needs to match the 
            # character name for example 0041.svg needs to be imported as A.svg

            svg_filename = os.path.basename(unicode_filename)
            svg_path = unicode_filename.split(svg_filename)[0]
            hex_str = svg_filename.strip(".svg")
            decimal_value = int(hex_str, 16)
            decimal_to_character = chr(decimal_value)

            try:
                character = unicodedata.name(decimal_to_character)
                new_name = f"{decimal_to_character}.svg"
                character_filename = os.path.join(os.path.dirname(unicode_filename), new_name)
                self.importGlyph(svg_filename, new_name, svg_path)

            except ValueError:
                self.progressLog.error(f"Error: Imported File Missing {character_filename}")   

            


    #
    #
    # The AI generated images are labeled with their unicode value
    # but Glyphs App expects them to be named after the character
    # This method will create a temporary softlink using the character
    # value and point it to the  to the unicode labeled file
    # 
    # For example ln -s 0041.svg A.svg
    #
    # Todo:
    #
    # importGlyph(self, unicode_value, character, svg_file_path)
    #
    @objc.python_method
    def importGlyph(self, svg_filename, character_filename, svg_path):

        thisFont = Glyphs.font

        svgFileUrl = NSURL.alloc().initFileURLWithPath_(os.path.join(svg_path, svg_filename))
        characterFileUrl = NSURL.alloc().initFileURLWithPath_(os.path.join(svg_path, character_filename))

        try:
            # Create a symbolic link to the from the unicode labeled file to the character labeled file
            # This is done so that the file can be imported into Glyphs App
            os.symlink(svgFileUrl, characterFileUrl)
            self.progressLog.info(f"Creating symlink: {svgFileUrl} {characterFileUrl}")

            glyphName = os.path.basename(character_filename).replace(".svg", "")

            # Delete the glyph if it already exists then create a new one
            del thisFont.glyphs[glyphName]
            new_glyph = GSGlyph(glyphName)
            thisFont.glyphs.append(new_glyph)

            # Create a new layer for the glyph
            layer = GSLayer()
            new_glyph.layers[thisFont.selectedFontMaster.id] = layer

            activeLayer = thisFont.selectedFontMaster.id

            layerOfGlyph = thisFont.glyphs[glyphName].layers[activeLayer]

            result = layerOfGlyph.importOutlinesFromURL_scale_error_(characterFileUrl, 1, None)

            # Remove the symbolic link
            try:
                os.unlink(characterFileUrl)  # or os.remove(link_name)
                self.progressLog.info(f"Removed symlink: {svgFileUrl} {characterFileUrl}")
                self.progressLog.info(f"Character {glyphName} imported")

                # Correct the path direction
                layerOfGlyph.correctPathDirection()
                
            except FileNotFoundError:
                self.progressLog.error(f"Symbolic link not found: {svgFileUrl} {characterFileUrl} {e.strerror}")

        except OSError as e:
            self.progressLog.error(f"Creating symlink failed: {svgFileUrl} {characterFileUrl} {e.strerror}")





    #
    #
    # Called when Action triggered by UI
    #
    # Todo: Allowed characters to GET a-zA-Z as of now.
    #
    @objc.python_method
    def unicodeRangeCallback(self, sender):

        # clear the list
        self.list_of_unicodes.clear()
        self.list_of_AI_generated_outlines.clear()

        text = sender.get().strip()

        if len(text):
            # Split by commas to handle individually separated values
            parts = text.split(",")

            for part in parts:
                if len(part):
                    part = part.strip()

                    if "-" in part:  # Handle ranges
                        start, end = part.split("-")
                        
                        if start and end:
                            self.progressLog.info(f"start {start}  end {end}")

                            start = int(start, 16)
                            end = int(end, 16)

                            if start and end > start:
                                for code in range(start, end + 1):
                                    self.list_of_unicodes.append(code)

                    else:
                        # Handle individual Unicode characters
                        part = int(part, 16)
                        self.list_of_unicodes.append(part)

 
        
        if len(self.list_of_unicodes):
            self.genAITab.generateButton.enable(True)
        else:
            self.genAITab.generateButton.enable(False)






    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def exportOTFFontFile(self, export_folder):

        # Check if the folder exists, if not, create it
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)
        
        # Attempt to export the font
        try:
            for instance in Glyphs.font.instances:
                result = instance.generate(
                    FontPath=export_folder,
                    Format=OTF,
                    AutoHint=False,
                    RemoveOverlap=True,
                    UseProductionNames=True,
                )

                if result is True:
                    self.progressLog.info(f"Font exported successfully to {self.full_export_font_path}")
                    return True

                else:
                    self.progressLog.error(f"Export Failed: {result}")
                    return False

        except Exception as e:
            self.progressLog.error(f"Export failed: {e}")
            return False




    #
    #
    # Called when a font is exported by glyphs app if a font is exported. 
    # This is called for every instance and notification.object() will 
    # contain the path to the final font file. 
    #
    # Todo:
    #
    @objc.python_method
    def exportCallback(self, info):
        try:
            obj = info.object()
            self.full_export_font_path = obj['fontFilePath']
           
        except:
            # Error. Print exception.
            import traceback
            self.progressLog.error(f"Export failed: {traceback.format_exc()}")  




    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def runDiagnosticTests(self):

        test_obj = test.Test(self.font)

        #####

        if self.diagnosticStatus:
            # Testing the font to make sure has only one master
            self.progressLog.info("Checking masters")

            number_of_masters = test_obj.calculateMasters()

            if number_of_masters == 1:
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
                )
                self.diagnosticLog.info("Font has 1 master")

            else:
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
                )
                self.diagnosticLog.error(f"Font does not have the requied 1 master, font has {number_of_masters} masters")
                self.diagnosticStatus = False

        #####

        if self.diagnosticStatus:
            # Check that the font has the required characters
            self.progressLog.info("Checking required characters are present")

            missingCharacters = test_obj.calculateMissingCharacters()
            if len(missingCharacters):
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
                )
                self.diagnosticLog.error(f"Font is missing characters: {', '.join(missingCharacters)}")
                self.diagnosticStatus = False

            else:
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
                )
                self.diagnosticLog.info(f"Font has required characters")
             

        #####


        if self.diagnosticStatus:
            # Check that the required characters actually have outlines
            self.progressLog.info("Checking required outlines present")

            missingOutlines = test_obj.calculateMissingOutlines()
            if len(missingOutlines):
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
                )
                self.diagnosticLog.error(f"Font is missing outlines: {', '.join(missingOutlines)}")
                self.diagnosticStatus = False

            else:
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
                )
                self.diagnosticLog.info("Font has required outlines")
                

        #####


        if self.diagnosticStatus:
            # Check that the font is using the correct UPM
            self.progressLog.info("Checking required Units per Em (UMM)")

            units_per_em = test_obj.calculateUPM()
            if units_per_em == 1000:
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
                )
                self.diagnosticLog.info(f"Font has required UPM {units_per_em}")
            else:
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
                )
                self.diagnosticLog.error(f"Font does not have required UPM of 1000, font UPM is currently set to {units_per_em}")
                self.diagnosticStatus = False


        #####


        if self.diagnosticStatus:
            # Check that the font has the ascender and descender set in the OS/2 table
            self.progressLog.info("Checking ascender and descender values are set in the OS/2 table")

            ascender = test_obj.OS2TableGetAscender()
            descender = test_obj.OS2TableGetDescender()

            self.progressLog.info(f"Ascender: {ascender} Descender: {descender}")

            if ascender != 0 and descender != 0:
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
                )
                self.diagnosticLog.info(f"Font has required ascender and descender set in the OS/2 table")
            else:
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
                )
                self.diagnosticLog.error(f"Font does not have required ascender and descender values set in the OS/2 table")
                self.diagnosticStatus = False


        #####


        if self.diagnosticStatus:
            # Testing the network connection
            endpoint = urljoin(self.gen_ai_base_url, self.gen_ai_GET_status_url)
            endpoint = endpoint.replace("{font_id}", "1234")
            
            self.diagnosticLog.info(f"Checking network connection {endpoint}")        

            result = self.network.ping_url(endpoint)
            if(result == 200):
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
                )
                self.diagnosticLog.info(f"Network connection good")

            else:
                self.genAITab.diagnosticLabelBox.setBorderColor(
                    NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
                )
                self.diagnosticLog.error(f"Network connection failure {result}")
                self.diagnosticStatus = False



    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
