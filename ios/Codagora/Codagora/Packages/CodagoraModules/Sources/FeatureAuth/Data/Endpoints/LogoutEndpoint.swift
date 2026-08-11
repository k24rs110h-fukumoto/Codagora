//
//  LogoutEndpoint.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import CoreNetworking

struct LogoutEndpoint: APIEndpoint {
    typealias Response = LogoutResponse

    let path = "/api/auth/logout/"
    let method = HTTPMethod.post

    private let csrfToken: String

    init(csrfToken: String) {
        self.csrfToken = csrfToken
    }

    var headers: [String: String] {
        [
            "Accept": "application/json",
            "X-CSRFToken": csrfToken
        ]
    }
}
