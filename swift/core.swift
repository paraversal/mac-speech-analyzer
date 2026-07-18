import Foundation
import AVFAudio
import Speech
import Darwin

let INFO = Int32(20)

enum MSAError: Error {
    case osRequirementError(String)
}

func checkMacosVersion () throws {
    guard #available(macOS 26.0, *) else {
        throw MSAError.osRequirementError("SpeechAnalyzer is only available on macos >= 26.0.")
    }
}

func transcribe(url: String, locale: String?, emitLiveSegments: Bool) async throws -> String {
    try checkMacosVersion()
    let locale = await getLocale(customLocale: locale)

    let transcriber = SpeechTranscriber(
        locale: locale,
        preset: .transcription
    )
    do {
        try await downloadLocale(locale, transcriber)
    } catch {
        msaLog(INFO, "so this failed...")
    }

    let analyzer = SpeechAnalyzer(modules: [transcriber])
    let inputURL = URL(fileURLWithPath: url)
    let audioFile = try AVAudioFile(forReading: inputURL)

    var transcript = ""
    let consumer = Task {
    for try await result in transcriber.results where result.isFinal {
            let piece = String(result.text.characters)
            if emitLiveSegments {
                msaLiveTranscriptionSendFragment(piece)
            }
            transcript += piece
        }
        return transcript
    }

    if let last = try await analyzer.analyzeSequence(from: audioFile) {
        try await analyzer.finalizeAndFinish(through: last)
    } else {
        await analyzer.cancelAndFinishNow()
    }
    try await consumer.value

    msaLog(INFO, "Successfully transcribed text.")
    return transcript
}

/// Obtains a valid locale (e.g., en_US).
/// Only a subset of all available locales are supported by the SpeechAnalyzer API.
/// 1. If a custom locale was passed, there is an attempt to parse it.
/// 2. If there was no custom locale passed or the parsing failed, we try to use the system locale.
/// 3. If this also fails, we use the `en` locale
func getLocale(customLocale: String?) async -> Locale {
    var locale: Locale
    // if a custom locale was passed; try to parse it
    if let setCustomLocaleString = customLocale {
        let setCustomLocale = Locale.init(identifier: setCustomLocaleString)
        if let supportedCustomLocale = await SpeechTranscriber.supportedLocale(equivalentTo: setCustomLocale) {
            return supportedCustomLocale
        } else {
            // we should probably throw an exception here
        }
    }

    // if not, try to use current system locale
    if let currentLocale = await SpeechTranscriber.supportedLocale(equivalentTo: Locale.current) {
        locale = currentLocale
    } else {
        // if even this doesn't work, we simply use English
        locale = Locale.init(languageCode: .english, script: .latin, languageRegion: .unknown)
    }

    return locale
}

/// Checks the availability of the selected locale, and downloads it if necessary.
func downloadLocale(_ locale: Locale, _ transcriber: SpeechTranscriber) async throws {
    if !(await SpeechTranscriber.installedLocales).contains(locale) {
        msaLog(INFO, "Downloading locale \(locale)")
        if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
            try await request.downloadAndInstall()
        }
    }
}
