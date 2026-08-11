//
//  AuthenticatedUser.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public struct AuthenticatedUser: Decodable, Equatable, Sendable, Identifiable {
    public let id: String
    public let email: String
    public let displayName: String
    public let firstName: String
    public let lastName: String
    public let avatarUrl: String
    public let timezone: String

    public init(
        id: String,
        email: String,
        displayName: String,
        firstName: String,
        lastName: String,
        avatarUrl: String,
        timezone: String
    ) {
        self.id = id
        self.email = email
        self.displayName = displayName
        self.firstName = firstName
        self.lastName = lastName
        self.avatarUrl = avatarUrl
        self.timezone = timezone
    }
}
