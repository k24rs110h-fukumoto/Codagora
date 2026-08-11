//
//  LogoutViewModel.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Combine

@MainActor
public final class LogoutViewModel: ObservableObject {
    @Published public private(set) var isLoading = false
    @Published public private(set) var errorMessage: String?
    
    private let logoutUseCase: any LogoutUseCaseProtocol
    
    public init(logoutUseCase: any LogoutUseCaseProtocol) {
        self.logoutUseCase = logoutUseCase
    }
    
    public func logout() async -> Bool {
        guard !isLoading else {
            return false
        }
        
        isLoading = true
        errorMessage = nil
        
        defer {
            isLoading = false
        }
        
        do {
            try await logoutUseCase.execute()
            return true
        } catch {
            errorMessage = AuthErrorMapper.message(for: error)
            return false
        }
    }
    
    public func clearError() {
        errorMessage = nil
    }
}
