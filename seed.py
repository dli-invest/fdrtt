# install whispers in a different step to not overwhelm the github action
import whisper
model = whisper.load_model("tiny")