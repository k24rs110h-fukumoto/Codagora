//
//  WorkspaceListViewModel.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Combine

@MainActor
public final class WorkspaceListViewModel: ObservableObject {
    @Published public private(set) var workspaces: [WorkspaceSummary] = []
    @Published public private(set) var isLoading = false
    @Published public private(set) var errorMessage: String?
    
    private let fetchWorkspacesUseCase: any FetchWorkspacesUseCaseProtocol
    
    public init(fetchWorkspacesUseCase: any FetchWorkspacesUseCaseProtocol) {
        self.fetchWorkspacesUseCase = fetchWorkspacesUseCase
    }
    
    public var isEmpty: Bool {
        workspaces.isEmpty
    }
    
    public func load() async {
        guard !isLoading else {
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        defer {
            isLoading = false
        }
        
        do {
            workspaces = try await fetchWorkspacesUseCase.execute()
        } catch {
            errorMessage = "ワークスペース一覧の取得に失敗しました"
        }
    }
    
    public func reload() async {
        await load()
    }
    
    public func clearError() {
        errorMessage = nil
    }
}
