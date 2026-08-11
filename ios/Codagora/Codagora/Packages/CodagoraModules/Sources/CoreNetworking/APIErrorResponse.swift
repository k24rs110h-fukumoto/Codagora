//
//  APIErrorResponse.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/06.
//

import Foundation

public struct APIErrorResponse:
    Decodable,
    Equatable,
    Sendable
{
    public let detail: String?
    public let message: String?
    public let code: String?
    public let errors: [String: [String]]?

    public var primaryMessage: String? {
        if let detail, !detail.isEmpty {
            return detail
        }

        if let message, !message.isEmpty {
            return message
        }

        guard let errors else {
            return nil
        }

        for key in errors.keys.sorted() {
            if let firstMessage = errors[key]?.first,
               !firstMessage.isEmpty {
                return firstMessage
            }
        }

        return nil
    }
}
