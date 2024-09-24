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
import re
import requests


from GlyphsApp import *
from GlyphsApp.plugins import *


class Api(object):

    #
    #
    # Called when the plug-in gets initialized upon Glyphs.app startup
    #
    # Todo:
    #
    @objc.python_method
    def __init__(self, logger):
        self.networkLog = logger

        # Timeouts for the requests are in seconds
        self.connect_timeout = 30
        self.read_timeout = 30

        
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

        # skipping for now
        return 200;
    
        try:
            response = requests.get(url, timeout=(self.connect_timeout, self.read_timeout))
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            self.networkLog.info(f"Response: {response.status_code}") 
            self.networkLog.info(f"Response: {response.text}")
            return response.status_code

        except requests.exceptions.RequestException as e:
            self.networkLog.info(f"Error: {e}") 
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
            self.networkLog.info(f"post_font() invalid path {path_to_font}") 
            return 404, "Invalid font file path"

     
        #
        # Currently the response is formatted as follows:
        # {
        # "font_id": "59b2355497f57c141f2d1b3f1e198e73",
        # "message": "{'message': 'Fine Tune is Complete for font ID 59b2355497f57c141f2d1b3f1e198e73.'}"
        # }
        #
        headers = {
            "Accept": "application/json"
        }
       
        with open(path_to_font, "rb") as file:
            files = {"fontfile": file}
            response = requests.post(post_url, headers=headers, files=files)
            API_Data = response.json()

            if response.status_code == 200:
                font_id = API_Data["font_id"]
                return response.status_code, font_id
            else:
                message = API_Data["message"]
                return response.status_code, message
            



    #
    #
    # Called when the plug-in gets initialized upon Glyphs.app startup
    #
    # Todo:
    # This needs to be polled because it could take a
    # long time for the previous step "finishing" to complete
    #
    @objc.python_method
    def poll_for_completion(self, poll_url, font_id, interval=5, timeout=60):

        self.networkLog.info(f"poll_for_completion url {poll_url} font id {font_id}") 
        params = {"font_id": font_id}

        start_time = time.time()

        while True:
            try:
                response = requests.get(poll_url, params=params, timeout=(self.connect_timeout, self.read_timeout))
                response.raise_for_status()  # Raise an exception for non-2xx status codes
                self.networkLog.info(f"Response: {response.status_code}") 
                return response.status_code
            
            except requests.exceptions.RequestException as e:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Timed out after {timeout} seconds")
                    time.sleep(interval)
         




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

        self.networkLog.info(f"get_genai_font_zip()  url {fetch_font_url} zip to path {path_to_zip} font id {font_id} unicode string {unicode_string}") 
        params = {"unicode_string": unicode_string}

        try:
            response = requests.get(fetch_font_url, params=params, stream=True, timeout=(self.connect_timeout, self.read_timeout))
            response.raise_for_status()    # Raise an exception for non-2xx status codes
            self.networkLog.info(f"Waiting for download to complete...") 

            try:
                with open(path_to_zip, "wb") as f:
                    progress = ""
                    for chunk in response.iter_content(chunk_size=8192):
                        progress += "."
                        self.networkLog.info(f"Receiving:  {progress}") 
                        f.write(chunk)

                    self.networkLog.info(f"Download complete")
                    return response.status_code

            except Exception as e:
                self.networkLog.error(f"Error: {e}") 
                return e

            
        except requests.exceptions.RequestException as e:
            self.networkLog.error(f"Error: {e}") 
            return e
