#!/usr/bin/python3

import os
import glob
import re
import shutil
import subprocess
import argparse
import sys
import svn_util
import json
import threading
import copy
import time
import ms8250b


if sys.platform.startswith('win32'):
	#FETCHLINE="%s\\vpwfetch-oa245-2_4_0.exe --config %s --if %s"
	FETCHLINE="%s\\vpwfetch-oa231-2_5_0.exe --config %s --if %s"
	SEPAR="\\"
	RAMDRIVE="c:\\video4test"
	PORT1="COM14"
	PORT2="COM15"
else:
	FETCHLINE="%s/vpwfetch-oa2410 --config %s --if %s"
	#FETCHLINE="%s/vpwfetch-oa2410 -h %s %s"
	SEPAR="/"
	RAMDRIVE="/ramdisk"
	PORT1="/dev/ttyUSB0"
	PORT2="/dev/ttyUSB1"

PROCESSES = 4
ITERATIONS = 3
READ_POWER_INTERVAL=1
meter1 = None
meter2 = None

class PowerMeasurer(threading.Thread):
	global READ_POWER_INTERVAL

	def __init__(self, meter1, meter2):
		super(PowerMeasurer, self).__init__()
		self.stoprequest = threading.Event()
		self.power_log = []
		self.starttime = int(time.time())
		self.meter1 = meter1
		self.meter2 = meter2
	def run(self):
		while not self.stoprequest.isSet():
			#READ CURRENT AND VOLTAGE
			v1 = self.meter1.getValue()
			v2 = self.meter2.getValue()
			curtime = int(time.time())
			power = v1["value"] * v2["value"]
			self.power_log.append((curtime - self.starttime, power))
			time.sleep(READ_POWER_INTERVAL)
	
	def join(self, timeout=None):
		self.stoprequest.set()
		super(PowerMeasurer, self).join(timeout)

def getVideoList(video_dir):
	dirs = glob.glob(os.path.abspath(video_dir) + SEPAR + "*")
	video_list = []
	for entry in dirs:
		resolution = entry.split(SEPAR)[-1]
		res = resolution.split("x")
		file_list = glob.glob(entry + SEPAR + "*")
		cnt = 0
		for entry2 in file_list:
			if entry2[-4:] == ".jpg" or entry2[-4:] == ".JPG":
				ext = entry2[-4:]
				entry2 = entry2.split(SEPAR)
				entry2[-1] = "*" + ext
				entry2 = SEPAR.join(entry2)
				video_list.extend([{"id":cnt,"path":entry2, "width":int(res[0]), "height":int(res[1])}])
				break
			if entry2[-4:] == ".bmp" or entry2[-4:] == ".BMP":
				ext = entry2[-4:]
				entry2 = entry2.split(SEPAR)
				entry2[-1] = "*" + ext
				entry2 = SEPAR.join(entry2)
				video_list.extend([{"id":cnt,"path":entry2, "width":int(res[0]), "height":int(res[1])}])
				break
			video_list.extend([{"id":cnt,"path":entry2, "width":int(res[0]), "height":int(res[1])}])
			cnt = cnt + 1
	return video_list

def walkVideolist(video_list, sdk_dir, config, fnresult, iterations, procnt):
	res_objects = []
	if (meter1 == None) or (meter2 == None):
		with_power = False
	else:
		with_power = True

	for entry in video_list:
		#Copy file to ramdisk
		print(entry)
		for entry2 in glob.glob(entry["path"]):
			dst_file = RAMDRIVE + SEPAR + entry2.split(SEPAR)[-1] 
			shutil.copy(entry2, dst_file)
		if entry["path"][-4:].lower() == ".jpg":
			dst_file = RAMDRIVE + SEPAR+"*" + dst_file[-4:]
		elif entry["path"][-4:].lower() == ".bmp":
			dst_file = RAMDRIVE + SEPAR+"*" + dst_file[-4:]
		
		#Run test
		args = (FETCHLINE%(sdk_dir, config, dst_file)).split(' ')
		results = []#entry["path"]
		power_logs = []
		for j in range(0, iterations):
			processes = []
			if with_power:
				measurer = PowerMeasurer(meter1, meter2)
				measurer.start()
			for i in range(0, procnt):
				processes.extend([subprocess.Popen(args, stdout=subprocess.PIPE,  shell=False)])
		
			for i in range(0, procnt):
				comres = processes[i].communicate()
				fpsline = comres[0].decode("UTF-8").split('\n')
				fpsline = fpsline[-1]
				results.append(fpsline)
			if with_power:
				measurer.join()
				power_logs.append(copy.deepcopy(measurer.power_log))
			
		average = count_average_fps(results)
		entry["fps"] = average
		if with_power:
			entry["power"] = copy.deepcopy(power_logs)
		res_objects.extend([entry])

		#Remove files
		for entry2 in glob.glob(dst_file):
			os.unlink(entry2)
	fresult = open(fnresult, "w")
	json.dump(res_objects, fresult)
	fresult.close()

def count_average_fps(fps_list):
	average = 0
	count = 0
	for i in range(0,len(fps_list)):
		try:
			ivalue = float(fps_list[i])
			average = average + ivalue
			count = count + 1
		except:
			pass
	try:
		average = average / count
	except:
		average = 0
	return average
		
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("--sdkdir", type=str, required=False, default="sdkdir", help="directory to export SDK")
	parser.add_argument("--svn_uname", type=str, required=False, default="c3pio", help="SVN username")
	parser.add_argument("--svn_passw", type=str, required=False, default="cNocIsT1xevU", help="SVN password")
	parser.add_argument("--svn_config", type=str, required=False, default="svn_config.conf", help="SVN configuration")
	parser.add_argument("--config", type=str, required=False, default="vpwfetch.conf", help="vpwfetch config file")
	parser.add_argument("--videodir", type=str, required=False, default="C:\\video4test", help="video directory")
	parser.add_argument("--iterations", type=int, required=False, default=3, help="video directory")
	parser.add_argument("--processes", type=int, required=False, default=4, help="video directory")
	parser.add_argument("--with_power", action="store_true", help="Measure consumed power")
	parser.add_argument("--meter1", type=str, required=False, default=PORT1, help="Serial port for meter 1")
	parser.add_argument("--meter2", type=str, required=False, default=PORT2, help="Serial port for meter 2")
	parser.add_argument("-o", type=str, required=False, default="results.txt", help="file with results")
	args = parser.parse_args(sys.argv[1:])
	# svn_util.svn_export_fromfile(args.svn_config, args.sdkdir, args.svn_uname, args.svn_passw)
	config = os.path.abspath(args.config)
	if sys.platform.startswith('win32'):	
		shutil.copyfile("opencv_ffmpeg245.dll", args.sdkdir + "\\opencv_ffmpeg245.dll")

	if args.with_power:
		meter1 = ms8250b.Multimeter(args.meter1)
		meter2 = ms8250b.Multimeter(args.meter2)
		while 1:
			time.sleep(1)
			print("Connecting measurers")
			v1 = meter1.getValue()
			v2 = meter2.getValue()
			if ("value" in v1.keys()) and ("value" in v2.keys()):
				bad = 0
				try:
					float(v1["value"])
					float(v1["value"])
				except:
					bad = 1
					pass
				if bad == 0:
					break

	vlist = getVideoList(args.videodir)
	walkVideolist(vlist, args.sdkdir, config, args.o, args.iterations, args.processes)
	if args.with_power:
		meter1.stop()
		meter2.stop()
