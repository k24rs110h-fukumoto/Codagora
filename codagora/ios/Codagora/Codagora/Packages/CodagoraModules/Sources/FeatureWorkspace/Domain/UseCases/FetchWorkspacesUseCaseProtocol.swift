//
//  FetchWorkspacesUseCaseProtocol.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public protocol FetchWorkspacesUseCaseProtocol: Sendable {
    func execute() async throws -> [WorkspaceSummary]
}

public struct FetchWorkspacesUseCase: FetchWorkspacesUseCaseProtocol, Sendable {
    private let repository: any WorkspaceRepository
    
    public init(repository: any WorkspaceRepository) {
        self.repository = repository
    }
    
    public func execute() async throws -> [WorkspaceSummary] {
        try await repository.fetchWorkspaces()
    }
}
