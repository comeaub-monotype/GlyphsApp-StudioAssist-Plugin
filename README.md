# GlyphsApp-StudioAssist-Plugin
Glyphs App Plugin that provides Glyphs App users with the access to Monotypes generative AI functionality.



Requirements:
    Glyphs App Version 3.2.3 (3260)
    Monotype VPN connection



Installation:

    Glyphs App Plugin Manager:
        This method is not supported.


    ZIP File:
        Unzip the GlyphsApp-StudioAssist-Plugin
        From the GlyphsApp-StudioASsist-Plugin folder locate the Studio-Assist.glyphsFileFormat file and double click on it
        If you have Glyphs App installed it will launch and ask if you wan to install the plugin from an alias on Git or to copy the plugin, select copy the plugin
        Restart Glyphs App
        Open up a font file
        Select a layer from the glyph view
        Click Filter->Monotype Assist (version)
        The Monotype Studio Assist main dialog window should be presented

        Hint: From the glyphs app menu select Window->Macro Panel
              This will open a seperate dialog that will reveal information from the plugin at run time




Development Installation
    If you happen to be a developer and will be making changes to this plugin it's advisable 
    to clone the repository where this source code lives into your development environment and
    then create a softlink from the Glyphs App Plugin area to your development area.

    Clone the repo
        create a new directory
            mkdir plugin-dev-area
        cd into the directory
            cd plugin-dev-area
        clone the repo
            git clone https://github.com/comeaub-monotype/StudioAssist-GlyphsApp-Plugin.git
        open the project folder using VS Code


    Create the soft link
        in order for Glyphs App to resolve the plugin it has to reside in the following folder
        ~(your-path)/Library/Application Support/Glyphs 3/Plugins 

        from a terminal window navigate to 
        ~(yoour-path)/Library/Application Support/Glyphs 3/Plugins

        Restart Glyphs App
        load a font file and select a layer
        click filer->Monotype Assist (version) 
        your development version of Monotype Studio Assist main dialog window should be presented
