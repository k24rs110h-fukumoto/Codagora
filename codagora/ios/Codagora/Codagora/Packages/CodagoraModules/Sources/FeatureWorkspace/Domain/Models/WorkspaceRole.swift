//
//  WorkspaceRole.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public enum WorkspaceRole: String, Codable, CaseIterable, Equatable, Sendable {
    case owner
    case admin
    case member
    case guest
}
