//
//  RootView.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/07/30.
//

import SwiftUI
import FeatureAuth
import FeatureWorkspace

@MainActor
struct RootView: View {
    @EnvironmentObject private var authenticationSession:
        AuthenticationSession

    @StateObject private var loginViewModel:
        LoginViewModel

    @StateObject private var authenticationViewModel:
        AuthenticationViewModel

    @StateObject private var logoutViewModel:
        LogoutViewModel

    @StateObject private var workspaceListViewModel:
        WorkspaceListViewModel

    @State private var hasFinishedSplash = false

    init(
        authFactory: AuthFeatureFactory,
        workspaceFactory: WorkspaceFeatureFactory
    ) {
        _loginViewModel = StateObject(
            wrappedValue:
                authFactory.makeLoginViewModel()
        )

        _authenticationViewModel = StateObject(
            wrappedValue:
                authFactory.makeAuthenticationViewModel()
        )

        _logoutViewModel = StateObject(
            wrappedValue:
                authFactory.makeLogoutViewModel()
        )

        _workspaceListViewModel = StateObject(
            wrappedValue:
                workspaceFactory.makeWorkspaceListViewModel()
        )
    }

    var body: some View {
        ZStack {
            if shouldShowSplash {
                SplashView {
                    withAnimation(
                        .easeInOut(duration: 0.4)
                    ) {
                        hasFinishedSplash = true
                    }
                }
                .transition(.opacity)
                .zIndex(1)
            } else {
                mainContent
                    .transition(.opacity)
            }
        }
        .animation(
            .easeInOut(duration: 0.4),
            value: hasFinishedSplash
        )
        .task {
            await restoreSession()
        }
    }

    private var shouldShowSplash: Bool {
        guard hasFinishedSplash else {
            return true
        }

        switch authenticationViewModel.state {
        case .idle, .loading:
            return true

        case .authenticated,
             .unauthenticated,
             .failed:
            return false
        }
    }

    @ViewBuilder
    private var mainContent: some View {
        switch authenticationViewModel.state {
        case let .failed(message):
            sessionRestoreErrorView(
                message: message
            )

        default:
            if authenticationSession.isAuthenticated {
                MainTabView(
                    workspaceListViewModel:
                        workspaceListViewModel
                )
            } else {
                LoginView(
                    viewModel: loginViewModel,
                    onLoginSuccess: { user in
                        authenticationSession
                            .markLoggedIn(
                                user: user
                            )
                    }
                )
            }
        }
    }

    private func sessionRestoreErrorView(
        message: String
    ) -> some View {
        VStack(spacing: 16) {
            Image(
                systemName:
                    "exclamationmark.triangle"
            )
            .font(.system(size: 42))

            Text(
                "ログイン状態を確認できませんでした"
            )
            .font(.headline)

            Text(message)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Button("再試行") {
                Task {
                    await restoreSession()
                }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(24)
        .frame(
            maxWidth: .infinity,
            maxHeight: .infinity
        )
    }

    private func restoreSession() async {
        await authenticationViewModel
            .restoreSession()

        if case let .authenticated(user) =
            authenticationViewModel.state {
            authenticationSession
                .markLoggedIn(
                    user: user
                )
        }
    }
}
