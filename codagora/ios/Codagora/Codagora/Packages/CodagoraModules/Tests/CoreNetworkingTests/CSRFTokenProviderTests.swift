//
//  CSRFTokenProviderTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation
import Testing
@testable import CoreNetworking

@Suite(.serialized)
struct CSRFTokenProviderTests {
    @Test("対象URLのCSRFトークンを取得する")
    func returnsCSRFTokenForURL() async throws {
        let storage = HTTPCookieStorage.shared

        let url = try #require(
            URL(
                string: "https://api.example.com/api/auth/logout/"
            )
        )

        let cookie = try makeCookie(
            name: "csrftoken",
            value: "csrf-token-123",
            domain: "api.example.com"
        )

        storage.setCookie(cookie)

        defer {
            storage.deleteCookie(cookie)
        }

        let provider = HTTPCookieCSRFTokenProvider(
            cookieStorage: storage
        )

        let token = await provider.token(
            for: url
        )

        #expect(token == "csrf-token-123")
    }

    @Test("CSRFトークンが存在しない場合はnilを返す")
    func returnsNilWithoutCSRFCookie() async throws {
        let storage = HTTPCookieStorage.shared

        let url = try #require(
            URL(
                string: "https://no-cookie.example.com/"
            )
        )

        let provider = HTTPCookieCSRFTokenProvider(
            cookieStorage: storage
        )

        let token = await provider.token(
            for: url
        )

        #expect(token == nil)
    }

    @Test("別名のCookieはCSRFトークンとして扱わない")
    func ignoresCookieWithDifferentName() async throws {
        let storage = HTTPCookieStorage.shared

        let url = try #require(
            URL(
                string: "https://different-name.example.com/"
            )
        )

        let cookie = try makeCookie(
            name: "sessionid",
            value: "session-123",
            domain: "different-name.example.com"
        )

        storage.setCookie(cookie)

        defer {
            storage.deleteCookie(cookie)
        }

        let provider = HTTPCookieCSRFTokenProvider(
            cookieStorage: storage
        )

        let token = await provider.token(
            for: url
        )

        #expect(token == nil)
    }

    @Test("別ドメインのCSRFトークンは取得しない")
    func ignoresCSRFCookieFromDifferentDomain() async throws {
        let storage = HTTPCookieStorage.shared

        let requestURL = try #require(
            URL(
                string: "https://api.example.com/"
            )
        )

        let cookie = try makeCookie(
            name: "csrftoken",
            value: "other-domain-token",
            domain: "other.example.com"
        )

        storage.setCookie(cookie)

        defer {
            storage.deleteCookie(cookie)
        }

        let provider = HTTPCookieCSRFTokenProvider(
            cookieStorage: storage
        )

        let token = await provider.token(
            for: requestURL
        )

        #expect(token == nil)
    }

    private func makeCookie(
        name: String,
        value: String,
        domain: String
    ) throws -> HTTPCookie {
        try #require(
            HTTPCookie(
                properties: [
                    .name: name,
                    .value: value,
                    .domain: domain,
                    .path: "/",
                    .secure: "TRUE"
                ]
            )
        )
    }
}
