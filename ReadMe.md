# Real time cheap as heck transcription service


## Components

### Github actions

open sourcing this content again for free computing power

### Libraries

* ffmpeg
* wit.ai or speech recognization
* youtube-dl
* asyncio 
* one thread for wit.ai call

Python cmd tool to parse a youtube livestream and save it in 4:50 minute intervals to send to wit.ai for speech recognization (free to use).

Next time powell gives a speech I will be ready.

Use the wit-ai api.

https://medium.com/wit-ai/pure-audio-transcription-7372aa0bda7e

wit.ai blows with wav files, never rely on them.

### pseduoCode

```
initialize youtube dl to get video

grab first element in video, various variables to track performance

video download complete

wit.ai logic in async run with discord posting and outputting txt file

grab next element in video.

should be all todo all this in vscodespaces