//
//  AuthErrorMapperTests.swift
//  CodagoraModules
//
//  Created by Haruto Fukumoto on 2026/08/06.
//

import Foundation
import Testing
import CoreNetworking
@testable import FeatureAuth

struct AuthErrorMapperTests {
    @Test("401をログイン情報のエラーへ変換する")
    func mapsUnauthorizedError() {
        let message = AuthErrorMapper.message(
            for: NetworkError.unauthorized(nil)
        )

        #expect(
            message ==
            "メールアドレスまたはパスワードが正しくありません。"
        )
    }

    @Test("400ではサーバーのメッセージを優先する")
    func usesBadRequestServerMessage() throws {
        let response = try decodeAPIError(
            """
            {
              "detail": "メールアドレスの形式が正しくありません。"
            }
            """
        )

        let message = AuthErrorMapper.message(
            for: NetworkError.badRequest(response)
        )

        #expect(
            message ==
            "メールアドレスの形式が正しくありません。"
        )
    }

    @Test("オフラインを接続確認メッセージへ変換する")
    func mapsOfflineError() {
        let message = AuthErrorMapper.message(
            for: NetworkError.transport(
                code: .notConnectedToInternet
            )
        )

        #expect(
            message ==
            "インターネット接続を確認してください。"
        )
    }

    @Test("タイムアウトを再試行メッセージへ変換する")
    func mapsTimeoutError() {
        let message = AuthErrorMapper.message(
            for: NetworkError.transport(
                code: .timedOut
            )
        )

        #expect(
            message ==
            "通信がタイムアウトしました。再度お試しください。"
        )
    }

    @Test("不明なエラーを共通メッセージへ変換する")
    func mapsUnknownError() {
        let message = AuthErrorMapper.message(
            for: TestError.unknown
        )

        #expect(
            message ==
            "予期しないエラーが発生しました。"
        )
    }

    private func decodeAPIError(
        _ json: String
    ) throws -> APIErrorResponse {
        try JSONDecoder().decode(
            APIErrorResponse.self,
            from: Data(json.utf8)
        )
    }
}

private enum TestError: Error {
    case unknown
}
