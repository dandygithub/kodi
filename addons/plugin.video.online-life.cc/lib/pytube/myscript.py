from api import YouTube

# not necessary, just for demo purposes
from pprint import pprint

yt = YouTube()

# Set the video URL.
yt.url = "http://www.youtube.com/watch?v=yQsCjlFBCmc"

# Once set, you can see all the codec and quality options YouTube has made
# available for the perticular video by printing videos.

pprint(yt.videos)

#[<Video: MPEG-4 Visual (.3gp) - 144p>,
# <Video: MPEG-4 Visual (.3gp) - 240p>,
# <Video: Sorenson H.263 (.flv) - 240p>,
# <Video: H.264 (.flv) - 360p>,
# <Video: H.264 (.flv) - 480p>,
# <Video: H.264 (.mp4) - 360p>,
# <Video: H.264 (.mp4) - 720p>,
# <Video: VP8 (.webm) - 360p>,
# <Video: VP8 (.webm) - 480p>]

# The filename is automatically generated based on the video title.
# You can override this by manually setting the filename.

# view the auto generated filename:
print yt.filename

#Pulp Fiction - Dancing Scene [HD]

# set the filename:
yt.filename = 'Dancing Scene from Pulp Fiction'

# You can also filter the criteria by filetype.

pprint(yt.filter('flv'))

#[<Video: Sorenson H.263 (.flv) - 240p>,
# <Video: H.264 (.flv) - 360p>,
# <Video: H.264 (.flv) - 480p>]

# notice that the list is ordered by lowest resolution to highest. If you
# wanted the highest resolution available for a specific file type, you
# can simply do:
print yt.filter('mp4')[-1]
#<Video: H.264 (.mp4) - 720p>

# you can also get all videos for a given resolution
pprint(yt.filter(res='480p'))

#[<Video: H.264 (.flv) - 480p>,
#<Video: VP8 (.webm) - 480p>]

# to select a video by a specific resolution and filetype you can use the get
# method.

video = yt.get('mp4', '720p')

# NOTE: get() can only be used if and only if one object matches your criteria.
# for example:

pprint(yt.videos)

#[<Video: MPEG-4 Visual (.3gp) - 144p>,
# <Video: MPEG-4 Visual (.3gp) - 240p>,
# <Video: Sorenson H.263 (.flv) - 240p>,
# <Video: H.264 (.flv) - 360p>,
# <Video: H.264 (.flv) - 480p>,
# <Video: H.264 (.mp4) - 360p>,
# <Video: H.264 (.mp4) - 720p>,
# <Video: VP8 (.webm) - 360p>,
# <Video: VP8 (.webm) - 480p>]

# Notice we have two H.264 (.mp4) available to us.. now if we try to call get()
# on mp4..

video = yt.get('mp4')
# MultipleObjectsReturned: get() returned more than one object -- it returned 2!

# In this case, we'll need to specify both the codec (mp4) and resolution
# (either 360p or 720p).

# Okay, let's download it!
video.download()

# Downloading: Pulp Fiction - Dancing Scene.mp4 Bytes: 37561829
# 37561829  [100.00%]

# Note: If you wanted to choose the output directory, simply pass it as an
# argument to the download method.
video.download('/tmp/')
