//
//  LoginUseCase.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public protocol LoginUseCaseProtocol: Sendable {
    func execute(credentials: LoginCredentials) async throws -> AuthenticatedUser
}

public struct LoginUseCase: LoginUseCaseProtocol, Sendable {
    private let repository: any AuthRepository
    
    public init(repository: any AuthRepository) {
        self.repository = repository
    }
    
    public func execute(credentials: LoginCredentials) async throws -> AuthenticatedUser {
        try await repository.login(credentials: credentials)
    }
}
