//
//  APIClientTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/06.
//

import Foundation
import Testing
@testable import CoreNetworking

struct APIClientTests {
    @Test("200のレスポンスをモデルへ変換する")
    func decodesSuccessfulResponse() async throws {
        let data = Data(
            #"{"message":"Hello"}"#.utf8
        )

        let transport = MockHTTPTransport(
            data: data,
            statusCode: 200
        )

        let client = try makeClient(
            transport: transport
        )

        let response = try await client.send(
            MockEndpoint()
        )

        #expect(
            response == MockResponse(
                message: "Hello"
            )
        )
    }

    @Test("401を認証エラーへ変換する")
    func mapsUnauthorizedResponse() async throws {
        try await assertNetworkError(
            expected: .unauthorized(nil),
            transport: MockHTTPTransport(
                data: Data(),
                statusCode: 401
            )
        )
    }

    @Test("500をサーバーエラーへ変換する")
    func mapsServerErrorResponse() async throws {
        try await assertNetworkError(
            expected: .serverError(
                statusCode: 500,
                response: nil
            ),
            transport: MockHTTPTransport(
                data: Data(),
                statusCode: 500
            )
        )
    }

    @Test("不正なJSONを変換エラーとして扱う")
    func mapsInvalidJSONToDecodingError() async throws {
        let invalidData = Data(
            #"{"message":"#.utf8
        )

        try await assertNetworkError(
            expected: .responseDecodingFailed,
            transport: MockHTTPTransport(
                data: invalidData,
                statusCode: 200
            )
        )
    }

    @Test("タイムアウトを通信エラーへ変換する")
    func mapsTimeoutToTransportError() async throws {
        try await assertNetworkError(
            expected: .transport(
                code: .timedOut
            ),
            transport: TimedOutHTTPTransport()
        )
    }
    
    @Test("snake_caseのキーをキャメルケースへ変換する")
    func convertsSnakeCaseKeys() async throws {
        let data = Data(
            #"{"workspace_id":"workspace-001"}"#.utf8
        )

        let transport = MockHTTPTransport(
            data: data,
            statusCode: 200
        )

        let client = try makeClient(
            transport: transport
        )

        let response = try await client.send(
            SnakeCaseEndpoint()
        )

        #expect(
            response.workspaceId == "workspace-001"
        )
    }
    
    @Test("ISO 8601形式の日時をDateへ変換する")
    func decodesISO8601Date() async throws {
        let timestamp = "2026-08-06T13:40:00Z"

        let data = Data(
            #"{"created_at":"\#(timestamp)"}"#.utf8
        )

        let transport = MockHTTPTransport(
            data: data,
            statusCode: 200
        )

        let client = try makeClient(
            transport: transport
        )

        let response = try await client.send(
            ISO8601DateEndpoint()
        )

        let expectedDate = try #require(
            ISO8601DateFormatter().date(
                from: timestamp
            )
        )

        #expect(response.createdAt == expectedDate)
    }
    
    @Test("400のエラー本文を保持する")
    func keepsBadRequestResponseBody() async throws {
        let data = Data(
            #"{"detail":"入力内容を確認してください。"}"#.utf8
        )

        let transport = MockHTTPTransport(
            data: data,
            statusCode: 400
        )

        let client = try makeClient(
            transport: transport
        )

        do {
            let _: MockResponse = try await client.send(
                MockEndpoint()
            )

            Issue.record(
                "400エラーになるはずの通信が成功しました"
            )
        } catch let error as NetworkError {
            #expect(error.statusCode == 400)

            #expect(
                error.apiErrorResponse?.primaryMessage ==
                "入力内容を確認してください。"
            )
        } catch {
            Issue.record(
                "想定外のエラーが発生しました: \(error)"
            )
        }
    }

    private func makeClient<Transport: HTTPTransport>(
        transport: Transport
    ) throws -> APIClient {
        let baseURL = try #require(
            URL(
                string: "https://api.example.com/"
            )
        )

        return APIClient(
            baseURL: baseURL,
            transport: transport
        )
    }

    private func assertNetworkError<
        Transport: HTTPTransport
    >(
        expected: NetworkError,
        transport: Transport
    ) async throws {
        let client = try makeClient(
            transport: transport
        )

        do {
            let _: MockResponse = try await client.send(
                MockEndpoint()
            )

            Issue.record(
                "エラーになるはずの通信が成功しました"
            )
        } catch let error as NetworkError {
            #expect(error == expected)
        } catch {
            Issue.record(
                "想定外のエラーが発生しました: \(error)"
            )
        }
    }
}

private struct MockResponse:
    Decodable,
    Equatable,
    Sendable
{
    let message: String
}

private struct MockEndpoint: APIEndpoint {
    typealias Response = MockResponse

    let path = "/test/"
    let method = HTTPMethod.get
}

private struct MockHTTPTransport: HTTPTransport {
    let data: Data
    let statusCode: Int

    func send(
        _ request: URLRequest
    ) async throws -> (Data, URLResponse) {
        guard
            let url = request.url,
            let response = HTTPURLResponse(
                url: url,
                statusCode: statusCode,
                httpVersion: nil,
                headerFields: nil
            )
        else {
            throw NetworkError.invalidResponse
        }

        return (data, response)
    }
}

private struct TimedOutHTTPTransport: HTTPTransport {
    func send(
        _ request: URLRequest
    ) async throws -> (Data, URLResponse) {
        throw URLError(.timedOut)
    }
}

private struct SnakeCaseResponse:
    Decodable,
    Sendable
{
    let workspaceId: String
}

private struct SnakeCaseEndpoint: APIEndpoint {
    typealias Response = SnakeCaseResponse

    let path = "/snake-case/"
    let method = HTTPMethod.get
}

private struct ISO8601DateResponse:
    Decodable,
    Sendable
{
    let createdAt: Date
}

private struct ISO8601DateEndpoint: APIEndpoint {
    typealias Response = ISO8601DateResponse

    let path = "/date/"
    let method = HTTPMethod.get
}
