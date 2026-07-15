# mac-speech-analyzer

🐍 Python package to run the macOS 26 SpeechAnalyzer API from Python to transcribe audio files.

## Requirements

- at least macOS 26.0
- XCode command-line tools

## Development

```zsh
uv pip install -e .
```

to one-time-install the package as editable, from then on:

```zsh
ninja
```

to rebuild the package

## Usage

mac-speech-analyzer can be used in one of three ways: 

1. One-time transcription

```py
s = transcribe("/path/to/file", "en_US")
```

After the one-time transcription, the model will be unloaded, and subsequent runs will completely restart the process of initialising the SpeechAnalyzer API (takes a couple of seconds). If you need to make multiple transcriptions:

2. Class-based (static)

```py
s = SpeechAnalyzer(locale="en_US")
s.ready()
s.transcribe("/path/to/file")
s.free()
```

3. Context manager

Finally, a context manager can be used as well

```py
with SpeechAnalyzer(locale="en_US") as s:
    s.transcribe("/path/to/file")
```

# License

mac-speech-analyzer is released under the MIT License. See [LICENSE](./LICENSE) for more details.
