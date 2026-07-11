import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// The native counterpart to Web RuntimeBus: one authenticated socket that
/// reconnects with bounded exponential backoff and never puts its bearer in a URL.
public actor DesktopRuntimeBus {
    private let client: HTTPDesktopClient
    private let session: URLSession
    private var task: URLSessionWebSocketTask?
    private var stopped = false

    public init(client: HTTPDesktopClient, session: URLSession = .shared) {
        self.client = client
        self.session = session
    }

    public nonisolated static func reconnectDelay(attempt: Int) -> Duration {
        let bounded = min(max(attempt, 0), 5)
        return .milliseconds(min(12_000, 500 * (1 << bounded)))
    }

    /// Frames arrive as strings. Ending iteration cancels the connection; a
    /// network close reconnects until `stop()` is called.
    public func frames() -> AsyncStream<String> {
        stopped = false
        return AsyncStream { continuation in
            let worker = Task { await self.run(continuation) }
            continuation.onTermination = { _ in
                worker.cancel()
                Task { await self.stop() }
            }
        }
    }

    public func stop() {
        stopped = true
        task?.cancel(with: .goingAway, reason: nil)
        task = nil
    }

    private func run(_ continuation: AsyncStream<String>.Continuation) async {
        var attempt = 0
        while !stopped && !Task.isCancelled {
            let socket = session.webSocketTask(with: client.runtimeWebSocketRequest())
            task = socket
            socket.resume()
            do {
                while !stopped && !Task.isCancelled {
                    switch try await socket.receive() {
                    case .string(let value): continuation.yield(value)
                    case .data(let data):
                        if let value = String(data: data, encoding: .utf8) {
                            continuation.yield(value)
                        }
                    @unknown default: break
                    }
                    attempt = 0
                }
            } catch {
                task = nil
                if stopped || Task.isCancelled { break }
                try? await Task.sleep(for: Self.reconnectDelay(attempt: attempt))
                attempt += 1
            }
        }
        continuation.finish()
    }
}
