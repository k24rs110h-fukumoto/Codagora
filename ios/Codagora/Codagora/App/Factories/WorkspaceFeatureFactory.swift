//
//  WorkspaceFeatureFactory.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import CoreNetworking
import FeatureWorkspace

@MainActor
struct WorkspaceFeatureFactory {
    private let apiClient: any APIClientProtocol
    
    init(apiClient: any APIClientProtocol) {
        self.apiClient = apiClient
    }
    
    func makeWorkspaceListViewModel() -> WorkspaceListViewModel {
        let repository = WorkspaceRepositoryImpl(apiClient: apiClient)
        
        let useCase = FetchWorkspacesUseCase(repository: repository)
        
        return WorkspaceListViewModel(fetchWorkspacesUseCase: useCase)
    }
}
