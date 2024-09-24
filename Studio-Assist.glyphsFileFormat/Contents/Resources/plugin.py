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

        self.gen_ai_plugin_version = "1.0.3"

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
        # self.gen_ai_base_url            = "http://172.28.1.197:5000"
        self.gen_ai_base_url            = "https://glyphgenai-pp.monotype.com"     
        self.gen_ai_POST_font_url       = "/v1/font-outline/outline"
        self.gen_ai_GET_status_url      = "/v1/font-outline/outline/{font_id}/status"
        self.gen_ai_GET_zip_file_url    = "/v1/font-outline/outline/{font_id}"
        self.gen_ai_GET_engine_status   = "/v1/font-outline/engine-status"


        #self.gen_ai_base_url = "http://172.28.1.197:5000"
        #self.gen_ai_monotype_url = "https://www.monotype.com"
        #self.gen_ai_url_post_font = "/v1/font-outline/outline"
        #self.gen_ai_url_get_status = "/v1/font-outline/outline/{font_id}/status"
        #self.gen_ai_url_get_font = "/v1/font-outline/outline/{font_id}"

        self.gen_ai_debug_simulate_api_calls = False
        self.gen_ai_debug_shift_imported_glyphs = False
        self.gen_ai_debug_scale_imported_glyphs = False
        self.root_path = "~/Desktop/MonotypeGenAI/"
        self.export_path = ""
    



        # Build the UI
        width = 800
        height = 500

        self.w = Window((width, height))
 
        #self.w.group = Group((0, 0, width, height))


        # (left, top, width, height)
        self.w.tabs = Tabs((20, 10, -10, -10), ["Glyph Generation", "Kerning"])
        self.genAITab = self.w.tabs[0]
        
        self.genAITab.EndPointsBox = Box((5, 25, 400, 25))
        self.genAITab.EndPointsLabel = TextBox((10, 27, 400, 22), "Endpoint Status")

        self.genAITab.MasterLabelBox = Box((5, 55, 400, 25))
        self.genAITab.MasterLabel = TextBox((10, 57, 400, 22), "Master Status")

        self.genAITab.CharacterLabelBox = Box((5, 85, 400, 25))
        self.genAITab.CharacterLabel = TextBox((10, 87, 400, 22), "Character Status")

        self.genAITab.OutlineLabelBox = Box((5, 115, 400, 25))
        self.genAITab.OutlineLabel = TextBox((10, 117, 400, 22), "Outline Status")

        self.genAITab.UPMLabelBox = Box((5, 145, 400, 25))
        self.genAITab.UPMLabel = TextBox((10, 147, 400, 22), "Units per Em Status")

        self.genAITab.UnicodeRangeLabel = TextBox(
            (5, 200, 375, 25),
            "Enter hexidecimal unicode values or range to generate",
        )
        self.genAITab.UnicodeRangeEdit = EditText(
            (5, 225, 400, 25),
            callback=self.unicodeRangeCallback,
            placeholder="example: 0041-004f, 0054, 0056",
            continuous=True,  # call the callback on each key stroke
        )
        # Be very careful about the position of buttons
        # In some cases button events wont happen if for
        # example label is placed over a button
        self.genAITab.generateButton = Button(
            (5, 260, 150, 50), "Generate Outlines", callback=self.generateOutlinesButton
        )

        self.genAITab.progressSpinner = ProgressSpinner(
            (525, 285, 50, 50), displayWhenStopped=False
        )

        self.genAITab.progressLabel = TextBox((5, 360, 600, 25), "")

        # Development Options
        # left, top, width, height
        self.genAITab.box = Box((460, 25, 200, 200))
        self.genAITab.boxtext = TextBox((465, 30, 150, 25), "Developer Options")

        self.genAITab.simulateAPICalls = CheckBox(
            (465, 65, -10, 20),
            "Simulate API Calls",
            callback=self.simulateAPICalls,
            value=False,
        )


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

        # Your init code goes here...
        self.progressLog    = Log(self.genAITab.progressLabel)
        self.networkLog     = Log(self.genAITab.EndPointsLabel)
        self.mastersLog     = Log(self.genAITab.MasterLabel)
        self.characterLog   = Log(self.genAITab.CharacterLabel)
        self.outlinesLog    = Log(self.genAITab.OutlineLabel)
        self.upmLog         = Log(self.genAITab.UPMLabel)
        self.network        = Api(self.networkLog)


        self.progressLog.info(f"Studio Assist Plugin Version {self.gen_ai_plugin_version} Starting...")
        
        self.genAITab.generateButton.enable(False)

        self.font = Glyphs.font
      
        self.export_path = os.path.expanduser(self.root_path + self.font.familyName)

        self.progressLog.fontInfo(self.font)

        self.list_of_unicodes = []
        self.list_of_AI_generated_outlines = []

        test_obj = test.Test(self.font)


        # This callback is called when a user generates glyphs which
        # triggers the plugin to export the active font file to 
        # be POSTED back to the genAI service
        Glyphs.addCallback(self.exportCallback, DOCUMENTEXPORTED)
       

        #####

        # Testing the font to make sure has only one master
        self.mastersLog.info("Checking masters")

        if test_obj.calculateMasters() == 1:
            self.genAITab.MasterLabelBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
            )
            self.mastersLog.info("Font has 1 master")

        else:
            self.genAITab.MasterLabelBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
            )
            self.mastersLog.error("Font has more than 1 master")

        #####

        # Check that the font has the required characters
        self.characterLog.info("Checking required characters are present")

        missingCharacters = test_obj.calculateMissingCharacters()
        if len(missingCharacters):
            self.genAITab.CharacterLabelBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
            )
            self.characterLog.error(f"Font is missing characters: {', '.join(missingCharacters)}")

        else:
            self.genAITab.CharacterLabelBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
            )
            self.characterLog.info(f"Font has required characters")

        #####

        # Check that the required characters actually have outlines
        self.outlinesLog.info("Checking required outlines present")

        missingOutlines = test_obj.calculateMissingOutlines()
        if len(missingOutlines):
            self.genAITab.OutlineLabelBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
            )
            self.outlinesLog.error(f"Font is missing outlines: {', '.join(missingOutlines)}")

        else:
            self.genAITab.OutlineLabelBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
            )
            self.outlinesLog.info("Font has required outlines")

        #####

        # Check that the font is using the correct UPM
        self.upmLog.info("Checking required Units per Em (UMM)")

        units_per_em = test_obj.calculateUPM()
        if units_per_em == 1000:
            self.genAITab.UPMLabelBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
            )
            self.upmLog.info(f"Font has required UPM {units_per_em}")
        else:
            self.genAITab.UPMLabelBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
            )
            self.upmLog.error(f"Font does not have required UPM {units_per_em}")

        #####

        # Testing the network connection
        endpoint = urljoin(self.gen_ai_base_url, self.gen_ai_GET_status_url)
        endpoint = endpoint.replace("{font_id}", "1234")
        
        self.networkLog.info(f"Checking network connection {endpoint}")        

        result = self.network.ping_url(endpoint)
        if(result == 200):
            self.genAITab.EndPointsBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(0, 1, 0, 0.5)
            )
            self.networkLog.info(f"Network connection good {endpoint}")
            self.progressLog.info(f"Studio Assist Plugin Version {self.gen_ai_plugin_version} Ready...")


        else:
            self.genAITab.EndPointsBox.setBorderColor(
                NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 0.5)
            )
            self.networkLog.error(f"Network connection failure {result}")

        # pre-populate the unicode range with the selected glyphs
        self.genAITab.UnicodeRangeEdit.set(self.getSelectedLayers())



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
        
        if self.gen_ai_debug_simulate_api_calls:
            self.progressLog.info("Simulating Outline Generation")
            self.simulateGeneratingOutlines()
        else:
            self.progressLog.info("Generating Outlines")
            self.generateOutlines()

        self.genAITab.progressSpinner.stop()
        self.genAITab.generateButton.enable(False)


    #
    #
    # Called when
    #
    # Todo:
    #
    @objc.python_method
    def simulateGeneratingOutlines(self):
        # The data in the SVG should be placed that the origin (0, 0) is at the top left of the glyph.
        # Glyphs will shift it up by the height of the view box as the coordinate systems in
        # font/Glyphs and .svg are different.
        parts = __file__.split("plugin.py")
        
        path = os.path.join(parts[0], "SimulatedOutlineImages")
        self.import_glyph_outlines(path)

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

            # post the font so that the service can do the fine tuning
            self.progressLog.info(f"Posting the font to {post_url}")
            post_status, font_id = self.network.post_font(
                post_url, self.full_export_font_path
            )

            # 
            # POSTing a font can be time consuming event, currently it can take 
            # upwards of 50 minutes to complete the "fine tuning".  The early design 
            # of the plugin would make the POST API call and then enter into a 
            # polling situation where the plugin would repeatedly ask the service
            # if the fine tuning was completed.  Upon completeion the plugin would
            # move on to the next step which is to GET the zip file with the outlines.
            #
            # This turns out not to be a good design because the service so for now 
            # the plugin will POST the font and will then skip over the polling and
            # issue the GET outlines API call.
            # 
            # This user experience will be worked out in the future.
            #
            if post_status == 202:
                self.progressLog.info(f"Polling {poll_url} for completion")
                poll_url = poll_url.replace("{font_id}", font_id)
                poll_status = self.network.poll_for_completion(poll_url, font_id)



            
            if post_status == 200:
                self.progressLog.info(f"POST completed font_id is {font_id}")
                get_font_url = get_font_url.replace("{font_id}", font_id)
                self.progressLog.info(f"GETing the zip file {get_font_url}")

                list_of_characters = []




                # for long lists of characters the plugin will need to do multiple GET calls
                # to retrieve the outlines.
                # fonr now limit the number of characters to 5
                #
                #for i in range(0, len(self.list_of_unicodes), 5):
                 #   short_list = ''.join(self.list_of_unicodes[i:i+5])
                  
                  #  self.progressLog.info(f"Short list {short_list}")
                
                for unicode in self.list_of_unicodes:
                    decimal_to_character = chr(int(unicode, 16))
                    list_of_characters.append(decimal_to_character)
                    unicode_string = ''.join(list_of_characters)

            
                # during this step the plugin will retrieve a zip file that has the 
                # AI generated outlines for the requested characters
                #
                get_font_status = self.network.get_genai_font_zip(
                    get_font_url,
                    self.full_path_to_zip,
                    font_id,
                    list_of_characters
                 )


                # unpack the images and verify there is one image for each unicode requested
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

            # 
            # The service that handles the POST call is running on a single GPU instance
            # and can only handle one request at a time.  If the service is busy it will
            # return a 503 status code.  The plugin will need to retry the POST call at a 
            # later time. 
            # In the future the plan is to have the service scale to handle multiple requests
            #
            elif post_status == 503:
                self.progressLog.error(f"Error: {post_status} return code {font_id}")

            else:
                self.progressLog.error(f"Error: POST failed with a {post_status}")


     
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
        
        for pattern in self.list_of_unicodes:
            zero_filleda_pattern = pattern.zfill(4)
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
                self.progressLog.info(f"Glyph {glyphName} imported")

                # Correct the path direction
                layerOfGlyph.correctPathDirection()
                self.progressLog.info(f"Correcting path direction for {glyphName}")

                # align the glyph to the baseline
                self.shiftAndScale(layerOfGlyph)

            except FileNotFoundError:
                print(f"Symbolic link not found: {svgFileUrl} {characterFileUrl} {e.strerror}")

        except OSError as e:
            self.progressLog.error(f"Creating symlink failed: {svgFileUrl} {characterFileUrl} {e.strerror}")




    #
    #
    # Called when 
    #
    # Todo:
    #
    @objc.python_method
    def shiftAndScale(self, layer):

        # Access the current font and selected glyph layer
        font = self.font  # Current font
       
        # Get the cap height from the font's master
        cap_height = font.masters[0].capHeight

        # Get the bounding box of the glyph (the highest and lowest Y-coordinates)
        min_y = min(node.y for path in layer.paths for node in path.nodes)
        max_y = max(node.y for path in layer.paths for node in path.nodes)

        # Calculate the current height of the glyph
        current_height = max_y - min_y
       
        # Calculate the scale factor to match the cap height
        scale_factor = cap_height / current_height

        # Create a transformation matrix
        transform = NSAffineTransform.transform()

        # Step 1: Move the glyph to the baseline (shift Y so min_y becomes 0)
        if self.gen_ai_debug_shift_imported_glyphs:
            transform.translateXBy_yBy_(0, -min_y)
        else:
            transform.translateXBy_yBy_(0, 0)

        # Step 2: Scale the glyph to match the cap height
        if self.gen_ai_debug_scale_imported_glyphs:
            transform.scaleBy_(scale_factor)
        else:
            transform.scaleBy_(1)
        
        # Apply the transformation to the glyph layer
        layer.applyTransform(transform.transformStruct())

        # Redraw the view to reflect changes
        layer.clearSelection()
        layer.updateMetrics()





    #
    #
    # Called when Action triggered by UI
    #
    # Todo:
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
                        self.progressLog.info(f"start {start}  end {end}")

                        if start and end:
                            # Convert the range to a list of Unicode characters
                            self.list_of_unicodes.extend(
                                [
                                    chr(code)
                                    for code in range(int(start, 16), int(end, 16) + 1)
                                ]
                            )
                    else:
                        # Handle individual Unicode characters
                        # self.list_of_unicodes.append(chr(int(part, 16)))
                        self.list_of_unicodes.append(part)


                    # Todo:  validate the values in the list of unicodes
                    # before enabling the generate button
                    # self.genAITab.generateButton.enable(True)

        # else:
        #   self.genAITab.generateButton.enable(False)
        if len(self.list_of_unicodes):
            #self.genAITab.generateButton.enable(True)
            self.genAITab.generateButton.enable(True)
        else:
            #self.genAITab.generateButton.enable(False)
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
            print(traceback.format_exc())




    #
    #
    # Called when Action triggered by UI
    #
    # Todo:
    #
    @objc.python_method
    def simulateAPICalls(self, sender):
        if sender.get():
            self.gen_ai_debug_simulate_api_calls = True
            self.progressLog.info("Simulation Mode")

        else:
            self.gen_ai_debug_simulate_api_calls = False
            self.progressLog.info("Live Mode")



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
