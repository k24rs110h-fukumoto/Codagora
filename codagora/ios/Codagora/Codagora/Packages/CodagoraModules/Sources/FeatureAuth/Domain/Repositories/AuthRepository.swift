//
//  AuthRepository.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

public protocol AuthRepository: Sendable {
    func login(credentials: LoginCredentials) async throws -> AuthenticatedUser
    
    func currentUser() async throws -> AuthenticatedUser
    
    func logout() async throws
}
