from scipy import io
import tarfile

# Container for a segment of data
class Segment:
	def __init__(self, file):
		matFile = io.loadmat(file)

		# matFile is a dictionary.
		# It contains 4 key-value pairs.
		# The values of '__version__', '__header__', and '__globals__' are unimportant.
		# The other value is the actual data (actually, it's a 1x1 matrix containing the data).
		# However, the key name for the data changes depending on the file.
		# It is of the form '%type_segment_%number' where %type is preictal/interital/test and %number is the segment number
		# I'm simply finding the key that doesn't start with '_'
		for key in matFile.keys():
			if not (key[0] == '_'):
				matData = matFile[key][0][0]
				break;
		
		# matData is a list containing the 5 fields mentioned on the Kaggle data page.
		# the rest of this function is basically unpacking this data and storing it in the appropriate variable.
		
		# data: a matrix of EEG sample values arranged row x column as electrode x time.
		self.data = matData[0]
		
		# data_length_sec: the time duration of each data row.
		self.data_length_sec = matData[1][0][0]
		
		# sampling_frequency: the number of data samples representing 1 second of EEG data.
		self.sampling_frequency = matData[2][0][0]
		
		# channels: a list of electrode names corresponding to the rows in the data field.
		self.channels = []
		for i in range(len(matData[3][0])):
			self.channels.append(matData[3][0][i][0])
		
		# sequence: the index of the data segment within the one hour series of clips. For example, preictal_segment_6.mat has a sequence number of 6, and represents the iEEG data from 50 to 60 minutes into the preictal data.
		if (len(matData) >= 5):
			self.sequence = matData[4][0][0]
		else:
			self.sequence = None



# Use to read from a subset of a .tar archive one file at a time
class SegmentStream:
	def __init__(self, parser, range):
		self._parser = parser
		self._current = range[0]
		self._range = range

	def size(self):
		return self._range[1] - self._range[0]

	def hasNext(self):
		return (self._current < self._range[1])

	def getNext(self):
		if not self.hasNext():
			return None
		file = self._parser.extractfile(self._current)
		self._current += 1
		segment = Segment(file)
		file.close()
		return segment



# Use to read from .tar archive one file at a time.
class TarParser:
	def __init__(self, fileName):
		self._archive = tarfile.open(fileName)
		list = (2,1,3)
		self._fileNames = self._archive.getnames()
		self._fileNames.sort()
		size = len(self._fileNames)
		
		start = 0
		for i in range(start, size):
			if "interictal" in self._fileNames[i]:
				start = i
				break
		
		for i in range(start, size):
			if "preictal" in self._fileNames[i]:
				self._interictalRange = (start, i)
				start = i
				break
		
		self._preictalRange = ()
		for i in range(start, size):
			if "test" in self._fileNames[i]:
				self._preictalRange = (start, i)
				start = i
				break

		self._testRange = (start, size)


	def getInterictalStream(self):
		return SegmentStream(self, self._interictalRange)

	def getPreictalStream(self):
		return SegmentStream(self, self._preictalRange)

	def getTestStream(self):
		return SegmentStream(self, self._testRange)

	def extractfile(self, nameIndex):
		return self._archive.extractfile(self._fileNames[nameIndex])