from threading import Thread
from app.DVRClass import DVR

class FrameHandler:
    """docstring for FrameHandler"""
    def __init__(self, app):
        self.App = app
        self.run_dvr = {}
        # by cam_id
        self.run_modules = {}

    def process(self, frame):
        cam_id = frame.Cam.getId()

        Thread(target=self.process_draw, args=[frame]).start()

        for module in self.App.Modules:
            if int(frame.Cam.getSettings(module)['is_active']) == 1:
                if cam_id not in self.run_modules:
                    self.run_modules[cam_id] = {}
                if module not in self.run_modules[cam_id]:
                    self.run_modules[cam_id][module] = { 'is_run': False, 'output': None } # 'thread': None

                if not self.run_modules[cam_id][module]['is_run']:
                    self.run_modules[cam_id][module]['is_run'] = True
                    self.run_modules[cam_id][module]['thread'] = Thread(target=self.process_module, args=[{ 'module': module, 'frame': frame }])
                    self.run_modules[cam_id][module]['thread'].start()
            else:
                if cam_id in self.run_modules:
                    if module in self.run_modules[cam_id]:
                        self.run_modules[cam_id][module]['output'] = None

        # self.App.Caps[cam_id].frame_th = None
        # self.App.Caps[cam_id].frame_process = False

    def process_module(self, task):
        cam_id = task['frame'].Cam.getId()
        module = task['module']

        if cam_id in self.run_modules:
            self.run_modules[cam_id][module]['output'] = self.App.Modules[module].process(task['frame'])
            self.run_modules[cam_id][module]['is_run'] = False

    def process_draw(self, frame):
        outputs = []
        cam_id = frame.Cam.getId()

        if cam_id in self.run_modules:
            if len(self.run_modules[cam_id]) > 0:
                for module in self.run_modules[cam_id]:
                    if self.run_modules[cam_id][module]['output']:
                        outputs.append(self.run_modules[cam_id][module]['output'])

        if len(outputs) > 0:
            drawn_frame = self.App.Drawer.process(frame.frame, outputs)
        else:
            drawn_frame = frame.frame

        if cam_id in self.App.Caps:
            self.App.Caps[cam_id].frame_process = False
        else:
            self.run_modules.pop(cam_id, None)

        if not cam_id in self.run_dvr:
            self.run_dvr[cam_id] = DVR(cam_id, self.App.Config.dvr_duration,
                "/".join([self.App.Config.api_endpoint, 
                self.App.Config.api_version]), self.App.Sockets.Client)

        if cam_id in self.run_dvr:
            self.run_dvr[cam_id].frame(frame.frame)

        self.App.Event.emit_frame(drawn_frame, frame.Cam)
