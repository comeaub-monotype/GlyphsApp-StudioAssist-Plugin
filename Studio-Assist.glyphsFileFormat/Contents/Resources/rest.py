###########################################################################################################
#
#
# File Filter Plugin
# Implementation of api class to handle REST API calls
#
#
###########################################################################################################


from __future__ import division, print_function, unicode_literals
import time
import objc
import ssl
import os
import requests


from GlyphsApp import *
from GlyphsApp.plugins import *


class api(object):

    #
    #
    # Called when the plug-in gets initialized upon Glyphs.app startup
    #
    # Todo:
    #
    @objc.python_method
    def __init__(self):
        # Flag for removing http security protection
        self.httpSecurityOff = True

        if self.httpSecurityOff:
            ssl._create_default_https_context = ssl._create_unverified_context
        else:
            # Currently Crashing
            # ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]
            self.ctx = ssl.create_default_context()



    #
    #
    # Called when the plug-in gets initialized upon Glyphs.app startup
    #
    # Todo:
    #
    @objc.python_method
    def ping_url(self, url):
        time_out = 3

        try:
            response = requests.get(url, timeout=time_out)
            return response.status_code

        except requests.exceptions.RequestException as e:
            return e
            

    

    #
    #
    # Called when the plug-in gets initialized upon Glyphs.app startup
    #
    # Todo:
    #
    @objc.python_method
    def post_font(self, post_url, path_to_font):

        # check path
        if not os.path.exists(path_to_font):
            print("post_font() invalid path ", {path_to_font})
            

        files = {"file": open(path_to_font, "rb")}

        with requests.post(post_url, files=files) as response:
            API_Data = response.json()
            # for key in API_Data:
            #    {print(key, ":", API_Data[key])}
            font_id = API_Data["font_id"]
            status = response.status_code

        return status, font_id

    #
    #
    # Called when the plug-in gets initialized upon Glyphs.app startup
    #
    # Todo:
    # This needs to be polled because it could take a
    # long time for the previous step "finishing" to complete
    #
    @objc.python_method
    def poll_for_completion(self, poll_url, font_id):

        print("poll_for_completion()   url %s font id %s " % (poll_url, font_id))
        payload = {"font_id": font_id}

        with requests.get(poll_url, params=payload) as response:
            status = response.status_code

        return status

    #
    #
    # Called when the plug-in gets initialized upon Glyphs.app startup
    #
    # Todo:
    # After the previous "finishing" step is completed the plugin
    # needs to retrieve the zip file, in addition this API is sent
    # a list of unicodes. Each unicode should correspond to an image
    # that is named after the unicode value for example A.svg is the capital
    # letter A.  This is a requirement from Glhphs App import process
    #
    @objc.python_method
    def get_genai_font_zip(self, fetch_font_url, path_to_zip, font_id, unicode_string):

        print(
            "get_genai_font_zip()   url %s zip to path %s font id %s unicode string %s"
            % (fetch_font_url, path_to_zip, font_id, unicode_string)
        )

        payload = {"font_id": font_id, "unicode_string": unicode_string}

        with requests.get(fetch_font_url, params=payload, stream=True) as r:
            r.raise_for_status()
            with open(path_to_zip, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"Fle `{path_to_zip}` downloaded successfully.")

        return r.status_code
