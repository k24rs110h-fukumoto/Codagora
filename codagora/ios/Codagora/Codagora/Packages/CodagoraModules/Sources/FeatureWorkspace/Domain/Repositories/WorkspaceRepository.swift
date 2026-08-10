//
//  WorkspaceRepository.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public protocol WorkspaceRepository: Sendable {
    func fetchWorkspaces() async throws -> [WorkspaceSummary]
}
