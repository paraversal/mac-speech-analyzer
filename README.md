# mac-speech-analyzer

🐍 Python package to run the macOS 26 SpeechAnalyzer API from Python to transcribe audio files.

## Requirements

- at least macOS 26.0
- XCode command-line tools

## Installation

```bash
uv add mac-speech-analyzer
# or
pip install mac-speech-analyzer
```

## Usage

### Basic usage

```py
# for one-time transcription - will unload model after transcription
text = transcribe("/path/to/file", "en_US")

# for multiple subsequent transcriptions - will keep the model in memory for as long as the object is in scope. Either as a context manager...
with SpeechAnalyzer(locale="en_US") as s:
    text = s.transcribe("/path/to/file")

# ... or without one
s = SpeechAnalyzer(locale="en_US")
s.goodmorning()
text = s.transcribe("/path/to/file")
text = s.transcribe("/path/to/another/file")
s.goodnight()
```

### Live transcription

The SpeechAnalyzer API provides progressive transcription, allowing us to access to transcription as its happening.

```py
# default: no live transcription
with SpeechAnalyzer(locale="en_US") as s:
    text = s.transcribe("/path/to/file")

# prints live transcription to stdout
with SpeechAnalyzer(locale="en_US", live=True) as s:
    text = s.transcribe("/path/to/file")

# calls custom callback on every new transcription fragment
def log(text: str) -> None:
    print(f"... {text} ...")

with SpeechAnalyzer(locale="en_US", live=True, custom_live_callback=log) as s:
    text = s.transcribe("/path/to/file")
```

## Development

```zsh
uv pip install -e .
```

to one-time-install the package as editable, from then on:

```zsh
ninja
```

to rebuild the package

# License

mac-speech-analyzer is released under the MIT License. See [LICENSE](./LICENSE) for more details.
