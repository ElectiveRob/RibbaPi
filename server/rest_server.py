from bottle import run, get, post, request, response, static_file, hook, install, route
import threading
import zipfile
import os
import json
import glob
import imageio
import re
import shutil

class RibbaPiRestServer:
    def __init__(self, ribbapi):
        self.ribbapi = ribbapi

    def start(self):
        # setup routing
        route("/display/brightness", method=['OPTIONS', 'POST'])(self.set_brightness)
        route("/mode", method=['OPTIONS', 'POST'])(self.set_mode)
        route("/moodlight/mode", method=['OPTIONS', 'POST'])(self.set_moodlight_mode)
        route("/gameframe", method=['OPTIONS', 'GET'])(self.get_gameframes)
        route("/gameframe", method=['OPTIONS', 'DELETE'])(self.delete_gameframe)
        get("/gameframe/<gameframe>")(self.get_gameframe)
        post("/gameframe/upload/<name>")(self.upload_gameframe)
        post("/gameframe")(self.select_gameframes)

        # run server
        install(EnableCors())
        threading.Thread(target=run, kwargs=dict(host='127.0.0.1', port=8081)).start()

    # POST /display/brightness [float: value]
    def set_brightness(self):
        value = request.json
        if value > 1.0:
            value = 1.0
        elif value < 0.0:
            value = 0.0
        self.ribbapi.display.set_brightness(value)

    # POST /mode [int: mode]
    def set_mode(self):
        value = request.json
        self.ribbapi.disable_animations()
        if value == 1:
            self.ribbapi.moodlight_activated = True
        elif value == 2:
            self.ribbapi.gameframe_activated = True
        elif value == 3:
            self.ribbapi.blm_activated = True
        elif value == 4:
            self.ribbapi.clock_activated = True
            self.ribbapi.clock_last_shown = 0
        elif value == 5:
            self.ribbapi.play_random = True

        self.ribbapi.stop_current_animation()

    # POST /moodlight/mode [int: mode]
    def set_moodlight_mode(self):
        value = request.json
        self.ribbapi.set_moodlight_mode(value)

    # POST /gameframe/upload/<name>
    def upload_gameframe(self, name):
        file = request.body
        zip = zipfile.ZipFile(file)
        zip.extractall('resources/animations/gameframe_upload/' + name)

    # POST /gameframe sets the playlist
    def select_gameframes(self):
        self.ribbapi.refresh_animations()
        gameframes = request.json;
        self.ribbapi.gameframe_selected = ["resources/animations/gameframe_upload/" + frame for frame in gameframes]

    # DELETE /gameframe deletes a gameframe
    def delete_gameframe(self):
        name = request.json
        shutil.rmtree('resources/animations/gameframe_upload/' + name)
        self.ribbapi.refresh_animations()

    # GET /gameframe
    def get_gameframes(self):
        response.set_header('Content-type', 'application/json')
        return json.dumps(self.get_folder_names('resources/animations/gameframe_upload/'))

    # GET /gameframe/<gameframe>
    def get_gameframe(self, gameframe):
        file_names = sorted(glob.glob('resources/animations/gameframe_upload/' + gameframe + '/*.bmp'), key=alphanum_key)
        print(file_names)
        images = [imageio.imread(filename) for filename in file_names]
        imageio.mimwrite('resources/animations/gameframe_temp.gif', images)
        return static_file('resources/animations/gameframe_temp.gif',  root=".", mimetype='image/gif')

    def get_folder_names(self, dir):
        return [name for name in os.listdir(dir)]

def tryint(s):
    try:
        return int(s)
    except ValueError:
        return s

def alphanum_key(s):
    return [tryint(c) for c in re.split('([0-9]+)', s)]


class EnableCors(object):
    name = 'enable_cors'
    api = 2

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            # set CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

            if request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)

        return _enable_cors





