//
//  AuthFeatureFactory.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation
import CoreNetworking
import FeatureAuth

@MainActor
struct AuthFeatureFactory {
    private let baseURL: URL
    private let apiClient: any APIClientProtocol
    private let csrfTokenProvider:
        any CSRFTokenProviding

    init(
        baseURL: URL,
        apiClient: any APIClientProtocol,
        csrfTokenProvider:
            any CSRFTokenProviding =
                HTTPCookieCSRFTokenProvider()
    ) {
        self.baseURL = baseURL
        self.apiClient = apiClient
        self.csrfTokenProvider = csrfTokenProvider
    }

    func makeLoginViewModel()
        -> LoginViewModel {
        let useCase = LoginUseCase(
            repository: makeRepository()
        )

        return LoginViewModel(
            loginUseCase: useCase
        )
    }

    func makeAuthenticationViewModel()
        -> AuthenticationViewModel {
        let useCase = CurrentUserUseCase(
            repository: makeRepository()
        )

        return AuthenticationViewModel(
            currentUserUseCase: useCase
        )
    }

    func makeLogoutViewModel()
        -> LogoutViewModel {
        let useCase = LogoutUseCase(
            repository: makeRepository()
        )

        return LogoutViewModel(
            logoutUseCase: useCase
        )
    }

    private func makeRepository()
        -> AuthRepositoryImpl {
        AuthRepositoryImpl(
            apiClient: apiClient,
            baseURL: baseURL,
            csrfTokenProvider: csrfTokenProvider
        )
    }
}
