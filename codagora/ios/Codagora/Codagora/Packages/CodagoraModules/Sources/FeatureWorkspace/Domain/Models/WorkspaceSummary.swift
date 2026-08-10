//
//  WorkspaceSummary.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation

public struct WorkspaceSummary: Decodable, Equatable, Sendable, Identifiable {
    public let id: String
    public let name: String
    public let slug: String
    public let description: String
    public let owner: WorkspaceOwner
    public let currentUserRole: WorkspaceRole?
    public let activeMemberCount: Int
    public let createdAt: Date
    public let updatedAt: Date

    public init(
        id: String,
        name: String,
        slug: String,
        description: String,
        owner: WorkspaceOwner,
        currentUserRole: WorkspaceRole?,
        activeMemberCount: Int,
        createdAt: Date,
        updatedAt: Date
    ) {
        self.id = id
        self.name = name
        self.slug = slug
        self.description = description
        self.owner = owner
        self.currentUserRole = currentUserRole
        self.activeMemberCount = activeMemberCount
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}
