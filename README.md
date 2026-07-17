# mac-speech-analyzer

🐍 Python package to run the macOS 26 SpeechAnalyzer API from Python to transcribe audio files.

The SpeechAnalyzer API generally provides [faster and better results]((https://get-inscribe.com/blog/apple-speech-api-benchmark.html)) than other locally running transcription engines of comparable size. 

## Features

- **Online** or **Offline** transcription
- Automatic download of new languages

## Requirements

- macOS >= 26.0
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
from macspeechanalyzer import transcribe

text = transcribe("/path/to/file", locale = "en_US")
```

## Technical details

This package is made up of two parts: the Python wrapper provides the API, but the actual functionality is achieved by embedding a Swift project which exposes functions to C. With this kind of three language interplay, a clean separation of concerns is really important. Therefore, the implementation is divided into the following four layers:

- Pure Python
- Python → C compat
- Swift → C compat
- Pure Swift

The pure Swift and pure Python layers only deal with their respective languages & types, while the compat layers do all the ugly work of converting between native and C-compatible types

## Roadmap

- ✅ Basic one-shot transcription
- Class-based interface
    - Context manager implementation
- Transcription of live audio stream (microphone, ...)


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
