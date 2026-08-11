//
//  LoginResponse.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public struct LoginResponse: Decodable, Equatable, Sendable {
    public let user: AuthenticatedUser
    public let message: String?

    public init(
        user: AuthenticatedUser,
        message: String?
    ) {
        self.user = user
        self.message = message
    }
}
