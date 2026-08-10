//
//  LoginViewModel.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation
import Combine
import CoreUtilities

@MainActor
public final class LoginViewModel: ObservableObject {
    @Published public var email: String = ""
    @Published public var password: String = ""
    
    @Published public private(set) var isLoading: Bool = false
    @Published public private(set) var errorMessage: String?
    
    private let loginUseCase: any LoginUseCaseProtocol
    
    public init(loginUseCase: any LoginUseCaseProtocol) {
        self.loginUseCase = loginUseCase
    }
    
    public var canSubmit: Bool {
        ValidationUtility.isValidEmail(email) &&
        !password.isEmpty &&
        !isLoading
    }
    
    public func login() async -> AuthenticatedUser? {
        guard canSubmit else {
            return nil
        }
        
        isLoading = true
        errorMessage = nil
        
        defer {
            isLoading = false
        }
        
        let credentials = LoginCredentials(email: email.trimmingCharacters(in: .whitespacesAndNewlines), password: password)
        
        do {
            return try await loginUseCase.execute(credentials: credentials)
        } catch {
            errorMessage = AuthErrorMapper.message(for: error)
            return nil
        }
    }
}
