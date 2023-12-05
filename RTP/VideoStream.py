import pickle
class VideoStream:
	def __init__(self, filename, ipAddress):
		self.frameNum = 0
		self.ipAddress = ipAddress
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		
	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5) # Get the framelength from the first 5 bits
		if data: 
			framelength = int(data)
							
			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	def restart(self):
		"""Restart the video."""
		self.file.close()

		try:
			self.file = open(self.filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		
	def serialize(self):
		dict = {'frameNum': self.frameNum, 'filename': self.filename, 'ipAddress': self.ipAddress}
		return pickle.dumps(dict)

	def deserialize(data):
		obj = pickle.loads(data)

		video_stream = VideoStream(obj['filename'],obj['ipAddress'])
		video_stream.frameNum = obj['frameNum']
		return video_stream