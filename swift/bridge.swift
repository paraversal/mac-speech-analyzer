import Foundation

// Async compat
final class ResultBox<T>: @unchecked Sendable {
    var value: Result<T, Error>?
}

func runBlocking<T: Sendable>(_ body: @Sendable @escaping () async throws -> T) throws -> T {
    let box = ResultBox<T>()
    let semaphore = DispatchSemaphore(value: 0)
    Task.detached {
        do    { box.value = .success(try await body()) }
        catch { box.value = .failure(error) }
        semaphore.signal()
    }
    semaphore.wait()
    return try box.value!.get()
}

private let errorLock = NSLock()
private var _lastError: String?

func setLastError(_ message: String) {
    errorLock.lock(); defer { errorLock.unlock() }
    _lastError = message
}

@_cdecl("msa_last_error")
public func msaLastError() -> UnsafeMutablePointer<CChar>? {
    errorLock.lock(); defer { errorLock.unlock() }
    guard let err = _lastError else { return nil }
    return strdup(err)   // Python copies + msa_free_string's it
}

@_cdecl("msa_transcribe")
public func msaTranscribe(
                        _ url: UnsafePointer<CChar>?,
                        _ locale: UnsafePointer<CChar>?,
                        _ outText: UnsafeMutablePointer<UnsafeMutablePointer<CChar>?>?,
                        _ emitLiveSegments: CBool) -> Int32 {
    let localeStr = locale.map { String(cString: $0) }   // nil stays nil
    let urlStr = url.map { String(cString: $0) }!
    do {
        let text = try runBlocking { try await transcribe(url: urlStr, locale: localeStr, emitLiveSegments: emitLiveSegments) }
        outText?.pointee = strdup(text)
        return 0
    } catch {
        setLastError("\(error)")
        return 1
    }
}

@_cdecl("msa_free_string")
public func msaFreeString(_ ptr: UnsafeMutablePointer<CChar>?) {
    free(ptr)
}

public typealias MSALogCallback = @convention(c) (Int32, UnsafePointer<CChar>?) -> Void
private var logSink: MSALogCallback?

@_cdecl("msa_set_log_callback")
public func msa_set_log_callback(_ cb: MSALogCallback?) {
    logSink = cb
}

// use this everywhere instead of print()
func msaLog(_ level: Int32, _ message: String) {
    if let sink = logSink {
        message.withCString { sink(level, $0) }
    } else {
        print(message)          // fallback when nobody registered
    }
}

public typealias MSALiveTranscription = @convention(c) (UnsafePointer<CChar>?) -> Void
private var liveTranscriptionSink: MSALiveTranscription?

@_cdecl("msa_set_live_callback")
public func msa_set_live_transcription_callback(_ cb: MSALiveTranscription?) {
    liveTranscriptionSink = cb
}

func msaLiveTranscriptionSendFragment(_ message: String) {
    if let sink = liveTranscriptionSink {
        message.withCString { sink($0) }
    }
}
