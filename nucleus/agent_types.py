import tempfile
import os
import uuid
from PIL import Image

class AgentType:
    """
    # Oh man. It's the base type for agent outputs. Why did I make this abstract? Well, life is pain.
    """
    def __init__(self, value):
        self._value = value

    def __str__(self):
        # This is always returning a string, even when I'm too tired to care.
        return self.to_string()

    def to_raw(self):
        # Give me the raw stuff. Sometimes it's just what you need at 3am.
        return self._value

    def to_string(self):
        # Everything is a string if you try hard enough. Or just use str().
        return str(self._value)

class AgentText(AgentType, str):
    """
    # Text type for agent outputs. Yeah, I know, it's a subclass of str too. Why? Because I can.
    """
    def to_raw(self):
        return self._value

    def to_string(self):
        return str(self._value)

class AgentImage(AgentType):
    """
    # Image output. Handles both PIL.Image and file paths.
    # I wish Pillow just did this for me, but nooo, gotta handle all the edge cases.
    """
    def __init__(self, value):
        AgentType.__init__(self, value)
        self._path = None
        self._raw = None
        if isinstance(value, Image.Image):
            self._raw = value
        elif isinstance(value, str) and os.path.exists(value):
            self._path = value
        else:
            raise TypeError(f"Unsupported type for AgentImage: {type(value)}")

    def to_raw(self):
        # If you already have the raw image, just give it back. Otherwise, open the file.
        if self._raw is not None:
            return self._raw
        if self._path is not None:
            self._raw = Image.open(self._path)
            return self._raw

    def to_string(self):
        # This is where things get sketchy. If you don't have a path, dump the image to a temp file and return that.
        if self._path is not None:
            return self._path
        if self._raw is not None:
            directory = tempfile.mkdtemp()
            self._path = os.path.join(directory, str(uuid.uuid4()) + ".png")
            self._raw.save(self._path, format="png")
            return self._path

class AgentAudio(AgentType, str):
    """
    # Audio? Yeah, we have that. It's just a file path and a samplerate, because what else can I do at this hour.
    """
    def __init__(self, value, samplerate=16000):
        super().__init__(value)
        self._path = value
        self.samplerate = samplerate

    def to_raw(self):
        return self._path

    def to_string(self):
        return self._path

def handle_agent_output_types(output):
    """
    # This function tries to wrap outputs into agent types. It's not fancy but it works (most nights).
    """
    if isinstance(output, str):
        return AgentText(output)
    if isinstance(output, Image.Image):
        return AgentImage(output)
    return output