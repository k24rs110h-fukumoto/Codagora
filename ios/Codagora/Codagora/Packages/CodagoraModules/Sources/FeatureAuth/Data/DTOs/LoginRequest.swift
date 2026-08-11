//
//  LoginRequest.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

struct LoginRequest: Encodable, Equatable, Sendable {
    let email: String
    let password: String
    
    init(credentials: LoginCredentials) {
        self.email = credentials.email
        self.password = credentials.password
    }
}
