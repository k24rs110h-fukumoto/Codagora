//
//  Untitled.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/02.
//

import Foundation
import Testing
@testable import CoreNetworking

struct APIRequestBuilderTests {
    @Test("Endpointから正しいURLRequestを生成する")
    func buildsURLRequest() throws {
        let baseURL = try #require(
            URL(string: "https://api.example.com/v1/")
        )

        let builder = APIRequestBuilder(baseURL: baseURL)
        let endpoint = MockEndpoint()

        let request = try builder.build(from: endpoint)

        #expect(
            request.url?.absoluteString ==
            "https://api.example.com/v1/messages/?page=1"
        )

        #expect(request.httpMethod == "POST")

        #expect(
            request.value(
                forHTTPHeaderField: "Content-Type"
            ) == "application/json"
        )

        #expect(
            request.value(
                forHTTPHeaderField: "X-Test-Header"
            ) == "Codagora"
        )

        #expect(
            request.httpBody ==
            Data(#"{"message":"Hello"}"#.utf8)
        )
    }
}

private struct MockResponse: Decodable, Sendable {}

private struct MockEndpoint: APIEndpoint {
    typealias Response = MockResponse

    let path = "/messages/"
    let method = HTTPMethod.post

    var queryItems: [URLQueryItem] {
        [
            URLQueryItem(
                name: "page",
                value: "1"
            )
        ]
    }

    var headers: [String: String] {
        [
            "Content-Type": "application/json",
            "X-Test-Header": "Codagora"
        ]
    }

    func makeBody() throws -> Data? {
        Data(#"{"message":"Hello"}"#.utf8)
    }
}
