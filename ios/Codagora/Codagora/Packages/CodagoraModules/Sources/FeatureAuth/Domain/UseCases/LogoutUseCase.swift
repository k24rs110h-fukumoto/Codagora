//
//  LogoutUseCase.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public protocol LogoutUseCaseProtocol: Sendable {
    func execute() async throws
}

public struct LogoutUseCase: LogoutUseCaseProtocol, Sendable {
    private let repository: any AuthRepository
    
    public init(repository: any AuthRepository) {
        self.repository = repository
    }
    
    public func execute() async throws {
        try await repository.logout()
    }
}
