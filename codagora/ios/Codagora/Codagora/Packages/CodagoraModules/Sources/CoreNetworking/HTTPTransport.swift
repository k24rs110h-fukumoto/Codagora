//
//  HTTPTransport.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/02.
//

import Foundation

public protocol HTTPTransport: Sendable {
    func send(
        _ request: URLRequest
    ) async throws -> (Data, URLResponse)
}

public struct URLSessionTransport: HTTPTransport {
    private let session: URLSession

    public init(session: URLSession = .shared) {
        self.session = session
    }

    public func send(
        _ request: URLRequest
    ) async throws -> (Data, URLResponse) {
        try await session.data(for: request)
    }
}
