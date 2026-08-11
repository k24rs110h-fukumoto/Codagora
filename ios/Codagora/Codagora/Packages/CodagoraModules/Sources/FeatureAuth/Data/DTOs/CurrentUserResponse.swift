//
//  CurrentUserResponse.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public struct CurrentUserResponse: Decodable, Equatable, Sendable {
    public let user: AuthenticatedUser
    
    public init(user: AuthenticatedUser) {
        self.user = user
    }
}
