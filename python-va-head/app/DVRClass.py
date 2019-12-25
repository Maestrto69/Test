import os
import cv2
import json
import queue
import shutil
import tarfile
import asyncio
import requests
from threading import Thread
from datetime import datetime

"""Класс для сохранения видео"""

# output debug logs to console
OUTPUT_LOGS = True # False

# API endpoint of Core-module # ONLY FOR TEST
## TODO – remove this setting from production. 
# CORE_MODULE_API_ENDPOINT = 'http://0.0.0.0:48655/api/v1'
CORE_MODULE_API_ENDPOINT = 'http://192.168.1.25:8000/api/v1'


##
# output video settings
##
# record filename in FS-store
VIDEO_FILENAME = 'record'
# output video file format
VIDEO_FILEFORMAT = 'mp4'
# output video codec
## this value is equal to cv2.vw_fourcc=mp4v
VIDEO_FOURCC = cv2.VideoWriter_fourcc(*'avc1') #0x31637661 #0x39307076 # 
# default fps value to recover records. 25 – optimal value
DEFAULT_RECOVER_FPS_VALUE = 25
##

# video screenshot file format
SCREENSHOT_FILEFORMAT = 'jpg'

# number of frames to syncing fps value of video record
## default: 150 frames (+-6sec)
FRAMES_NUMBER_FOR_SYNC_FPS_VALUE = 150

##
# FS-store settings
##
# - archive settings
##
# store compressed tar.bz2 jpeg-frames. (!) if you need fps value, you should set STORE_RECORD_LOGS to True (below, fps value log)
STORE_ARCHIVE_JPEG_FRAMES = False
# store videos of released record
STORE_RELEASED_RECORDS = False
# store cdn uploads log, fps value log
STORE_LOGS = False
##
## - name settings
##
# directory name of released records
RELEASED_DIR = 'released'
# directory name of unreleased records
UNRELEASED_DIR = 'unreleased'
# jpeg-frames subdirectory name in unreleased record dir
JPEG_FRAMES_DIR = 'jpeg-frames'
# prefix of jpeg-frames filename
## filename jpeg-frames is filename prefix, self.frame_counter and file format (it always equal to .jpg)
JPEG_FRAMES_FILEPREFIX = 'frame-'
# fps value filename
FPS_VALUE_FILENAME = 'saved_avg_fps.value'
# cdn uploads log filename
CDN_LOG_FILENAME = 'cdn_uploads.log'
##


# DVR class (Digital Video Recorder)
##
## Creates video records from raw frames and store to FS-store by using VideoWriter object from cv2
## Creates Media-records by making requests to API of Core-module
## Uploads video records from FS-store to CDN-module by making POST requests with a Multipart-Encoded File
##
class DVR:

	# begin constructor func. sets config vars and defines helper vars
	##
	def __init__(self, cam_id, duration=60, api_endpoint=CORE_MODULE_API_ENDPOINT, sio=None, work_dir='./tmp_fs_dvr_store'):
		# api endpoint of Core-module
		self.api_endpoint = api_endpoint;

		# absolute or relative(from handler directory) path to DVR work dir
		self.work_dir = work_dir

		# ID of Camera-record in Core-module
		self.cam_id = cam_id

		# fps value of released video
		## it's just a set value, but it will be changed in sync_record_fps func
		self.fps = DEFAULT_RECOVER_FPS_VALUE
				# frame width of released video (px)
		self.frame_width = 1920
		# frame height of released video (px)
		self.frame_height = 1080
		# segment duration of released video (sec)
		## min duration is 60 sec
		if duration < 60:
			self._log('Video duration set to 60sec – minimum', True)
			self.duration = 60
		else:
			self.duration = duration

		# frame width of released video (px)
		# self.frame_width = frame_width
		# # frame height of released video (px)
		# self.frame_height = frame_height

		# output a warning if all store settings are disabled
		if not (STORE_ARCHIVE_JPEG_FRAMES or STORE_RELEASED_RECORDS or STORE_LOGS):
			self._log('Files will not be stored. consts STORE_ARCHIVE_JPEG_FRAMES and STORE_RELEASED_RECORDS and STORE_LOGS are disabled', True)
		##
			
		##
		# other helper variables will be created when first frame of video record is received (in frame func)
		##
		self.frame_counter = 0
		self.fps_synced = False
		self.vw_synced = False
		self.vw_synced_process = False
		self.is_stop = False
		##

		##
		# tasks queue and worker thread for process_frames worker
		##
		self.frames_worker_queue = queue.Queue()
		self.frames_worker_thread = None
		##

		##
		# tasks queue and worker thread for process_unreleased_records worker
		##
		self.unreleased_records_worker_queue = queue.Queue()
		self.unreleased_records_worker_thread = None
		##
		
		# out object of cv2.VideoWriter objects
		self.out = dict()

		##
		# workers
		##
		# run process_frames worker in frames_worker thread
		self.run_process_frames_worker()
		# run process_unreleased_records worker in unreleased_records_worker thread
		self.run_process_unreleased_records_worker()
		##

		##
		# define disabled auto_recover_process flag
		# run auto_recover_records func
		##
		self.auto_recover_process = False
		# self.auto_recover_records() # TODO 03-10 @binizik
		##

		##
		# socket-io
		##
		if not sio is None:
			# socket client
			self.sio = sio;
			# init socket handlers
			self.init_sio_handlers()
		##
		## func end.

	# begin init_sio_handlers func. subscribe on socket-io events 
	##
	## hot record release by req from ui
	##
	def init_sio_handlers(self):
		self._log('init_sio_handlers func ->init dvr_hot_release handler', True)
		self.sio.on('dvr_hot_release_server_req', self.on_dvr_hot_release)
		# func end.

	def on_dvr_hot_release(self, data):
		if data['cam_id'] == self.cam_id:
			self._log('on_dvr_hot_release func ->init', True)
			if not self.auto_recover_process and self.frame_counter > 0 and not self.is_stop:
				self._log('on_dvr_hot_release func ->enable is_stop flag')
				self.is_stop = True

				self._log('on_dvr_hot_release func ->START release process')
				released = self.release()

				if released[0]:
					self._log('on_dvr_hot_release func ->SUCCESSFULLY release process, MEDIA ID: %s' % released[1])
					self.sio.emit('dvr_hot_release_server_res', { 'cam_id': self.cam_id, 'status': True, 'media_id': released[1] })
				else:
					self._log('on_dvr_hot_release func ->FAILED release process')
					self.sio.emit('dvr_hot_release_server_res', { 'cam_id': self.cam_id, 'status': False })
			else:
				self._log('on_dvr_hot_release func ->request declined')
				self.sio.emit('dvr_hot_release_server_res', { 'cam_id': self.cam_id, 'status': False })
			##
		# func end.

	# begin on_hard_stop func. hard stop processes
	##
	def on_hard_stop(self):
		self._log('on_hard_stop func ->HARD STOP PROCESSES', True)

		# join frames_worker thread
		self._log('on_hard_stop func ->INIT JOIN frames_worker queue', True)
		self.frames_worker_queue.join()

		# try release this record
		self._log('on_hard_stop func ->TRY RELEASE', True)
		self.release()

		# join unreleased_records_worker thread
		self._log('on_hard_stop func ->INIT JOIN unreleased_records_worker queue', True)
		self.unreleased_records_worker_queue.join()

		self._log('on_hard_stop func ->HARD STOP PROCESSES – DONE', True)
		## func end.

	# begin auto_recover_records func. check unreleased dir and try recover records
	##
	## checks for jpeg-frames and fps value file
	## if they exist, try to collect and release a record from jpeg frames
	##
	def auto_recover_records(self):
		self._log('auto_recover_records func ->init', True)

		# enable auto_recover_process flag
		self.auto_recover_process = True

		# work dir
		unreleased_dir = os.path.abspath( "/".join([self.work_dir, UNRELEASED_DIR, self.cam_id]) )

		if self.dir_is_exist(unreleased_dir):
			# find subdirs in unreleased dir
			for subdir in os.listdir(unreleased_dir):
				subdir_path = os.path.join(unreleased_dir, subdir)
				fps_value_path = os.path.join(subdir_path, FPS_VALUE_FILENAME)
				jpeg_frames_path = os.path.join(subdir_path, JPEG_FRAMES_DIR)

				if self.dir_is_exist(subdir_path) and self.dir_is_exist(jpeg_frames_path):
					self._log('auto_recover_records func ->found unreleased record at: %s' % subdir, True)

					# check fps value file
					if self.path_is_exist(fps_value_path):
						# get fps value from file
						fps_value = self.get_fps_value_from_file(subdir_path)
						self._log('auto_recover_records func ->found fps_value is %s for unreleased record at: %s' % (fps_value, subdir), True)
					else:
						# set fps value to DEFAULT_RECOVER_FPS_VALUE const
						fps_value = DEFAULT_RECOVER_FPS_VALUE
						self._log('auto_recover_records func ->set default fps_value is %s for unreleased record at: %s' % (fps_value, subdir), True)

					##
					# configurate env to build unreleased record
					##
					# reset env
					self.init_helper_variables()
					self.unreleased_dvr_dir = subdir_path
					self.jpeg_frames_dir = jpeg_frames_path
					self.dvr_date = subdir
					##

					# init cv2.VideoWriter
					self.vw_init()

					# get jpeg-frames list
					frames_list = os.listdir(jpeg_frames_path)

					if len(frames_list) > 0:
						self._log('auto_recover_records func ->found %i frames for unreleased record at: %s' % (len(frames_list), subdir), True)

						# build record from frames
						for frame_i in range(0, len(frames_list)-1):
							if self.path_is_exist(self.get_frame_path(frame_i, jpeg_frames_path)):
								# gets a jpeg-frame from FS-store
								frame = cv2.imread(self.get_frame_path(frame_i, jpeg_frames_path))
								# adds a frame in video record
								self.out[self.get_out_name()].write(frame)

						# try release
						process_release = self.release()

						# check process_release result
						if not process_release[0]:
							self._log('auto_recover_records func ->FAILED release process for unreleased record at: %s' % subdir, True)
						else:
							self._log('auto_recover_records func ->recovered unreleased record from %s MEDIA ID: %s' % (subdir, process_release[1]), True)
							self._log('auto_recover_records func ->SUCCESSFULLY release process for unreleased record at: %s' % subdir, True)
					else:
						self._log('auto_recover_records func ->frames not found error for unreleased record at: %s' % subdir, True)

				else:
					self._log('auto_recover_records func ->ERROR recover for unreleased record at: %s' % subdir, True)
				##
			##
		else:
			self._log('auto_recover_records func ->not found dir for cam_id: %s' % self.cam_id, True)

		# reset env
		self.init_helper_variables()

		# disable auto_recover_proccess flag
		self.auto_recover_process = False

		self._log('auto_recover_records func ->done', True)
		## func end.

	# begin run_process_frames_worker func. init frames_worker thread for process_frames worker and run it
	##
	def run_process_frames_worker(self):
		# init thread
		## optional second param is args=(self or self.frames_worker_queue, but this isn't required)
		self.frames_worker_thread = Thread(target=self.process_frames_worker)
		# run worker thread as a daemon
		self.frames_worker_thread.setDaemon(True)
		self.frames_worker_thread.setName('process_frames_worker')
		# start process_frames_worker func in worker thread
		self.frames_worker_thread.start()
		## func end.

	# begin run_process_unreleased_records_worker func. init unreleased_records_worker thread of process_unreleased_records worker and run it
	##
	def run_process_unreleased_records_worker(self):
		# init thread
		## optional second param is args=(self or self.unreleased_records_worker_queue, but this isn't required)
		self.unreleased_records_worker_thread = Thread(target=self.process_unreleased_records_worker)
		# run worker thread as a daemon
		self.unreleased_records_worker_thread.setDaemon(True)
		self.unreleased_records_worker_thread.setName('records_worker_thread')
		# start process_unreleased_records_worker func in worker thread
		self.unreleased_records_worker_thread.start()
		## func end.

	# begin init_helper_variables func. creates/resets helper variables
	##
	def init_helper_variables(self):
		self.dvr_date = ''
		self.unreleased_dvr_dir = ''
		self.released_dvr_dir = ''
		self.jpeg_frames_dir = ''
		self.frame_counter = 0
		self.is_stop = False
		self.fps_synced = False
		self.vw_synced = False
		self.vw_synced_process = False
		self.sync_sheets = dict()
		## func end.

	# begin get_str_current_datetime func. returns a string of current datetime
	##
	## gets and format current datetime from now func of datetime object
	##
	### @return: string of current datetime
	def get_str_current_datetime(self):
		return datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M-%S")
		## func end.

	# begin log func. outputs debug logs with ID of Camera-record and start datetime of video record
	##
	## show debug logs in outputs if OUTPUT_LOGS const is enabled in head of script
	## if this func was called with force param set to True, then log event is forcibly outputted with FORCE_OUTPUT label
	## (!) TODO - log rotation? from all modules in system level?
	##
	def _log(self, msg, force=False):
		if force:
			print("DVR[%s][FORCE_OUTPUT][camera-%s]: %s" % (self.get_str_current_datetime(), self.cam_id, msg))
		else:
			if OUTPUT_LOGS:
				if hasattr(self, 'dvr_date'):
					print("DVR[%s][camera-%s][segstart-%s]: %s" % (self.get_str_current_datetime(), self.cam_id, self.dvr_date, msg))
				else:
					print("DVR[%s][FORCE_OUTPUT][camera-%s]: %s" % (self.get_str_current_datetime(), self.cam_id, msg))
		## func end.

	# begin dir_is_exist func. returns existence of dir along path or creates it if create_new param set to True
	##
	### @return: bool-flag [False if dir doesn't exist | True if dir is exist or was created]
	def dir_is_exist(self, path, create_new=False):
		if not os.path.isdir(path):
			if create_new:
				os.makedirs(path)
				return True
			else:
				return False
		else:
			return True
		## func end.

	# begin path_is_exist func. returns existence of path
	##
	### @return: bool-flag [False if path doesn't exist | True if path is exist]
	def path_is_exist(self, path):
		if not os.path.exists(path):
			return False
		else:
			return True
		## func end.

	# begin copy_file func. copies file
	##
	def copy_file(self, source, to):
		if self.path_is_exist(os.path.abspath(source)):	
			shutil.copy(os.path.abspath(source), os.path.abspath(to))
		## func end.

	# begin remove_file func. removes file
	##
	def remove_file(self, source):
		if self.path_is_exist(os.path.abspath(source)):	
			os.remove(os.path.abspath(source))
		## func end.

	# begin remove_dir func. R-removes directory
	##
	def remove_dir(self, source):
		if self.dir_is_exist(os.path.abspath(source)):	
			shutil.rmtree(os.path.abspath(source))
		## func end.

	# begin make_tarfile func. compress source_dir into tar file
	##
	def make_tarfile(self, output_filename, source_dir):
		with tarfile.open(os.path.abspath(output_filename), mode='w:bz2') as tar:
			tar.add(os.path.abspath(source_dir), arcname=os.path.basename(source_dir))
			tar.close()
		## func end.

	# begin init_unreleased_dirs func. sets and creates dir of unreleased record and dir of jpeg-frames
	##
	## sets dir of unreleased record by combining self.work_dir var, UNRELEASED_DIR const, Camera-record ID and datetime of start of segment of this record, which separated by "/"
	## sets dir of jpeg-frames by combining given dir path of unreleased record and JPEG_FRAMES_DIR const which are separated by sym "/"
	## checks existence of dirs and creates them if they don't exist
	##
	def init_unreleased_dirs(self):
		self._log('init_unreleased_dirs func')

		self.unreleased_dvr_dir = os.path.abspath("/".join([self.work_dir, UNRELEASED_DIR, self.cam_id, self.dvr_date]))
		self.jpeg_frames_dir = os.path.abspath("/".join([self.work_dir, UNRELEASED_DIR, self.cam_id, self.dvr_date, JPEG_FRAMES_DIR]))

		self.dir_is_exist(self.unreleased_dvr_dir, True)
		self.dir_is_exist(self.jpeg_frames_dir, True)

		self._log('init_unreleased_dirs func->dirs have been settled and created for unreleased record and jpeg-frames')
		## func end.

	# begin init_released_dir func. sets and creates dir of released record
	##
	## sets dir of released record by combining self.work_dir var, RELEASED_DIR const, Camera-record ID and datetime of start of segment of this record, which separated by "/"
	## checks existence of a dir and creates if it doesn't exist
	##
	def init_released_dir(self):
		self._log('init_released_dir func')

		self.released_dvr_dir = os.path.abspath("/".join([self.work_dir, RELEASED_DIR, self.cam_id, self.dvr_date]))

		self.dir_is_exist(self.released_dvr_dir, True)

		self._log('init_released_dir func->dir has been setted and created for released record')
		## func end.

	# begin get_out_name func. returns key name of cv2.VideoWriter (cv2.VW) object in self.out object
	##
	## generates key name by combining Camera-record ID and datetime of start of segment of this record, which separated by "–"
	##
	### @return: string key name of cv2.VW object in self.out object
	def get_out_name(self):
		return "-".join([self.cam_id, self.dvr_date])
		## func end.

	# begin get_output_video_filename func. returns output video filename
	##
	## generates filename by combining VIDEO_FILENAME and VIDEO_FILEFORMAT const, which separeted by "."
	##
	### @return: string output video filename
	def get_output_video_filename(self):
		return ".".join([VIDEO_FILENAME, VIDEO_FILEFORMAT])
		## func end.

	# begin get_unreleased_record_path func. returns absolute path of unreleased record file
	##
	## generates path of unreleased record file by combining absolute path of unreleased dir and filename getted by get_output_video_filename func, which separated by "/"
	##
	### @return: string absolute path of unreleased record file
	def get_unreleased_record_path(self, work_dir=None):
		if work_dir is None:
			work_dir = self.unreleased_dvr_dir

		return os.path.abspath("/".join([work_dir, self.get_output_video_filename()]))
		## func end.

	# begin get_released_record_path func. returns absolute path of released record file
	##
	## generates path of released record file by combining absolute path of released dir and filename getted by get_output_video_filename func, which separated by "/"
	##
	### @return: string absolute path of released record file
	def get_released_record_path(self, work_dir=None):
		if work_dir is None:
			work_dir = self.released_dvr_dir

		return os.path.abspath("/".join([work_dir, self.get_output_video_filename()]))
		## func end.

	# begin get_unreleased_frames_dir_path func. returns absolute path of unreleased frames dir
	##
	### @return: string absolute path of unreleased frames dir
	def get_unreleased_frames_dir_path(self, work_dir=None):
		if work_dir is None:
			work_dir = self.unreleased_dvr_dir

		return os.path.abspath("/".join([ work_dir, JPEG_FRAMES_DIR]))
		## func end

	# begin get_released_frames_dir_path func. returns absolute path of released frames dir
	##
	### @return: string absolute path of released frames dir
	def get_released_frames_dir_path(self, work_dir=None):
		if work_dir is None:
			work_dir = self.released_dvr_dir

		return os.path.abspath("/".join([ work_dir, JPEG_FRAMES_DIR]))
		## func end

	# begin get_frame_path func. returns absolute path of n-th frame file
	##
	### @return: string absolute path of next frame file
	def get_frame_path(self, n, work_dir=None):
		if work_dir is None:
			work_dir = self.get_unreleased_frames_dir_path()

		return os.path.abspath("/".join([ work_dir, JPEG_FRAMES_FILEPREFIX + ".".join([ str(n), SCREENSHOT_FILEFORMAT ]) ]))
		## func end.

	# begin get_next_frame_path func. returns absolute path of next frame file
	##
	## calls get_frame_path func with settled n-th param, which is equal to self.frame_counter
	##
	### @return: string absolute path of next frame file
	def get_next_frame_path(self, work_dir=None):
		if work_dir is None:
			return self.get_frame_path(self.frame_counter)
		else:
			return self.get_frame_path(self.frame_counter, work_dir)
		## func end.

	# begin get_unreleased_cdn_log_path func. returns absolute path of file were named by CDN_LOG_FILENAME const
	##
	### @return: string absolute path of file with cdn uploads log in unreleased record dir
	def get_unreleased_cdn_log_path(self, work_dir=None):
		if work_dir is None:
			work_dir = self.unreleased_dvr_dir

		return os.path.abspath("/".join([work_dir, CDN_LOG_FILENAME]))
		## func end.

	# begin get_released_cdn_log_path func. returns absolute path of file were named by CDN_LOG_FILENAME const
	##
	### @return: string absolute path of file with cdn uploads log in released record dir
	def get_released_cdn_log_path(self, work_dir=None):
		if work_dir is None:
			work_dir = self.released_dvr_dir

		return os.path.abspath("/".join([work_dir, CDN_LOG_FILENAME]))
		## func end.

	# begin create_cdn_log_file func. creates a text file and writes cdn uploads log in unreleased dir
	##
	## creates a file in unreleased record dir and file named by FPS_VALUE_FILENAME const
	##
	def create_cdn_log_file(self, content):
		self._log('create_cdn_log_file func')

		# creates a file in unreleased record dir
		file = open(self.get_unreleased_cdn_log_path(), 'w+')

		# writes content and closes file editing
		file.write(str(content))
		file.close()

		self._log('create_cdn_log_file func ->create log')
		## func end.

	# begin get_unreleased_fps_value_path func. returns absolute path of file were named by FPS_VALUE_FILENAME const
	##
	### @return: string absolute path of file with avg fps value in unreleased record dir
	def get_unreleased_fps_value_path(self, work_dir=None):
		if work_dir is None:
			work_dir = self.unreleased_dvr_dir

		return os.path.abspath("/".join([work_dir, FPS_VALUE_FILENAME]))
		## func end.

	# begin get_released_fps_value_path func. returns absolute path of file were named by FPS_VALUE_FILENAME const
	##
	### @return: string absolute path of file with avg fps value in released record dir
	def get_released_fps_value_path(self, work_dir=None):
		if work_dir is None:
			work_dir = self.released_dvr_dir

		return os.path.abspath("/".join([work_dir, FPS_VALUE_FILENAME]))
		## func end.

	# begin create_fps_value_file func. creates a text file and writes avg fps value for unreleased record
	##
	## creates a file in unreleased record dir and file name is set to FPS_VALUE_FILENAME const
	##
	def create_fps_value_file(self):
		self._log('create_fps_value_file func')

		# creates a file in unreleased record dir
		file = open(self.get_unreleased_fps_value_path(), 'w+')

		value = str(self.fps)

		# writes avg fps value and closes file editing
		file.write(value)
		file.close()

		self._log('create_fps_value_file func ->writed fps value of %s' % value)
		## func end.

	# begin get_fps_value_from_file func. opens a text file and reads avg fps value for unreleased record
	##
	## opens a text file with a name equal to FPS_VALUE_FILENAME const and reads avg fps value
	##
	### @return: string of fps value
	def get_fps_value_from_file(self, work_dir=None):
		self._log('get_fps_value_from_file func')

		if work_dir is None:
			file_path = self.get_unreleased_fps_value_path()
		else:
			file_path = self.get_unreleased_fps_value_path(work_dir)

		# opens a file in unreleased record dir
		file = open(file_path, 'r')

		# reads avg fps value and closes file editing
		value = file.read()
		file.close()

		self._log('get_fps_value_from_file func ->readed fps value of %s' % value)

		# returns fps value
		return value
		## func end.

	# # begin move_record_to_released func. moves file of video record and jpeg-frames dir to released dir
	# ##
	# def move_record_to_released(self):
	# 	# (doesn't work) os.rename func doesn't move files
	# 	# os.rename(self.get_unreleased_record_path(), self.get_unreleased_record_path())

	# 	# copy func is used, not move func (it guaranted that video file has not be lost)
	# 	## copies video record file to released dir
	# 	shutil.copy(self.get_unreleased_record_path(), self.get_released_record_path())
	# 	# copies file of fps value
	# 	shutil.copy(self.get_unreleased_fps_value_path(), self.get_released_fps_value_path())
	# 	# copies jpeg-frames dir to released dir (archive raw frames)
	# 	shutil.copy(self.get_unreleased_frames_dir_path(), self.get_released_frames_dir_path())
	# 	## func end.

	# begin create_media_record func. creates new Media-record in Core-module
	##
	## required filename and filetype [video | photo (for preview screenshot of video record)] for new Media-record
	## API endpoint of Core-module sets by self.api_endpoint from constructor func
	## if filetype='video' then screenshot's Media-record ID is required
	## calls Core-module's API and creates a new Media-record
	## 
	### @return: [result bool-flag, [media_id, cdn_file_url]]
	def create_media_record(self, filename, filetype='video', screenshot_media_id=None, preview_url=None):
		self._log('create_media_record func')

		# association to Camera-record and screenshot (only for videos)
		##
		file_links = { 'cam_id': self.cam_id, 'media_id': None }

		#
		if not screenshot_media_id is None:
			file_links['media_id'] = screenshot_media_id
		#

		# make a request to API of Core-module
		res = requests.post("/".join([self.api_endpoint, 'medias/add']), json={ 'name': filename, 'file_type': filetype, 'file_link': file_links, 'preview_url': preview_url })
		# parse json response
		jres = res.json()

		# some error, record hasn't created
		if not 'id' in jres:
			self._log('create_media_record func->API ERROR: %s' % res.content, True)
			return [False, [res.status_code, res.content]]

		# set file format
		fileformat = VIDEO_FILEFORMAT

		if filetype == 'photo':
			fileformat = SCREENSHOT_FILEFORMAT

		# successfully created
		self._log('create_media_record func ->new media-record has been created with id: %s' % jres['id'])

		# cdn_file_url builds by combining protocol, public host of cdn and cdn record id (cdn_id) with file format separated by "."
		return [True, [jres['id'], "/".join(['http:/', jres['cdn_public_url'], ".".join([jres['cdn_id'], fileformat]) ])]]
		## func end.

	def create_in_DB(self, url1, url2):
		start = self.dvr_date.replace('_', ' ')
		start = start[:11] + start[11:].replace('-', ':')
		end = self.get_str_current_datetime().replace('_', ' ')
		end = end[:11] + end[11:].replace('-', ':')
		
		res = requests.post('/'.join([self.api_endpoint, 'dvr', self.cam_id, datetime.strftime(datetime.utcnow(), "%Y-%m-%d_%H-%M-%S")[:-9], 'add']), json={ 'start': start, 'end': end, 'mp4': url1, 'webm': url2 })
		
		print('CHECK: ', '/'.join([self.api_endpoint, 'dvr', self.cam_id, datetime.strftime(datetime.utcnow(), "%Y-%m-%d_%H-%M-%S")[:-9], 'add']))
		print('\n', { 'start': start, 'end': end, 'mp4': url1, 'webm': url2 })

	# begin upload_record func. uploads video (and screenshots) records to CDN-module from FS-store
	##
	### @return: bool-flag
	def upload_record(self, cdn_file_url, file_path):
		self._log('upload_record func', True)
		self._log('upload_record func->cdn_file_url: %s' % cdn_file_url, True)

		# read file
		upload_file = open(os.path.abspath(file_path), 'rb')
		files = {'file': upload_file}

		# make upload req
		res = requests.post(cdn_file_url, files=files)
		
		# successfully uploaded
		if res.status_code == 201:
			return True
		else:
		# 	# some error
			self._log('upload_record func->upload ERROR: %s' % res.content, True)
			return False
		## func end.

	# begin vw_init func. init cv2.VideoWriter object
	##
	## sets start datetime of record
	## calls init_unreleased_dirs func
	## stores cv2.VideoWriter object in self.out object
	##
	def vw_init(self):
		self._log('vw_init func')

		# creates cv2.VideoWriter object
		self.out[self.get_out_name()] = cv2.VideoWriter(self.get_unreleased_record_path(), VIDEO_FOURCC, self.fps, (self.frame_width,self.frame_height))
		## func end.

	# begin is_end_of_record_segment func. checks is whether it end of video record
	##
	## checks by self.frame_counter value
	## if frames count is equal to self.duration (segment durations in secs) * self.fps, then is end of video record
	##
	### @returns: bool-flag
	def is_end_of_record_segment(self):
		if self.frame_counter >= self.duration*self.fps:
			return True
		else:
			return False
		## func end.

	# begin store_sync_fps_data func. stores count of fps in sections by h-m-s
	##
	def store_sync_fps_data(self):
		now_time = str(datetime.strftime(datetime.now(), "%H-%M-%S"))

		if not now_time in self.sync_sheets:
			self.sync_sheets[now_time] = 0
		else:
			self.sync_sheets[now_time] += 1
		## func end.

	# begin sync_record_fps func. calcs avg fps value by stored data
	##
	def sync_record_fps(self):
		self._log('sync_record_fps func')

		# sums all fps values and divides them by number of elements
		self.fps = sum(self.sync_sheets.values()) / len(self.sync_sheets.values())
		self.fps_synced = True

		# writes fps value to file in unreleased record dir
		self.create_fps_value_file()

		self._log('sync_record_fps func ->fps value was synced with an average value of %s' % self.fps)
		## func end.

	# begin sync_vw_fps func. creates new cv2.VideoWriter object in self.out and writes all last frames to unreleased record
	##
	def sync_vw_fps(self):
		self._log('sync_vw_fps func', True)

		# init cv2.VideoWriter
		self.vw_init()

		

		# writes frames that were used when sync fps value
		for frame_i in range(0, FRAMES_NUMBER_FOR_SYNC_FPS_VALUE-1):
			# gets a jpeg-frame from FS-store
			frame = cv2.imread(self.get_frame_path(frame_i))
			# adds a frame to video of unreleased record
			self.out[self.get_out_name()].write(frame)

		# sets bool-flag that cv2.vw object has been synced
		self.vw_synced = True

		self._log('sync_vw_fps func ->cv2.vw object has been synced', True)
		## func end.

	# begin release func. stops recording this video segment and releases it
	##
	## enables flag of stop recording
	## checks existence of cv2.VideoWriter object and if it doesn't exist, calls release func
	## resets frames counter and disables flag to stop recording
	## calls create_media_record func and gets ID of new Media-record
	## 
	### @return: [bool-flag, ID of video Media-record in Core-module]
	def release(self):
		self._log('release func')
		
		self.is_stop = True

		self._log(str(self.get_out_name()), True)

		if not str(self.get_out_name()) in self.out:
			self._log('release func ->cv2.vw object does not exist', True)
			# resets helper vars
			self.init_helper_variables()
			# breaks
			return [False]
		else:
			# init released dir
			self.init_released_dir()

			# key-name of cv2.vw object in self.out
			vw_name = self.get_out_name()

			# creates a new Media-record in Core-module
			screenshot_media_record = self.create_media_record('screenshot.' + SCREENSHOT_FILEFORMAT, 'photo')
			video_media_record = self.create_media_record(self.get_output_video_filename(), 'video', screenshot_media_record[1][0], screenshot_media_record[1][1]) # {}
			print('URL: ', video_media_record[1][1])
			self.create_in_DB(video_media_record[1][1], 'none')
			# check video Media-record error
			if not video_media_record[0]:
				self._log('release func ->create video_media_record ERROR', True)
				self._log('release func ->record has not be released. create video_media_record returns error')
				# resets helper vars
				self.init_helper_variables()
				# this operation must be interrupted. record will try release by auto_recover_records func after reinit this instance
				return [False]

			# create cdn uploads log
			cdn_uploads_log = { 'screenshot': screenshot_media_record, 'video': video_media_record, 'datetime': self.get_str_current_datetime() }
			self.create_cdn_log_file(json.dumps(cdn_uploads_log))

			unreleased_record_task = { 'screenshot_cdn_url': screenshot_media_record[1][1], 'video_cdn_url': video_media_record[1][1], 'vw_name': self.get_out_name(), 'unreleased_dir': self.unreleased_dvr_dir, 'released_dir': self.released_dvr_dir }

			# puts a new task to unreleased_records_worker queue
			self.unreleased_records_worker_queue.put(unreleased_record_task)
			self._log('release func ->task for process_unreleased_records worker was putted into queue')

		# resets helper vars
		self.init_helper_variables()

		# return success status and Media-record ID
		return [True, video_media_record[1][0]]
		## func end.

	# begin process_unreleased_records_worker func. archives jpeg-frames, move all data of unreleased record from unreleased dir to released dir, create a new Media-record and upload released video record to CDN-module
	##
	## worker will run in unreleased_records_worker thread
	## processing unreleased records
	##
	def process_unreleased_records_worker(self):
		self._log('process_released_records_worker func ->init', True)

		# this is worker:)
		while True:
			# gets unreleased record from unreleased_records_worker_queue
			unreleased_record = self.unreleased_records_worker_queue.get()

			if unreleased_record is None:
				break

			# calls release func of cv2.vw object
			self.out[unreleased_record['vw_name']].release()

			# copies released video to released dir
			self._log('process_released_records_worker func ->copy released video', True)
			self.copy_file(self.get_unreleased_record_path(unreleased_record['unreleased_dir']), self.get_released_record_path(unreleased_record['released_dir']))

			# uploads first screenshot of released video to CDN-module
			self._log('process_released_records_worker func ->upload screenshot of video record', True)
			print()
			self.upload_record(unreleased_record['screenshot_cdn_url'], self.get_frame_path( 0, "/".join([unreleased_record['unreleased_dir'], JPEG_FRAMES_DIR]) ))

			# uploads released video to CDN-module
			self._log('process_released_records_worker func ->upload video record', True)
			self.upload_record(unreleased_record['video_cdn_url'], self.get_released_record_path(unreleased_record['released_dir']))

			# compress jpeg-frames dir and save in released dir
			if STORE_ARCHIVE_JPEG_FRAMES:
				self._log('process_released_records_worker func ->compress jpeg-frames dir', True)
				self.make_tarfile("/".join([unreleased_record['released_dir'], JPEG_FRAMES_DIR + ".tar.bz2"]), self.get_unreleased_frames_dir_path(unreleased_record['unreleased_dir']))
			
			# removes jpeg-frames in unreleased dir
			self._log('process_released_records_worker func ->remove jpeg-frames in unreleased dir', True)
			self.remove_dir(self.get_unreleased_frames_dir_path(unreleased_record['unreleased_dir']))
			
			# stores logs
			if STORE_LOGS:
				# copies fps value file to released dir
				self._log('process_released_records_worker func ->copy fps value file to released dir', True)
				self.copy_file(self.get_unreleased_fps_value_path(unreleased_record['unreleased_dir']), self.get_released_fps_value_path(unreleased_record['released_dir']))
				# copies cdn uploads log to released dir
				self._log('process_released_records_worker func ->copy cdn uploads log to released dir', True)
				self.copy_file(self.get_unreleased_cdn_log_path(unreleased_record['unreleased_dir']), self.get_released_cdn_log_path(unreleased_record['released_dir']))

			# removes unreleased dir
			self._log('process_released_records_worker func ->remove unreleased dir', True)
			self.remove_dir(unreleased_record['unreleased_dir'])

			# removes (!)released video record
			if not STORE_RELEASED_RECORDS:
				self._log('process_released_records_worker func ->remove (!)released video record', True)
				self.remove_file(self.get_released_record_path(unreleased_record['released_dir']))

			# removes (!)released dir
			if not (STORE_ARCHIVE_JPEG_FRAMES or STORE_RELEASED_RECORDS or STORE_LOGS):
				self._log('process_released_records_worker func ->remove (!)released dir', True)
				self.remove_dir(unreleased_record['released_dir'])

			# completes task in unreleased_records_worker queue
			self.unreleased_records_worker_queue.task_done()
		## func end.

	# begin write_frame func. writes frame into video of unreleased record and writes as jpeg file in jpeg-frames subdir
	##
	## calls cv2.VideoWriter.write func to add a frame to unreleased video record
	## uses cv2.imwrite func to save frame as a jpeg file
	##
	def write_frame(self, frame):
		# self._log('write_frame func ->frame_counter: %s' % self.frame_counter)

		# cv2.VideoWriter object will be created after syncs fps value and cv2.vw recorder object (it adds first frames that were received during sync of fps value)
		if self.vw_synced:
			# adds a frame to unreleased record
			self.out[self.get_out_name()].write(frame)

		# writes frame to jpeg file
		cv2.imwrite(self.get_next_frame_path(), frame)
		# if self.frame_counter == 0:
		# 	cv2.imwrite(self.get_next_frame_path(), frame)
		# updates frame counter
		self.frame_counter += 1
		


		## func end.

	# begin process_frames_worker func. get frames and create record by cv2.VideoWriter (cv2.VW)
	##
	## worker will run in frames_worker thread
	## processing frames
	##
	def process_frames_worker(self):
		self._log('process_frames_worker func ->init', True)

		# this is worker:)
		while True:
			# gets frame from frames_worker_queue
			frame = self.frames_worker_queue.get()

			if frame is None:
				break

			# first frame
			if self.frame_counter < 1:
				# init helper variables
				self.init_helper_variables()
				# sets start datetime of video record
				self.dvr_date = self.get_str_current_datetime()
				# sets and creates dirs of unreleased(tmp) record (main unreleased record dir and jpeg-frames subdir)
				self.init_unreleased_dirs()

			if not self.is_stop:
				# stores number of frames in sections by seconds
				if self.frame_counter <= FRAMES_NUMBER_FOR_SYNC_FPS_VALUE:

					self.store_sync_fps_data()

					# calcs avg fps value from stored data
					if self.frame_counter == FRAMES_NUMBER_FOR_SYNC_FPS_VALUE:
						self.sync_record_fps()

					##
				else:

					# if avg fps value was calculated, it's necessary to sync cv2.vw object
					if not self.vw_synced and not self.vw_synced_process:
						self.vw_synced_process = True
						self.sync_vw_fps()

					# if avg fps value and cv2.vw object were synced
					if self.vw_synced_process and self.vw_synced:
						self.vw_synced_process = False

					##
				##

				# if this is end of this segment in video record
				if self.is_end_of_record_segment():
					self._log('frame func ->calls release func', True)
					# release ended segment of video record
					self.release()
				else:
					# writes frame in FS-store
					if not self.vw_synced_process:
						self.write_frame(frame)

				# completes task in frames_worker queue
				if not self.vw_synced_process:
					self.frames_worker_queue.task_done()
			##
		## func end.

	# begin frame func. gets frames and creates video record uses cv2.VideoWriter (cv2.VW)
	##
	## gets raw cap.read frame and puts it to frames_worker_queue
	##
	def frame(self, frame):
		# self._log('frame func ->frame_counter: %s' % self.frame_counter)
		if (self.frame_height is None) or (self.frame_width is None):
			self.frame_height 	= frame.shape[0]
			self.frame_width 	= frame.shape[1]

		if (frame.shape[0] != self.frame_height) or (frame.shape[1] != self.frame_width):
			self.frame_height 	= frame.shape[0]
			self.frame_width 	= frame.shape[1]
			self.release()
			
		if not self.is_stop:
			# puts a new task to process frame to frames_worker queue
			self.frames_worker_queue.put(frame)

		## func end.

##
## DVRClass END.
##
