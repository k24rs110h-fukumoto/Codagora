//
//  CurrentUserUseCase.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public protocol CurrentUserUseCaseProtocol: Sendable {
    func execute() async throws -> AuthenticatedUser
}

public struct CurrentUserUseCase: CurrentUserUseCaseProtocol, Sendable {
    private let repository: any AuthRepository
    
    public init(repository: any AuthRepository) {
        self.repository = repository
    }
    
    public func execute() async throws -> AuthenticatedUser {
        try await repository.currentUser()
    }
}
