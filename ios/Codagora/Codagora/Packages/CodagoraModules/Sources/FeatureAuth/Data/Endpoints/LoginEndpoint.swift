//
//  LoginEndpoint.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation
import CoreNetworking

struct LoginEndpoint: APIEndpoint {
    typealias Response = LoginResponse
    
    let path = "/api/auth/login/"
    let method = HTTPMethod.post
    
    private let request: LoginRequest
    
    var headers: [String : String] {
        [
            "Content-Type": "application/json",
            "Accept": "application/json"
        ]
    }
    
    init(credentials: LoginCredentials) {
        self.request = LoginRequest(credentials: credentials)
    }
    
    func makeBody() throws -> Data? {
        try JSONEncoder().encode(request)
    }
}
