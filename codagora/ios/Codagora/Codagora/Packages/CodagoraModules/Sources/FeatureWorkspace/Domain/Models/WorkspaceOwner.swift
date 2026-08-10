//
//  WorkspaceOwner.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public struct WorkspaceOwner: Decodable, Equatable, Sendable, Identifiable {
    public let id: String
    public let displayName: String
    public let avatarUrl: String
    
    public init(id: String, displayName: String, avatarUrl: String) {
        self.id = id
        self.displayName = displayName
        self.avatarUrl = avatarUrl
    }
}
