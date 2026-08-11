//
//  LoginEndpointTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation
import Testing
import CoreNetworking
@testable import FeatureAuth

struct LoginEndpointTests {
    @Test("ログイン用のURLRequestを正しく生成する")
    func buildsLoginRequest() throws {
        let baseURL = try #require(
            URL(string: "https://api.example.com/")
        )

        let credentials = LoginCredentials(
            email: "mail@example.com",
            password: "Password1"
        )

        let endpoint = LoginEndpoint(
            credentials: credentials
        )

        let builder = APIRequestBuilder(
            baseURL: baseURL
        )

        let request = try builder.build(
            from: endpoint
        )

        #expect(
            request.url?.absoluteString ==
            "https://api.example.com/api/auth/login/"
        )

        #expect(request.httpMethod == "POST")

        #expect(
            request.value(
                forHTTPHeaderField: "Content-Type"
            ) == "application/json"
        )

        #expect(
            request.value(
                forHTTPHeaderField: "Accept"
            ) == "application/json"
        )

        let bodyData = try #require(
            request.httpBody
        )

        let body = try JSONDecoder().decode(
            LoginRequestBody.self,
            from: bodyData
        )

        #expect(body.email == "mail@example.com")
        #expect(body.password == "Password1")
    }
}

private struct LoginRequestBody: Decodable {
    let email: String
    let password: String
}
