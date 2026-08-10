//
//  Content.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/08.
//

import SwiftUI
import Foundation
import CoreNetworking

@MainActor
struct ContentView: View {
    @StateObject private var authenticationSession:
        AuthenticationSession

    private let authFactory:
        AuthFeatureFactory

    private let workspaceFactory:
        WorkspaceFeatureFactory

    init() {
        guard let baseURL = URL(
            string: "http://127.0.0.1:8000/"
        ) else {
            fatalError("APIのBase URLが不正です")
        }

        let apiClient = APIClient(
            baseURL: baseURL
        )

        self.authFactory = AuthFeatureFactory(
            baseURL: baseURL,
            apiClient: apiClient
        )

        self.workspaceFactory =
            WorkspaceFeatureFactory(
                apiClient: apiClient
            )

        _authenticationSession = StateObject(
            wrappedValue:
                AuthenticationSession()
        )
    }

    var body: some View {
        RootView(
            authFactory: authFactory,
            workspaceFactory: workspaceFactory
        )
        .environmentObject(
            authenticationSession
        )
    }
}
