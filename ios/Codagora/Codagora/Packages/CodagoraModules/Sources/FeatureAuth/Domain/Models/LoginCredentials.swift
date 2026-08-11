//
//  LoginCredentials.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public struct LoginCredentials: Equatable, Sendable {
    public let email: String
    public let password: String

    public init(
        email: String,
        password: String
    ) {
        self.email = email
        self.password = password
    }
}
