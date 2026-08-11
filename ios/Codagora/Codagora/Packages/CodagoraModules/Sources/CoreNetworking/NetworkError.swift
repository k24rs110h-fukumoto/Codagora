//
//  NetworkError.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/02.
//

import Foundation

public enum NetworkError: Error, Equatable, Sendable {
    case invalidURL
    case invalidResponse

    case requestEncodingFailed
    case responseDecodingFailed

    case badRequest(APIErrorResponse?)
    case unauthorized(APIErrorResponse?)
    case forbidden(APIErrorResponse?)
    case notFound(APIErrorResponse?)
    case conflict(APIErrorResponse?)
    case tooManyRequests(APIErrorResponse?)

    case serverError(
        statusCode: Int,
        response: APIErrorResponse?
    )

    case unexpectedStatusCode(
        statusCode: Int,
        response: APIErrorResponse?
    )

    case transport(code: URLError.Code)

    public var statusCode: Int? {
        switch self {
        case .badRequest:
            return 400

        case .unauthorized:
            return 401

        case .forbidden:
            return 403

        case .notFound:
            return 404

        case .conflict:
            return 409

        case .tooManyRequests:
            return 429

        case let .serverError(statusCode, _):
            return statusCode

        case let .unexpectedStatusCode(statusCode, _):
            return statusCode

        default:
            return nil
        }
    }

    public var apiErrorResponse: APIErrorResponse? {
        switch self {
        case let .badRequest(response),
             let .unauthorized(response),
             let .forbidden(response),
             let .notFound(response),
             let .conflict(response),
             let .tooManyRequests(response):
            return response

        case let .serverError(_, response),
             let .unexpectedStatusCode(_, response):
            return response

        default:
            return nil
        }
    }
}
