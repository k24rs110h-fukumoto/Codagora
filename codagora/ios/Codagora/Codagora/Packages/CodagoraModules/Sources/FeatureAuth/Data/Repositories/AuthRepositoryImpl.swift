//
//  AuthRepositoryImpl.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation
import CoreNetworking

public struct AuthRepositoryImpl: AuthRepository {
    private let apiClient: any APIClientProtocol
    private let baseURL: URL
    private let csrfTokenProvider:
        any CSRFTokenProviding

    public init(
        apiClient: any APIClientProtocol,
        baseURL: URL,
        csrfTokenProvider:
            any CSRFTokenProviding =
                HTTPCookieCSRFTokenProvider()
    ) {
        self.apiClient = apiClient
        self.baseURL = baseURL
        self.csrfTokenProvider = csrfTokenProvider
    }

    public func login(
        credentials: LoginCredentials
    ) async throws -> AuthenticatedUser {
        let endpoint = LoginEndpoint(
            credentials: credentials
        )

        let response = try await apiClient.send(
            endpoint
        )

        return response.user
    }

    public func currentUser() async throws
        -> AuthenticatedUser {
        let endpoint = CurrentUserEndpoint()

        let response = try await apiClient.send(
            endpoint
        )

        return response.user
    }

    public func logout() async throws {
        guard let csrfToken =
                await csrfTokenProvider.token(
                    for: baseURL
                )
        else {
            throw NetworkError.unauthorized(nil)
        }

        let endpoint = LogoutEndpoint(
            csrfToken: csrfToken
        )

        let _: LogoutResponse = try await apiClient.send(
            endpoint
        )
    }
}
