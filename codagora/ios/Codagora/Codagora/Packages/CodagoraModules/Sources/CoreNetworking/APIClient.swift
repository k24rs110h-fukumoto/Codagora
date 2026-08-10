//
//  APIClient.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/06.
//

import Foundation

public protocol APIClientProtocol: Sendable {
    func send<Endpoint: APIEndpoint>(
        _ endpoint: Endpoint
    ) async throws -> Endpoint.Response
}

public struct APIClient: APIClientProtocol, Sendable {
    private let requestBuilder: APIRequestBuilder
    private let transport: any HTTPTransport

    private let decoderFactory:
        @Sendable () -> JSONDecoder

    public init(
        baseURL: URL,
        transport: any HTTPTransport = URLSessionTransport(),
        decoderFactory: @escaping @Sendable () -> JSONDecoder = {
            let decoder = JSONDecoder()

            decoder.keyDecodingStrategy =
                .convertFromSnakeCase

            decoder.dateDecodingStrategy = .custom {
                decoder in

                let container =
                    try decoder.singleValueContainer()

                let value =
                    try container.decode(String.self)

                let fractionalFormatter =
                    ISO8601DateFormatter()

                fractionalFormatter.formatOptions = [
                    .withInternetDateTime,
                    .withFractionalSeconds
                ]

                if let date =
                    fractionalFormatter.date(from: value) {
                    return date
                }

                let standardFormatter =
                    ISO8601DateFormatter()

                standardFormatter.formatOptions = [
                    .withInternetDateTime
                ]

                if let date =
                    standardFormatter.date(from: value) {
                    return date
                }

                throw DecodingError.dataCorruptedError(
                    in: container,
                    debugDescription:
                        "ISO 8601形式の日時を変換できません: \(value)"
                )
            }

            return decoder
        }
    ) {
        self.requestBuilder = APIRequestBuilder(
            baseURL: baseURL
        )

        self.transport = transport
        self.decoderFactory = decoderFactory
    }

    public func send<Endpoint: APIEndpoint>(
        _ endpoint: Endpoint
    ) async throws -> Endpoint.Response {
        let request = try requestBuilder.build(
            from: endpoint
        )

        let data: Data
        let response: URLResponse

        do {
            (data, response) = try await transport.send(
                request
            )
        } catch let error as NetworkError {
            throw error
        } catch let error as URLError {
            throw NetworkError.transport(
                code: error.code
            )
        } catch {
            throw NetworkError.transport(
                code: .unknown
            )
        }

        guard let httpResponse =
                response as? HTTPURLResponse
        else {
            throw NetworkError.invalidResponse
        }

        let apiErrorResponse = decodeAPIError(
            from: data
        )

        try validate(
            statusCode: httpResponse.statusCode,
            response: apiErrorResponse
        )

        do {
            let decoder = decoderFactory()

            return try decoder.decode(
                Endpoint.Response.self,
                from: data
            )
        } catch {
            throw NetworkError.responseDecodingFailed
        }
    }

    private func decodeAPIError(
        from data: Data
    ) -> APIErrorResponse? {
        guard !data.isEmpty else {
            return nil
        }

        let decoder = decoderFactory()

        return try? decoder.decode(
            APIErrorResponse.self,
            from: data
        )
    }

    private func validate(
        statusCode: Int,
        response: APIErrorResponse?
    ) throws {
        switch statusCode {
        case 200...299:
            return

        case 400:
            throw NetworkError.badRequest(response)

        case 401:
            throw NetworkError.unauthorized(response)

        case 403:
            throw NetworkError.forbidden(response)

        case 404:
            throw NetworkError.notFound(response)

        case 409:
            throw NetworkError.conflict(response)

        case 429:
            throw NetworkError.tooManyRequests(response)

        case 500...599:
            throw NetworkError.serverError(
                statusCode: statusCode,
                response: response
            )

        default:
            throw NetworkError.unexpectedStatusCode(
                statusCode: statusCode,
                response: response
            )
        }
    }
}
