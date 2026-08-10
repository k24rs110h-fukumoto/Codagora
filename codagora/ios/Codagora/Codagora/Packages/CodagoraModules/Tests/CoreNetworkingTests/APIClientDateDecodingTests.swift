//
//  APIClientDateDecodingTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/07.
//

import Foundation
import Testing
@testable import CoreNetworking

struct APIClientDateDecodingTests {
    @Test("Djangoの小数秒付き日時をDateへ変換する")
    func decodesDjangoFractionalDate() async throws {
        let data = Data(
            """
            {
                "created_at": "2026-07-26T03:31:49.930586+09:00"
            }
            """.utf8
        )

        let baseURL = try #require(
            URL(string: "https://api.example.com/")
        )

        let client = APIClient(
            baseURL: baseURL,
            transport: DateResponseTransport(
                data: data
            )
        )

        let response = try await client.send(
            DateEndpoint()
        )

        let expectedDate = try #require(
            makeUTCDate(
                year: 2026,
                month: 7,
                day: 25,
                hour: 18,
                minute: 31,
                second: 49,
                nanosecond: 930_586_000
            )
        )

        #expect(
            abs(
                response.createdAt
                    .timeIntervalSince(expectedDate)
            ) < 0.001
        )
    }

    @Test("小数秒なしのISO 8601日時をDateへ変換する")
    func decodesStandardISO8601Date() async throws {
        let data = Data(
            """
            {
                "created_at": "2026-08-06T13:40:00Z"
            }
            """.utf8
        )

        let baseURL = try #require(
            URL(string: "https://api.example.com/")
        )

        let client = APIClient(
            baseURL: baseURL,
            transport: DateResponseTransport(
                data: data
            )
        )

        let response = try await client.send(
            DateEndpoint()
        )

        let expectedDate = try #require(
            makeUTCDate(
                year: 2026,
                month: 8,
                day: 6,
                hour: 13,
                minute: 40,
                second: 0
            )
        )

        #expect(
            response.createdAt == expectedDate
        )
    }

    private func makeUTCDate(
        year: Int,
        month: Int,
        day: Int,
        hour: Int,
        minute: Int,
        second: Int,
        nanosecond: Int = 0
    ) -> Date? {
        guard let timeZone = TimeZone(
            secondsFromGMT: 0
        ) else {
            return nil
        }

        var calendar = Calendar(
            identifier: .gregorian
        )

        calendar.timeZone = timeZone

        var components = DateComponents()

        components.timeZone = timeZone
        components.year = year
        components.month = month
        components.day = day
        components.hour = hour
        components.minute = minute
        components.second = second
        components.nanosecond = nanosecond

        return calendar.date(
            from: components
        )
    }
}

private struct DateResponse:
    Decodable,
    Sendable
{
    let createdAt: Date
}

private struct DateEndpoint: APIEndpoint {
    typealias Response = DateResponse

    let path = "/dates/"
    let method = HTTPMethod.get
}

private struct DateResponseTransport:
    HTTPTransport
{
    let data: Data

    func send(
        _ request: URLRequest
    ) async throws -> (
        Data,
        URLResponse
    ) {
        guard
            let url = request.url,
            let response = HTTPURLResponse(
                url: url,
                statusCode: 200,
                httpVersion: nil,
                headerFields: [
                    "Content-Type":
                        "application/json"
                ]
            )
        else {
            throw URLError(
                .badServerResponse
            )
        }

        return (
            data,
            response
        )
    }
}
