//
//  WorkspaceRepositoryImpl.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import CoreNetworking

public struct WorkspaceRepositoryImpl: WorkspaceRepository, Sendable {
    private let apiClient: any APIClientProtocol
    
    public init(apiClient: any APIClientProtocol) {
        self.apiClient = apiClient
    }
    
    public func fetchWorkspaces() async throws -> [WorkspaceSummary] {
        let endpoint = WorkspaceListEndpoint()
        
        return try await apiClient.send(endpoint)
    }
}
