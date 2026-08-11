//
//  CSRFTokenProvider.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation

public protocol CSRFTokenProviding: Sendable {
    func token(for url: URL) async -> String?
}

public actor HTTPCookieCSRFTokenProvider: CSRFTokenProviding {
    private let cookieStorage: HTTPCookieStorage
    private let cookieName: String
    
    public init(
        cookieStorage: HTTPCookieStorage = .shared,
        cookieName: String = "csrftoken"
    ) {
        self.cookieStorage = cookieStorage
        self.cookieName = cookieName
    }
    
    public func token(for url: URL) async -> String? {
        cookieStorage
            .cookies(for: url)?
            .first {$0.name == cookieName}?
            .value
    }
}
