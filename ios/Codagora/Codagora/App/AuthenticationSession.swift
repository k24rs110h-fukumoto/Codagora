//
//  AuthencationSession.swift
//  Codagora
//
//  Created by Haruto Fukumoto on 2026/08/02.
//

import Combine
import FeatureAuth

@MainActor
final class AuthenticationSession: ObservableObject {
    @Published private(set) var currentUser: AuthenticatedUser?
    
    var isAuthenticated: Bool {
        currentUser != nil
    }
    
    func markLoggedIn(user: AuthenticatedUser) {
        currentUser = user
    }
    
    func markLoggedOut() {
        currentUser = nil
    }
}
