//
//  APIRequestBuilder.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/02.
//

import Foundation

public struct APIRequestBuilder: Sendable {
    private let baseURL: URL

    public init(baseURL: URL) {
        self.baseURL = baseURL
    }

    public func build<Endpoint: APIEndpoint>(
        from endpoint: Endpoint
    ) throws -> URLRequest {
        guard var components = URLComponents(
            url: baseURL,
            resolvingAgainstBaseURL: false
        ) else {
            throw NetworkError.invalidURL
        }

        let basePath = components.path.trimmingCharacters(
            in: CharacterSet(charactersIn: "/")
        )

        let endpointHasTrailingSlash =
            endpoint.path.hasSuffix("/")

        let endpointPath = endpoint.path.trimmingCharacters(
            in: CharacterSet(charactersIn: "/")
        )

        let combinedPath = [basePath, endpointPath]
            .filter { !$0.isEmpty }
            .joined(separator: "/")

        components.path = "/\(combinedPath)" + (endpointHasTrailingSlash ? "/" : "")
        components.queryItems = endpoint.queryItems.isEmpty
            ? nil
            : endpoint.queryItems

        guard let url = components.url else {
            throw NetworkError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue

        for (field, value) in endpoint.headers {
            request.setValue(
                value,
                forHTTPHeaderField: field
            )
        }

        do {
            request.httpBody = try endpoint.makeBody()
        } catch {
            throw NetworkError.requestEncodingFailed
        }

        return request
    }
}
